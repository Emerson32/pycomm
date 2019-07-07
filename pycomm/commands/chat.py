#!/usr/bin/env python3

# chat.py - Command used to initiate and connect to the chat server

import click


from prompt_toolkit.shortcuts import prompt

from pycomm.commands.prompt_styles import username_style, username_prompt
from pycomm.commands.chat_client import ChatClient

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('chat', context_settings=CONTEXT_SETTINGS,
               short_help='Connect to a chat service')
@click.argument('host', type=str, required=True)
@click.argument('port', type=int, required=True)
def chat(host, port):
    # Grab the username
    username = prompt(username_prompt, style=username_style)

    client = ChatClient(host, port, username)

    try:
        client.connect()
    except KeyboardInterrupt:
        client.disconnect()






