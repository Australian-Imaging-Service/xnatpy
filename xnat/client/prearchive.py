import click
import xnat


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
