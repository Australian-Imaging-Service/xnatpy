import click
import xnat


@click.group()
def download():
    pass


@download.command()
@click.option('--user', '-u')
@click.option('--host', '-h')
@click.argument('project')
@click.argument('targetdir')
def project(host, user, project, targetdir):
    with xnat.connect(host, user=user) as session:
        xnat_project = session.projects.get(project)

        if project is None:
            print('[ERROR] Could not find project!'.format(project))

        result = xnat_project.download_dir(targetdir)
