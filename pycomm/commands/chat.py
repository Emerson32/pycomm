#!/usr/bin/env python3

# chat.py - Command used to initiate and connect to the chat server

import click
import subprocess
import sys

from prompt_toolkit.shortcuts import prompt

from pycomm.commands.prompt_styles import username_style, username_prompt
from pycomm.commands.chat_service import ChatService
from pycomm.commands.chat_client import ChatClient

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('chat', context_settings=CONTEXT_SETTINGS,
               short_help='Initiate or connect to a chat service')
@click.option('-i', '--init', 'init', is_flag=True,
              help='Initiate a chat service args=[ip/host, port]')
@click.argument('host', type=str, required=True)
@click.argument('port', type=int, required=True)
def chat(init, host, port):

    if init:

        server = ChatService(host=host, port=port)
        server.start()

    else:

        username = prompt(username_prompt, style=username_style)

        client = ChatClient(host, port, username)

        client.connect()






