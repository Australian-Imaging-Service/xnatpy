import datetime
from pathlib import Path

import pytest
from pytest import fixture
from xnat import XNATSession
from conftest import XnatpyRequestsMocker
from xnat.prearchive import Prearchive, PrearchiveSession, PrearchiveScan


@fixture()
def prearchive_data(xnatpy_mock: XnatpyRequestsMocker):
    data = [
        {
            'scan_time': '08:52:11.146',
            'status': 'READY',
            'subject': 'SUB1',
            'tag': '',
            'TIMEZONE': '',
            'uploaded': '2021-12-29 10:11:28.996',
            'lastmod': '2022-01-18 16:41:25.0',
            'scan_date': '2001-09-24',
            'url': '/prearchive/projects/project1/20220122_105154616/NAME001',
            'timestamp': '20211229_101128996',
            'prevent_auto_commit': 'false',
            'project': 'project1',
            'SOURCE': '',
            'prevent_anon': 'false',
            'autoarchive': 'Manual',
            'name': 'NAME001',
            'folderName': 'FNAME001',
            'VISIT': '',
            'PROTOCOL': ''
        },
        {
            'scan_time': '',
            'status': 'ERROR',
            'subject': 'SUB2',
            'tag': '',
            'TIMEZONE': '',
            'uploaded': '',
            'lastmod': '2022-01-18 16:41:25.0',
            'scan_date': '',
            'url': '/prearchive/projects/project1/20220122_105234872/NAME002',
            'timestamp': '20211229_101128996',
            'prevent_auto_commit': 'false',
            'project': 'project1',
            'SOURCE': '',
            'prevent_anon': 'false',
            'autoarchive': 'Manual',
            'name': 'NAME002',
            'folderName': 'NAME002',
            'VISIT': '',
            'PROTOCOL': ''
        },
        {
            'scan_time': '',
            'status': 'READY',
            'subject': 'SUB001',
            'tag': '',
            'TIMEZONE': '',
            'uploaded': '2021-12-29 10:11:28.996',
            'lastmod': '2022-01-18 16:41:25.0',
            'scan_date': '',
            'url': '/prearchive/projects/project2/20220122_105312641/EXP003',
            'timestamp': '20211229_101128996',
            'prevent_auto_commit': 'false',
            'project': 'project2',
            'SOURCE': '',
            'prevent_anon': 'false',
            'autoarchive': 'Manual',
            'name': 'EXP003',
            'folderName': 'EXP003',
            'VISIT': '',
            'PROTOCOL': ''
        },
        {
            'scan_time': '',
            'status': 'RECEIVING',
            'subject': 'SUB002',
            'tag': '',
            'TIMEZONE': '',
            'uploaded': '2021-12-29 10:11:28.996',
            'lastmod': '2022-01-18 16:41:25.0',
            'scan_date': '',
            'url': '/prearchive/projects/project2/20220122_105424116/EXP004',
            'timestamp': '20211229_101128996',
            'prevent_auto_commit': 'false',
            'project': 'project2',
            'SOURCE': '',
            'prevent_anon': 'false',
            'autoarchive': 'Manual',
            'name': 'EXP004',
            'folderName': 'EXP004',
            'VISIT': '',
            'PROTOCOL': ''
        },
    ]
    xnatpy_mock.get('/data/prearchive/projects', json={'ResultSet': {'Result': data}})

    # Get data for 1 project only
    for project in ['project1', 'project2']:
        project_data = [x for x in data if x['project'] == project]
        xnatpy_mock.get(f'/data/prearchive/projects/{project}', json={'ResultSet': {'Result': project_data}})

    # For individual items
    for item in data:
        xnatpy_mock.get(f"/data{item['url']}?format=json", json={'ResultSet': {'Result': [item]}})
        xnatpy_mock.get(f"/data{item['url']}?format=zip", text=f'FILE_CONTENT_{item["name"]}')

    return data


def test_prearchive_sessions(xnatpy_connection: XNATSession,
                             prearchive_data):
    # Test data for multiple projects
    prearchive = Prearchive(xnatpy_connection)
    result = prearchive.sessions()

    assert len(result) == 3
    assert all(isinstance(x, PrearchiveSession) for x in result)
    assert result[0].name == 'NAME001'
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105154616/NAME001'
    assert result[1].name == 'NAME002'
    assert result[1].uri == '/data/prearchive/projects/project1/20220122_105234872/NAME002'
    assert result[2].name == 'EXP003'
    assert result[2].uri == '/data/prearchive/projects/project2/20220122_105312641/EXP003'

    result_project = prearchive.sessions(project='project2')
    assert all(isinstance(x, PrearchiveSession) for x in result_project)
    assert len(result_project) == 1
    assert result_project[0].name == 'EXP003'
    assert result_project[0].uri == '/data/prearchive/projects/project2/20220122_105312641/EXP003'


def test_prearchive_find(xnatpy_connection: XNATSession,
                         prearchive_data):
    prearchive = Prearchive(xnatpy_connection)

    # Search by project/status
    result = prearchive.find(project='project1', status='READY')
    assert all(isinstance(x, PrearchiveSession) for x in result)
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105154616/NAME001'

    # Search by project/status
    result = prearchive.find(project='project1', status='ERROR')
    assert all(isinstance(x, PrearchiveSession) for x in result)
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105234872/NAME002'

    # Search by session
    result = prearchive.find(session='NAME002')
    assert all(isinstance(x, PrearchiveSession) for x in result)
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105234872/NAME002'

    # Search by subject
    result = prearchive.find(subject='SUB001')
    assert all(isinstance(x, PrearchiveSession) for x in result)
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project2/20220122_105312641/EXP003'


def test_prearchive_cache(xnatpy_connection: XNATSession,
                          xnatpy_mock: XnatpyRequestsMocker,
                          prearchive_data):
    prearchive = Prearchive(xnatpy_connection)
    result1 = prearchive.sessions()
    result2 = prearchive.sessions()
    assert all(x[0] is x[1] for x in zip(result1, result2))

    prearchive.caching = False
    result1 = prearchive.sessions()
    result2 = prearchive.sessions()
    assert all(x[0] is not x[1] for x in zip(result1, result2))

    # Default to connection caching (which is on)
    del prearchive.caching
    result1 = prearchive.sessions()
    result2 = prearchive.sessions()
    assert all(x[0] is x[1] for x in zip(result1, result2))


def test_prearchive_session(xnatpy_connection: XNATSession,
                            xnatpy_mock: XnatpyRequestsMocker,
                            prearchive_data,
                            tmp_path: Path):
    session = PrearchiveSession(uri='/data/prearchive/projects/project1/20220122_105154616/NAME001',
                                xnat_session=xnatpy_connection)

    # Check all properties
    assert session.id == 'project1/20211229_101128996/NAME001'
    assert session.xpath == 'xnatpy:prearchiveSession'
    assert session.fulldata == prearchive_data[0]
    assert session.data == prearchive_data[0]
    assert session.autoarchive == 'Manual'
    assert session.folder_name == 'FNAME001'
    assert session.lastmod == datetime.datetime(2022, 1, 18, 16, 41, 25)
    assert session.name == 'NAME001'
    assert session.label == 'NAME001'
    assert session.prevent_anon == 'false'
    assert session.prevent_auto_commit == 'false'
    assert session.project == 'project1'
    assert session.scan_date == datetime.date(2001, 9, 24)
    assert session.scan_time == datetime.time(8, 52, 11, 146000)
    assert session.status == 'READY'
    assert session.subject == 'SUB1'
    assert session.tag == ''
    assert session.timestamp == '20211229_101128996'
    assert session.uploaded == datetime.datetime(2021, 12, 29, 10, 11, 28, 996000)

    # Check empty scan date and scan time
    session = PrearchiveSession(uri='/data/prearchive/projects/project1/20220122_105234872/NAME002',
                                xnat_session=xnatpy_connection)
    assert session.scan_date is None
    assert session.scan_time is None
    assert session.uploaded is None

    # Test XNAT 1.7.0 - 1.7.2 workaround
    xnatpy_mock.get('/data/version', text='1.7.2')
    xnatpy_connection.clearcache()
    print(xnatpy_connection.xnat_version)
    session = PrearchiveSession(uri='/data/prearchive/projects/project2/20220122_105312641/EXP003',
                                xnat_session=xnatpy_connection)
    assert session.name == 'EXP003'
    xnatpy_connection.clearcache()

    # Check the scans listing
    xnatpy_mock.get(f"{session.uri}/scans", json={'ResultSet': {'Result': [
        {
            "series_description": "T1",
            "ID": "1",
        },
        {
            "series_description": "PD",
            "ID": "2",
        }
    ]}})

    scans = session.scans
    assert len(scans) == 2
    assert all(isinstance(x, PrearchiveScan) for x in scans)
    assert scans[0].series_description == 'T1'
    assert scans[0].id == '1'
    assert scans[1].series_description == 'PD'
    assert scans[1].id == '2'

    assert session.cli_str() == 'Prearchive session EXP003'


def test_prearchive_session_download(xnatpy_connection: XNATSession,
                                     xnatpy_mock: XnatpyRequestsMocker,
                                     prearchive_data,
                                     tmp_path: Path):
    session = PrearchiveSession(uri='/data/prearchive/projects/project2/20220122_105312641/EXP003',
                                xnat_session=xnatpy_connection)

    target = tmp_path / 'file.ext'
    result = session.download(target)
    assert result == target

    call = xnatpy_mock.request_history[-1]
    assert call.url == 'https://xnat.example.com/data/prearchive/projects/project2/20220122_105312641/EXP003?format=zip'
    assert call.method == 'GET'

    content = target.read_text()
    assert content == 'FILE_CONTENT_EXP003'


def test_prearchive_session_archive(xnatpy_connection: XNATSession,
                                    xnatpy_mock: XnatpyRequestsMocker,
                                    prearchive_data):
    session = PrearchiveSession(uri='/data/prearchive/projects/project2/20220122_105312641/EXP003',
                                xnat_session=xnatpy_connection)

    # Test archiving of a session
    xnatpy_mock.post('/data/services/archive', text='/data/object_uri')

    result = session.archive()

    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/archive'
    assert request.qs == {
        'auto-archive': ['false'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    assert result.uri == '/data/object_uri'
    assert result.type is None
    assert result.fieldname is None

    # Try with a lot parameters
    session.archive(overwrite='none',
                    quarantine=False,
                    trigger_pipelines=True,
                    project='project_3',
                    subject='subject_01',
                    experiment='experiment_01_04')

    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/archive'
    assert request.qs == {
        'auto-archive': ['false'],
        'overwrite': ['none'],
        'quarantine': ['false'],
        'triggerpipelines': ['true'],
        'project': ['project_3'],
        'subject': ['subject_01'],
        'session': ['experiment_01_04'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    session.archive(overwrite='append',
                    quarantine=True,
                    trigger_pipelines=False,
                    project='project_2',
                    subject='subject_21',
                    experiment='experiment_21_04')

    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/archive'
    assert request.qs == {
        'auto-archive': ['false'],
        'overwrite': ['append'],
        'quarantine': ['true'],
        'triggerpipelines': ['false'],
        'project': ['project_2'],
        'subject': ['subject_21'],
        'session': ['experiment_21_04'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    with pytest.raises(ValueError):
        session.archive(overwrite='yes please!')

    with pytest.raises(TypeError):
        session.archive(quarantine=1)

    with pytest.raises(TypeError):
        session.archive(trigger_pipelines='yes')


def test_prearchive_session_delete(xnatpy_connection: XNATSession,
                                    xnatpy_mock: XnatpyRequestsMocker,
                                    prearchive_data):
    session = PrearchiveSession(uri='/data/prearchive/projects/project2/20220122_105312641/EXP003',
                                xnat_session=xnatpy_connection)

    xnatpy_mock.post('/data/services/prearchive/delete')

    result = session.delete()
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/delete'
    assert request.qs == {
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    result = session.delete(asynchronous=True)
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/delete'
    assert request.qs == {
        'async': ['true'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    result = session.delete(asynchronous=False)
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/delete'
    assert request.qs == {
        'async': ['false'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    with pytest.raises(TypeError):
        session.delete(asynchronous=42)


def test_prearchive_session_rebuild(xnatpy_connection: XNATSession,
                                    xnatpy_mock: XnatpyRequestsMocker,
                                    prearchive_data):
    session = PrearchiveSession(uri='/data/prearchive/projects/project2/20220122_105312641/EXP003',
                                xnat_session=xnatpy_connection)

    xnatpy_mock.post('/data/services/prearchive/rebuild')

    result = session.rebuild()
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/rebuild'
    assert request.qs == {
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    result = session.rebuild(asynchronous=True)
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/rebuild'
    assert request.qs == {
        'async': ['true'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    result = session.rebuild(asynchronous=False)
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/rebuild'
    assert request.qs == {
        'async': ['false'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    with pytest.raises(TypeError):
        session.rebuild(asynchronous='true')


def test_prearchive_session_move(xnatpy_connection: XNATSession,
                                    xnatpy_mock: XnatpyRequestsMocker,
                                    prearchive_data):
    session = PrearchiveSession(uri='/data/prearchive/projects/project2/20220122_105312641/EXP003',
                                xnat_session=xnatpy_connection)

    xnatpy_mock.post('/data/services/prearchive/move')

    result = session.move(new_project='project_x')
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/move'
    assert request.qs == {
        'newproject': ['project_x'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003']
    }

    result = session.move(new_project='project_y', asynchronous=True)
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/move'
    assert request.qs == {
        'newproject': ['project_y'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003'],
        'async': ['true'],
    }

    result = session.move(new_project='project_x', asynchronous=False)
    assert result.status_code == 200
    request = xnatpy_mock.request_history[-1]
    assert request.method == 'POST'
    assert request.path == '/data/services/prearchive/move'
    assert request.qs == {
        'newproject': ['project_x'],
        'src': ['/data/prearchive/projects/project2/20220122_105312641/exp003'],
        'async': ['false'],
    }

    with pytest.raises(TypeError):
        result = session.move(new_project='project_x', asynchronous=3.14)
