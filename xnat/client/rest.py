import click
import xnat


@click.group(name="rest")
@click.pass_context
def rest(ctx):
    pass

@rest.command()
@click.argument('path')
@click.option('--query', multiple=True)
@click.pass_context
def get(ctx, path, query):
    host, user, netrc, jsession, loglevel, timeout = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout']
    
    if query:
        query = {arg[0]:arg[1] for arg in map(lambda x: x.split("="), query)}
    
    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True, loglevel=loglevel) as session:
        result = session.get(path, query=query, timeout=timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@rest.command()
@click.argument('path')
@click.option('--user', '-u')
@click.option('--host', '-h', required=True, envvar='XNATPY_HOST')
@click.pass_context
def head(ctx, path):
    host, user, netrc, jsession, loglevel, timeout = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout']
    
    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True, loglevel=loglevel) as session:
        result = session.head(path, timeout=timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@rest.command()
@click.argument('path')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
@click.option('--query', multiple=True)
@click.pass_context
def post(ctx, path, jsonpath, datapath, query):
    host, user, netrc, jsession, loglevel, timeout = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout']
    
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

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True, loglevel=loglevel) as session:
        result = session.post(path, json=json_payload, data=data_payload, query=query, timeout=timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@rest.command()
@click.argument('path')
@click.option('--jsonpath', '-j')
@click.option('--datapath', '-d')
@click.option('--query', multiple=True)
@click.pass_context
def put(ctx, path, jsonpath, datapath, query):
    host, user, netrc, jsession, loglevel, timeout = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout']
    
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

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True, loglevel=loglevel) as session:
        result = session.put(path, json=json_payload, data=data_payload, query=query, timeout=timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')


@rest.command()
@click.argument('path')
@click.pass_context
def delete(ctx, path):
    host, user, netrc, jsession, loglevel, timeout = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout']
    
    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession,
                      cli=True, no_parse_model=True, loglevel=loglevel) as session:
        result = session.delete(path, timeout=timeout)
        click.echo(f'Result: {result.text}')
        click.echo(f'Path {path} {user}')
