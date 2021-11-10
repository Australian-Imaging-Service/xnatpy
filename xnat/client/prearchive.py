import collections
from os import O_WRONLY, stat
from re import sub
import click
import xnat

from .utils import unpack_context

@click.group(name="prearchive")
@click.pass_context
def prearchive(ctx):
    pass


@prearchive.command()
@click.pass_context
def list(ctx):
    host, user, netrc, jsession, loglevel, timeout = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout']

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, loglevel=loglevel) as session:
        click.echo(session.prearchive.sessions())


@prearchive.command()
@click.argument('--project', '-p')
@click.option('--label', '-l')
@click.option('--subject', '-s')
@click.option('--status')
@click.pass_context
def delete(ctx, project, label, subject, status):
    ctx = unpack_context(ctx)

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, loglevel=ctx.loglevel) as session:
        selected_sessions = session.prearchive.find(project=project, subject=subject, label=label, status=status)
        if not selected_sessions:
            session.logger.warning("No prearchive sessions have been selected based on your criteria!")
        else:
            for sess in selected_sessions:
                sess.delete()

@prearchive.command()
@click.argument('--project', '-p')
@click.argument('--dest-project')
@click.option('--label', '-l')
@click.option('--subject', '-s')
@click.option('--status')
@click.pass_context
def move(ctx, project, dest_project, label, subject, status):
    ctx = unpack_context(ctx)

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, loglevel=ctx.loglevel) as session:
        selected_sessions = session.prearchive.find(project=project, subject=subject, label=label, status=status)
        if not selected_sessions:
            session.logger.warning("No prearchive sessions have been selected based on your criteria!")
        else:
            for sess in selected_sessions:
                sess.move(dest_project)

@prearchive.command()
@click.argument('--sessionid')
@click.argument('--project')
@click.option('--subject')
@click.option('--experiment')
@click.option('--overwrite', is_flag=True)
@click.option('--quarantine')
@click.option('--trigger-pipelines', is_flag=True)
@click.pass_context
def archive(ctx, sessionid, project, subject, experiment, overwrite, quarantine, trigger_pipelines):
    ctx = unpack_context(ctx)

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, loglevel=ctx.loglevel) as session:
        selected_session = None
        for sess in session.prearchive.sessions:
            if sess.id == sessionid:
                selected_session = sess
                break
        
        if not selected_session:
            session.logger.warning("No prearchive sessions have been selected based on your criteria!")
        else:
            sess.archive(project=project, subject=subject, experiment=experiment, overwrite=overwrite, quarantine=quarantine, trigger_pipelines=trigger_pipelines)


prearchive.command()
@click.argument('--project', '-p')
@click.option('--label', '-l')
@click.option('--subject', '-s')
@click.option('--status')
@click.option('--overwrite', is_flag=True)
@click.option('--quarantine')
@click.option('--trigger-pipelines', is_flag=True)
@click.pass_context
def bulk_archive(ctx, project, dest_project, label, subject, status, overwrite, quarantine, trigger_pipelines):
    ctx = unpack_context(ctx)

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, loglevel=ctx.loglevel) as session:
        selected_sessions = session.prearchive.find(project=project, subject=subject, label=label, status=status)
        if not selected_sessions:
            session.logger.warning("No prearchive sessions have been selected based on your criteria!")
        else:
            for sess in selected_sessions:
                sess.archive(overwrite=overwrite, quarantine=quarantine, trigger_pipelines = trigger_pipelines)