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
    host, user, netrc, jsession = ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession']

    if not column:
        column = None

    with xnat.connect(host, user=user, netrc_file=netrc, jsession=jsession, cli=True) as session:
        result = session.projects.tabulate_csv(columns=column, filter=filter, header=header)
        print(result)

