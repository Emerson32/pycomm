import click
import os

from pycomm.commands.file_client import FileClient

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('transfer', context_settings=CONTEXT_SETTINGS,
               short_help='Send/Receive files from a created server')
@click.option('-s', '--send', 'send',
              is_flag=True, help='Send a file to a server')
@click.option('-r', '--receive', 'receive',
              is_flag=True, help='Receive a file from a server')
@click.option('-p', '--path', 'path', nargs=1,
              type=click.Path(writable=True, readable=True),
              default=lambda: os.environ.get('PWD', ''),
              show_default='current directory',
              help='Location for retrieved files to be written')
@click.argument('file', type=str, required=True)
@click.argument('host', type=str, required=True)
@click.argument('port', type=int, required=True)
def transfer(send, receive, file, path, host, port):
    # Check the existence of the provided storage path
    if not os.path.exists(path):
        raise click.UsageError("No such path")

    if send:
        file_path = os.path.join(path, file)

        if not os.path.isfile(file_path):
            raise click.UsageError("No such file")

        client = FileClient(host, port, file, path, 'send')
        client.connect()

    elif receive:
        client = FileClient(host, port, file, path, 'receive')
        client.connect()
    else:
        raise click.UsageError('Missing option')
