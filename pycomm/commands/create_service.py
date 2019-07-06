import click
import os

from pycomm.commands.chat_service import ChatService
from pycomm.commands.file_service import FileService
from pycomm.commands.shell_service import ShellService


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('create', context_settings=CONTEXT_SETTINGS,
               short_help='Initiate a service')
@click.option('-c', '--chat', 'chat',
              is_flag=True, help='Initiate a chat service on the local machine')
@click.option('-f', '--file', 'file', is_flag=True,
              help='Initiate a file transfer service on the local machine')
@click.option('-p', '--path', 'path', nargs=1,
              type=click.Path(writable=True, readable=True),
              default=lambda: os.environ.get('PWD', ''),
              show_default='current directory',
              help='Location for service files to be read/written')
@click.option('-r', '--reverse_shell', 'reverse', is_flag=True,
              help='Initiate a reverse shell service')
@click.argument('host',  type=str, required=True)
@click.argument('port',  type=int, required=True)
def create_service(chat, file, reverse, host, port, path):
    if chat:
        service = ChatService(host, port)
        service.start()
    elif file:
        service = FileService(host, port, path)
        service.start()
    elif reverse:
        service = ShellService(host, port)
        service.start()
    else:
        raise click.UsageError('Missing service option')
