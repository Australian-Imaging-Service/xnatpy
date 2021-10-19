import click
import xnat

from .download import download
from .importing import importing
from .listings import listings
from .search import search
from .rest import rest


@click.group()
@click.version_option()
@click.option('--jsession', envvar='XNATPY_JSESSION')
@click.option('--user', '-u')
@click.option('--host', '-h', required=True, envvar='XNATPY_HOST')
@click.option('--netrc', '-n', required=False)
@click.pass_context
def cli(ctx, host, jsession, user, netrc):
    ctx.ensure_object(dict)
    ctx.obj['host'] = host
    ctx.obj['jsession'] = jsession
    ctx.obj['user'] = user
    ctx.obj['netrc'] = netrc


cli.add_command(download)
cli.add_command(listings)
cli.add_command(importing)
cli.add_command(search)
cli.add_command(rest)


@cli.command()
@click.pass_context
def login(ctx):
    """
    Establish a connection to XNAT and print the JSESSIONID so it can be used in sequent calls.
    The session is purposefully not closed so will live for next commands to use until it will
    time-out.
    """
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']
    with xnat.connect(host, user=user, netrc_file=netrc, cli=True, no_parse_model=True) as session:
        print(session.jsession)


@cli.command()
@click.pass_context
def logout(ctx):
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']
    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      no_parse_model=True) as session:
        pass
    print('Disconnected from {host}!'.format(host=host))


if __name__ == '__main__':
    cli()