import click
import xnat

from xnat import exceptions


@click.group(name="import")
@click.pass_context
def importing(ctx):
    pass


@importing.command()
@click.argument('folder')
@click.option('--destination')
@click.option('--project')
@click.option('--subject')
@click.option('--experiment')
@click.option('--import_handler')
@click.option('--quarantine', is_flag=True)
@click.option('--trigger_pipelines', is_flag=True)
@click.pass_context
def experiment(ctx,
               folder,
               destination,
               project,
               subject,
               experiment,
               import_handler,
               quarantine,
               trigger_pipelines):
    try:
        host, user, netrc, jsession, loglevel = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel']
    
        with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                          cli=True, no_parse_model=True, loglevel=loglevel) as session:
            session.services.import_dir(folder, quarantine=quarantine, destination=destination,
                                          trigger_pipelines=trigger_pipelines, project=project, subject=subject,
                                          experiment=experiment, import_handler=import_handler)
    except exceptions.XNATLoginFailedError:
        print(f"ERROR Failed to login")
