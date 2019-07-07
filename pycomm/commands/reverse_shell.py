import click
from pycomm.commands.shell_client import ShellClient

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('shell', context_settings=CONTEXT_SETTINGS,
               short_help='Connect to a reverse shell service')
@click.argument('host', type=str, required=True)
@click.argument('port', type=int, required=True)
def shell(host, port):
    client = ShellClient(host, port)

    try:
        client.connect()
    except KeyboardInterrupt:
        client.disconnect()

