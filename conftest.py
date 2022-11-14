# Copyright 2011-2015 Biomedical Imaging Group Rotterdam, Departments of
# Medical Informatics and Radiology, Erasmus MC, Rotterdam, The Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import logging

import requests
import requests.cookies

import pytest
from pytest_mock import MockerFixture

from xnat4tests import start_xnat, stop_xnat, add_data, Config
from xnat4tests.utils import set_loggers

import xnat
from xnat.session import XNATSession
from xnat.tests.mock import XnatpyRequestsMocker, CreatedObject

try:
    import docker
    DOCKER_IMPORTED = True
except ImportError:
    docker = None
    DOCKER_IMPORTED = False


# Check if docker is available for xnat4tests
def docker_available() -> bool:
    if not DOCKER_IMPORTED:
        return False

    try:
        docker.from_env()
    except Exception:
        return False

    return True


# Add flag for functional tests
def pytest_addoption(parser):
    parser.addoption(
        "--run-functional", action="store_true", default=False, help="Run functional tests (default=False)"
    )


# Make sure docker tests are only run if docker is available and functional tests only if flag is given
def pytest_collection_modifyitems(config, items):
    run_functional = config.getoption('--run-functional')
    docker_found = docker_available()  # Check if docker is available
    skip_docker = pytest.mark.skip(reason='Need docker for this test, but docker not found on system')
    skip_functional = pytest.mark.skip(reason='Need --run-functional to run functional tests')

    for item in items:
        if not docker_found and 'docker_test' in item.keywords:
            item.add_marker(skip_docker)
        if not run_functional and 'functional_test' in item.keywords:
            item.add_marker(skip_functional)


@pytest.fixture(scope='function')
def xnatpy_mock() -> XnatpyRequestsMocker:
    with XnatpyRequestsMocker() as mocker:
        yield mocker


@pytest.fixture(scope='function')
def xnatpy_connection(mocker: MockerFixture,
                      xnatpy_mock: XnatpyRequestsMocker) -> XNATSession:
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

    # Patch create object to avoid a lot of hassle
    def create_object(uri, type_=None, fieldname=None, **kwargs):
        return CreatedObject(uri, type_, fieldname, **kwargs)

    xnat_session.create_object = create_object

    yield xnat_session

    # Close connection before the mocker gets cleaned
    xnat_session.disconnect()

    # Clean mocker
    xnatpy_mock.reset()

    # Stop patch of threading
    mocker.stop(threading_patch)


# Fixtures for xnat4tests, setup a config, use the pytest tmp_path_factory fixture for the tmpdir
@pytest.fixture(scope="session")
def xnat4tests_config(tmp_path_factory) -> Config:
    tmp_path = tmp_path_factory.mktemp('config')
    set_loggers(loglevel='INFO')
    yield Config(
        xnat_root_dir=tmp_path,
        xnat_port=9999,
        docker_image="xnatpy_xnat4tests",
        docker_container="xnatpy_xnat4tests",
        build_args={
            "xnat_version": "1.8.5",
            "xnat_cs_plugin_version": "3.2.0",
        },
        connection_attempts=30,
        connection_attempt_sleep=10,
    )


# Create a context to ensure closure
@contextlib.contextmanager
def xnat4tests(config) -> str:
    start_xnat(config_name=config)
    try:
        add_data("dummydicom", config_name=config)
        yield config.xnat_uri
    finally:
        stop_xnat(config_name=config)


# Fixtures for xnat4tests, start up a container and get the URI
@pytest.fixture(scope="session")
def xnat4tests_uri(xnat4tests_config) -> str:
    with xnat4tests(xnat4tests_config):
        yield xnat4tests_config.xnat_uri


# Fixtures for xnat4tests, create an xnatpy connection
@pytest.fixture(scope="session")
def xnat4tests_connection(xnat4tests_uri) -> XNATSession:
    with xnat.connect(xnat4tests_uri, user='admin', password='admin') as connection:
        yield connection
