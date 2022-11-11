from pytest import fixture
from xnat import XNATSession
from xnat.conftest import XnatpyRequestsMocker
from xnat.prearchive import Prearchive


@fixture()
def prearchive_data(xnatpy_mock: XnatpyRequestsMocker):
    data = [
        {
            'scan_time': '',
            'status': 'READY',
            'subject': 'SUB1',
            'tag': '',
            'TIMEZONE': '',
            'uploaded': '2021-12-29 10:11:28.996',
            'lastmod': '2022-01-18 16:41:25.0',
            'scan_date': '',
            'url': '/prearchive/projects/project1/20220122_105154616/NAME001',
            'timestamp': '20211229_101128996',
            'prevent_auto_commit': 'false',
            'project': 'project1',
            'SOURCE': '',
            'prevent_anon': 'false',
            'autoarchive': 'Manual',
            'name': 'NAME001',
            'folderName': 'NAME001',
            'VISIT': '',
            'PROTOCOL': ''
        },
        {
            'scan_time': '',
            'status': 'ERROR',
            'subject': 'SUB2',
            'tag': '',
            'TIMEZONE': '',
            'uploaded': '2021-12-29 10:11:28.996',
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
        xnatpy_mock.get(f"/data{item['url']}", json={'ResultSet': {'Result': [item]}})


def test_prearchive_sessions(xnatpy_connection: XNATSession,
                             prearchive_data):
    # Test data for multiple projects
    prearchive = Prearchive(xnatpy_connection)
    result = prearchive.sessions()

    assert len(result) == 3
    assert result[0].name == 'NAME001'
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105154616/NAME001'
    assert result[1].name == 'NAME002'
    assert result[1].uri == '/data/prearchive/projects/project1/20220122_105234872/NAME002'
    assert result[2].name == 'EXP003'
    assert result[2].uri == '/data/prearchive/projects/project2/20220122_105312641/EXP003'

    result_project = prearchive.sessions(project='project2')
    assert len(result_project) == 1
    assert result_project[0].name == 'EXP003'
    assert result_project[0].uri == '/data/prearchive/projects/project2/20220122_105312641/EXP003'


def test_prearchive_find(xnatpy_connection: XNATSession,
                         prearchive_data):
    prearchive = Prearchive(xnatpy_connection)

    # Search by project/status
    result = prearchive.find(project='project1', status='READY')
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105154616/NAME001'

    # Search by project/status
    result = prearchive.find(project='project1', status='ERROR')
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105234872/NAME002'

    # Search by session
    result = prearchive.find(session='NAME002')
    assert len(result) == 1
    assert result[0].uri == '/data/prearchive/projects/project1/20220122_105234872/NAME002'

    # Search by subject
    result = prearchive.find(subject='SUB001')
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

