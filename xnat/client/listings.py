import click
import xnat


@click.group(name="list")
@click.pass_context
def listings(ctx):
    pass

@listings.command()
@click.option('--filter')
@click.option('--header/--no-header', default=True)
@click.option('--column', multiple=True)
@click.pass_context
def projects(ctx, column, filter, header):
    host, user, netrc, jsession, loglevel = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel']
    
    if not column:
        column = None

    if filter:
        filter = filter.split('=')
        filter = {filter[0]: filter[1]}

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession, cli=True, loglevel=loglevel) as session:
        result = session.projects.tabulate_csv(columns=column, filter=filter, header=header)

        # Print result without trailing newline/whitespace
        print(result.strip())


@listings.command()
@click.option('--filter')
@click.option('--header/--no-header', default=True)
@click.option('--column', multiple=True)
@click.pass_context
def subjects(ctx, column, filter, header):
    host, user, netrc, jsession, loglevel = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel']
    
    if not column:
        column = None

    if filter:
        filter = filter.split('=')
        filter = {filter[0]: filter[1]}

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession, cli=True, loglevel=loglevel) as session:
        result = session.subjects.tabulate_csv(columns=column, filter=filter, header=header)

        # Print result without trailing newline/whitespace
        print(result.strip())
