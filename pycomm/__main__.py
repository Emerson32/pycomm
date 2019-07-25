#!/usr/bin/env python3
# __main__.py - Entry point for client application

import click

from pycomm.commands.chat import chat
from pycomm.commands.create_service import create_service
from pycomm.commands.reverse_shell import shell
from pycomm.commands.transfer import transfer

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.version_option(version='1.0.0', prog_name='pycomm')
@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    click.clear()


main.add_command(chat)
main.add_command(create_service)
main.add_command(shell)
main.add_command(transfer)
