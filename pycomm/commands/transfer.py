import click
import os

from pycomm.commands.file_client import FileClient

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('transfer', context_settings=CONTEXT_SETTINGS,
               short_help='Send/Receive files from a created server')
@click.option('-s', '--send', 'send', nargs=1,
              type=str, help='Send a file to a server')
@click.option('-r', '--receive', 'receive', nargs=1,
              type=str, help='Receive a file from a server')
@click.option('-l', '--list', 'list_files',
              is_flag=True, help='List all files stored on the server')
@click.option('-p', '--path', 'path', nargs=1,
              type=click.Path(writable=True, readable=True),
              default=lambda: os.environ.get('PWD', ''),
              show_default='current directory',
              help='Location for retrieved files to be written')
@click.argument('host', type=str, required=True)
@click.argument('port', type=int, required=True)
def transfer(send, receive, list_files, path, host, port):
    # Check the existence of the provided storage path
    if not os.path.exists(path):
        raise click.UsageError("No such path")

    if send:
        file_path = os.path.join(path, send[0])

        if not os.path.isfile(file_path):
            raise click.UsageError("No such file")

        client = FileClient(host=host, port=port, file=send, path=path, file_op='send')
        client.connect()

    elif receive:
        client = FileClient(host=host, port=port, file=receive, path=path, file_op='receive')
        client.connect()

    elif list_files:
        client = FileClient(host=host, port=port, file='', path=path, file_op='list')
        client.connect()
    else:
        raise click.UsageError('Missing option')
