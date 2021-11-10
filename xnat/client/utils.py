from collections import namedtuple

CLIContext = namedtuple('CLIContext', 'host user netrc jsession loglevel timeout')

def unpack_context(ctx):
    return CLIContext(ctx.obj['host'], ctx.obj['user'], ctx.obj['netrc'], ctx.obj['jsession'], ctx.obj['loglevel'], ctx.obj['timeout'])