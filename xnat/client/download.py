import click
import xnat


@click.group()
@click.pass_context
def download(ctx):
    pass


@download.command()
@click.argument('project')
@click.argument('targetdir')
@click.pass_context
def project(host, user, project, targetdir):
    with xnat.connect(host, user=user) as session:
        xnat_project = session.projects.get(project)

        if project is None:
            print('[ERROR] Could not find project!'.format(project))

        result = xnat_project.download_dir(targetdir)
