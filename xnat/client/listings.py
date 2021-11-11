import click
import xnat

from .utils import unpack_context

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
    ctx = unpack_context(ctx)

    if not column:
        column = None

    if filter:
        filter = filter.split('=')
        filter = {filter[0]: filter[1]}

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.projects.tabulate_csv(columns=column, filter=filter, header=header)

        # Print result without trailing newline/whitespace
        print(result.strip())


@listings.command()
@click.option('--filter')
@click.option('--header/--no-header', default=True)
@click.option('--column', multiple=True)
@click.pass_context
def subjects(ctx, column, filter, header):
    ctx = unpack_context(ctx)
    
    if not column:
        column = None

    if filter:
        filter = filter.split('=')
        filter = {filter[0]: filter[1]}

    with xnat.connect(ctx.host, user=ctx.user, netrc_file=ctx.netrc, jsession=ctx.jsession,
                      cli=True, no_parse_model=True, loglevel=ctx.loglevel) as session:
        result = session.subjects.tabulate_csv(columns=column, filter=filter, header=header)

        # Print result without trailing newline/whitespace
        print(result.strip())
