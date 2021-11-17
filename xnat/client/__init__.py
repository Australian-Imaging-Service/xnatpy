import click
import xnat

from .utils import unpack_context

from .download import download
from .importing import importing
from .listings import listings
from .search import search
from .rest import rest
from .scripts import script
from .prearchive import prearchive


@click.group()
@click.version_option()
@click.option('--jsession', envvar='XNATPY_JSESSION')
@click.option('--user', '-u')
@click.option('--host', '-h', envvar='XNATPY_HOST')
@click.option('--netrc', '-n')
@click.option('--loglevel', envvar='XNATPY_LOGLEVEL')
@click.option('--timeout', envvar="XNATPY_TIMEOUT", type=float)
@click.pass_context
def cli(ctx, host, jsession, user, netrc, loglevel, timeout):
    ctx.ensure_object(dict)
    ctx.obj['host'] = host
    ctx.obj['jsession'] = jsession
    ctx.obj['user'] = user
    ctx.obj['netrc'] = netrc
    ctx.obj['loglevel'] = loglevel
    ctx.obj['timeout'] = timeout


cli.add_command(download)
cli.add_command(listings)
cli.add_command(importing)
cli.add_command(search)
cli.add_command(rest)
cli.add_command(script)
cli.add_command(prearchive)


@cli.command()
@click.pass_context
def login(ctx):
    """
    Establish a connection to XNAT and print the JSESSIONID so it can be used in sequent calls.
    The session is purposefully not closed so will live for next commands to use until it will
    time-out.
    """
    ctx = unpack_context(ctx)
    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        click.echo(session.jsession)


@cli.command()
@click.pass_context
def logout(ctx):
    ctx = unpack_context(ctx)
    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      no_parse_model=True, loglevel=ctx.loglevel) as session:
        pass
    click.echo('Disconnected from {host}!'.format(host=ctx.host))


if __name__ == '__main__':
    cli()