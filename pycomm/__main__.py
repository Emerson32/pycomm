#!/usr/bin/env python3
# __main__.py - Entry point for client application

import click
import sys

from pycomm.commands.chat import chat
from pycomm.commands.create_service import create_service
from pycomm.commands.transfer import transfer
from pycomm.commands.reverse_shell import shell

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.version_option(version='1.0.0', prog_name='pycomm')
@click.group(invoke_without_command=True,
             context_settings=CONTEXT_SETTINGS)
def main():
    if len(sys.argv) == 1:
        raise click.UsageError('Missing option or subcommand')


main.add_command(chat)
main.add_command(create_service)
main.add_command(shell)
main.add_command(transfer)

