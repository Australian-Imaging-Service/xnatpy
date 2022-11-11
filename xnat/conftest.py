import logging
from typing import Any, Pattern, Union

import requests

from pytest import fixture
from pytest_mock import MockerFixture
from requests_mock import Mocker

from xnat.session import XNATSession


class XnatpyRequestsMocker(Mocker):
    def request(
      self,
      method: str,
      url: Union[str, Pattern[str]],
      **kwargs: Any,
    ):
        url = f"https://xnat.example.com/{url.lstrip('/')}"
        return super().request(method, url, **kwargs)


@fixture(scope='function')
def xnatpy_mock():
    with XnatpyRequestsMocker() as mocker:
        yield mocker


@fixture(scope='function')
def xnatpy_connection(mocker: MockerFixture,
                      xnatpy_mock: XnatpyRequestsMocker):
    # Create a working mocked XNATpy connection object
    threading_patch = mocker.patch('xnat.session.threading')  # Avoid background threads getting started
    logger = logging.getLogger('xnatpy_test')

    xnatpy_mock.get('/data/JSESSION')
    xnatpy_mock.delete('/data/JSESSION')
    xnatpy_mock.get('/data/version', status_code=404)
    xnatpy_mock.get('/xapi/siteConfig/buildInfo', json={
        "version": "1.7.5.6",
        "buildNumber": "1651",
        "buildDate": "Tue Aug 20 18:10:41 CDT 2019",
        "sha": "5696414138",
        "isDirty": "false",
        "commit": "2",
        "tag": "1.7.5.4",
        "shaFull": "5696414138d8c95288bf45c8eac2150ba041e867",
        "branch": "master",
        "timestamp": "1566342641000"})
    requests_session = requests.Session()

    # Set cookie for JSESSION/timeout
    cookie = requests.cookies.create_cookie(
        domain='xnat.example.com',
        name='JSESSIONID',
        value='3EFD012EF2FA60EF44BA72ED5925F074',
    )
    requests_session.cookies.set_cookie(cookie)

    cookie = requests.cookies.create_cookie(
        domain='xnat.example.com',
        name='SESSION_EXPIRATION_TIME',
        value='"1668081619871,900000"',
    )
    requests_session.cookies.set_cookie(cookie)

    xnat_session = XNATSession(
        server="https://xnat.example.com",
        logger=logger,
        interface=requests_session,
    )
    yield xnat_session

    # Close connection before the mocker gets cleaned
    xnat_session.disconnect()

    # Clean mocker
    xnatpy_mock.reset()

    # Stop patch of threading
    mocker.stop(threading_patch)
