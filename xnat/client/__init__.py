import click
import xnat

from .download import download
from .importing import importing
from .listings import listings
from .search import search


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


@cli.command()
@click.argument('path')
@click.pass_context
def get(ctx, path):
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True) as session:
        result = session.get(path)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h', required=True, envvar='XNATPY_HOST')
@click.pass_context
def head(ctx, path):
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True) as session:
        result = session.head(path)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
@click.pass_context
def post(ctx, path, jsonpath, datapath):
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']

    if jsonpath is not None:
        with open(jsonpath, 'r') as json_file:
            json_payload = json_file.read()
    else:
        json_payload = None
    
    if datapath is not None:
        with open(datapath, 'r') as data_file:
            data_payload = data_file.read()
    else:
        data_payload = None

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True) as session:
        result = session.post(path, json=json_payload, data=data_payload)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
@click.pass_context
def put(ctx, path, jsonpath, datapath):
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']

    if jsonpath is not None:
        with open(jsonpath, 'r') as json_file:
            json_payload = json_file.read()
    else:
        json_payload = None
    
    if datapath is not None:
        with open(datapath, 'r') as data_file:
            data_payload = data_file.read()
    else:
        data_payload = None

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True) as session:
        result = session.put(path, json=json_payload, data=data_payload)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.pass_context
def delete(ctx, path):
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True) as session:
        result = session.delete(path)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


if __name__ == '__main__':
    cli()