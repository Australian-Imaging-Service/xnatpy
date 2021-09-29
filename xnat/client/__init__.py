import click
import xnat

from .download import download
from .importing import importing
from .listings import listings
from .search import search


@click.group()
def cli():
    pass


cli.add_command(download)
cli.add_command(listings)
cli.add_command(importing)
cli.add_command(search)


@cli.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h', required=True)
@click.option('--netrc', '-n', required=False, default='~/.netrc')
def get(path, user, host, netrc):
    with xnat.connect(host, user=user, netrc_file=netrc) as session:
        result = session.get(path)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h')
def head(host, path, user):
    with xnat.connect(host, user=user) as session:
        result = session.head(path)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
def post(path, host, user, jsonpath, datapath):
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

    with xnat.connect(host, user=user) as session:
        result = session.post(path, json=json_payload, data=data_payload)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
def put(path, host, user, jsonpath, datapath):
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

    with xnat.connect(host, user=user) as session:
        result = session.put(path, json=json_payload, data=data_payload)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@cli.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h')
def delete(host, path, user):
    with xnat.connect(host, user=user) as session:
        result = session.delete(path)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


if __name__ == '__main__':
    cli()