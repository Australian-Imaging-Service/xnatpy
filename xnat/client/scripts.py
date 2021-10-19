import click
import xnat

from ..scripts.copy_project import XNATProjectCopier


@click.group(name="script")
def script():
    pass

@script.command()
@click.option("--source-host", required=True, help="Source XNAT URL")
@click.option("--source-project", required=True, help="Source XNAT project")
@click.option("--dest-host", required=True, help="Destination XNAT URL")
@click.option("--dest-project", required=True, help="Destination XNAT project")
def copy_project(source_host, source_project, dest_host, dest_project):
    with xnat.connect(source_host) as source_xnat, xnat.connect(dest_host) as dest_xnat:
        # Find projects
        try:
            source_project = source_xnat.projects[source_project]
            dest_project = dest_xnat.projects[dest_project]
        except KeyError as error:
            print(error.message)
        else:
            # Create and start copier
            copier = XNATProjectCopier(source_xnat, source_project, dest_xnat, dest_project)
            copier.start()
