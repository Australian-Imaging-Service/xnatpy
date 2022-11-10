import logging

import pytest
import requests
from requests_mock import Mocker

from xnat import check_auth_guest, check_auth
from xnat.exceptions import XNATAuthError, XNATLoginFailedError, XNATExpiredCredentialsError


def test_check_auth_guest(requests_mock: Mocker):
    server = 'https://xnat.example.com'
    logger = logging.getLogger()
    session = requests.Session()

    # Check if auth as guests is detected correctly
    requests_mock.get(server, text='<html><body><div><span id="user_info">Logged in as: <span style="color:red;">Guest</span></div></body></hmtl>')
    result = check_auth_guest(requests_session=session, server=server, logger=logger)
    assert result == 'guest'

    # Check if auth as user is picked up correctly
    requests_mock.get(server, text='<html><body><div><span id="user_info">Logged in as: &nbsp;<a id="username-link" href="/app/template/XDATScreen_UpdateUser.vm">hachterberg</a></div></body></hmtl>')
    result = check_auth_guest(requests_session=session, server=server, logger=logger)
    assert result == 'hachterberg'

    # Check if wrong response raises correct error
    with pytest.raises(XNATAuthError):
        requests_mock.get(server, text='<html><body><div>Some random html page</div></body></hmtl>')
        check_auth_guest(requests_session=session, server=server, logger=logger)


def test_check_auth(requests_mock: Mocker, caplog: pytest.LogCaptureFixture):
    server = 'https://xnat.example.com'
    test_uri = server.rstrip('/') + '/data/auth'
    logger = logging.getLogger()
    caplog.set_level(logging.INFO)
    session = requests.Session()

    # Check if a 401 login failed is raised correctly
    requests_mock.get(test_uri, status_code=401)
    caplog.clear()
    with pytest.raises(XNATLoginFailedError):
        check_auth(requests_session=session, server=server, user='testuser', logger=logger)
    assert caplog.record_tuples == [('root', logging.CRITICAL, "Login attempt failed for https://xnat.example.com, please make sure your credentials for user testuser are correct!")]

    # Check if a completely wrong server response leads to correct error
    requests_mock.get(test_uri, status_code=500, text='Random response')
    caplog.clear()
    with pytest.raises(XNATAuthError):
        check_auth(requests_session=session, server=server, user='testuser', logger=logger)
    assert caplog.record_tuples == [
        ('root', logging.WARNING, "Simple test requests did not return a 200 or 401 code! Server might not be functional!"),
        ('root', logging.CRITICAL, "Could not determine if login was successful!")
    ]

    # Check if username login is found in correct response
    requests_mock.get(test_uri, status_code=200, text='<html><body><div><span id="user_info">Logged in as: &nbsp;<a id="username-link" href="/app/template/XDATScreen_UpdateUser.vm">testuser</a></div></body></hmtl>')
    caplog.clear()
    result = check_auth(requests_session=session, server=server, user='testuser', logger=logger)
    assert result == 'testuser'
    assert caplog.record_tuples == [('root', logging.INFO, "Logged in successfully as testuser")]

    # Check if token login if found in correct response
    requests_mock.get(test_uri, status_code=200, text='<html><body><div><span id="user_info">Logged in as: &nbsp;<a id="username-link" href="/app/template/XDATScreen_UpdateUser.vm">tokenuser</a></div></body></hmtl>')
    caplog.clear()
    result = check_auth(requests_session=session, server=server, user='c0195ced-6015-4d7a-a83b-67785b6e828d', logger=logger)
    assert result == 'tokenuser'
    assert caplog.record_tuples == [('root', logging.INFO, "Token login successfully as tokenuser")]

    # Check if username login is found in correct response
    requests_mock.get(test_uri, status_code=200, text='<html><body><div><span id="user_info">Logged in as: &nbsp;<a id="username-link" href="/app/template/XDATScreen_UpdateUser.vm">otheruser</a></div></body></hmtl>')
    caplog.clear()
    result = check_auth(requests_session=session, server=server, user='testuser', logger=logger)
    assert result == 'otheruser'
    assert caplog.record_tuples == [('root', logging.WARNING, 'Logged in as otheruser but expected to be logged in as testuser')]

    # Check failure if password is expired
    requests_mock.get(test_uri, text='<html><body><div>Your password has expired.</div></body></hmtl>')
    caplog.clear()
    with pytest.raises(XNATExpiredCredentialsError):
        check_auth(requests_session=session, server=server, user='testuser', logger=logger)
    assert caplog.record_tuples == [('root', logging.ERROR, 'Your password has expired. Please try again after updating your password on XNAT.')]

    # Check failure if password is re-prompted
    requests_mock.get(test_uri, text='<html><body><div><form name="form1" method="post" action="/xnat/login">test</form></div></body></hmtl>')
    caplog.clear()
    with pytest.raises(XNATLoginFailedError):
        check_auth(requests_session=session, server=server, user='testuser', logger=logger)
    message = 'Login attempt failed for {}, please make sure your credentials for user testuser are correct!'.format(server)
    assert caplog.record_tuples == [('root', logging.ERROR, message)]

    # Check if auth as guests is detected correctly
    requests_mock.get(test_uri, text='<html><body><div><span id="user_info">Logged in as: <span style="color:red;">Guest</span></div></body></hmtl>')
    caplog.clear()
    with pytest.raises(XNATLoginFailedError):
        check_auth(requests_session=session, server=server, user='test', logger=logger)
    assert caplog.record_tuples == [('root', logging.ERROR, 'Login failed (in guest mode)!')]

