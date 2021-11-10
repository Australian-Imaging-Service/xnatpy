import click
import xnat

from .utils import unpack_context

@click.group(name="rest")
@click.pass_context
def rest(ctx):
    pass

@rest.command()
@click.argument('path')
@click.option('--query', multiple=True)
@click.pass_context
def get(ctx, path, query):
    ctx = unpack_context(ctx)
    
    if query:
        query = {arg[0]:arg[1] for arg in map(lambda x: x.split("="), query)}
    
    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.get(path, query=query, timeout=ctx.timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {ctx.user}')


@rest.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h', required=True, envvar='XNATPY_HOST')
@click.pass_context
def head(ctx, path):
    ctx = unpack_context(ctx)
    
    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.head(path, timeout=ctx.timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {ctx.user}')


@rest.command()
@click.argument('path')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
@click.option('--query', multiple=True)
@click.pass_context
def post(ctx, path, jsonpath, datapath, query):
    ctx = unpack_context(ctx)
    
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

    if query:
        query = {arg[0]:arg[1] for arg in map(lambda x: x.split("="), query)}

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.post(path, json=json_payload, data=data_payload, query=query, timeout=ctx.timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {ctx.user}')


@rest.command()
@click.argument('path')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
@click.option('--query', multiple=True)
@click.pass_context
def put(ctx, path, jsonpath, datapath, query):
    ctx = unpack_context(ctx)
    
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
    
    if query:
        query = {arg[0]:arg[1] for arg in map(lambda x: x.split("="), query)}

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.put(path, json=json_payload, data=data_payload, query=query, timeout=ctx.timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {ctx.user}')


@rest.command()
@click.argument('path')
@click.pass_context
def delete(ctx, path):
    ctx = unpack_context(ctx)
    
    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.delete(path, timeout=ctx.timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {ctx.user}')
