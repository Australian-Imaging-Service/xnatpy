def test_import():
    from xnat import connect


def test_connect():
    from xnat import connect
    with connect('https://central.xnat.org') as connection:
        print('Connected to XNAT central, running version {}'.format(connection.xnat_version))


def test_list_projects():
    from xnat import connect
    with connect('https://central.xnat.org') as connection:
        print('Projects on XNAT central: {}'.format(connection.projects))
