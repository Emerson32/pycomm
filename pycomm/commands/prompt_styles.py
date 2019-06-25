from prompt_toolkit.styles import Style

# Build prompt styling
username_style = Style.from_dict({
    # User input
    '': '#eaeaea',

    # Prompt
    'username_prompt': '#50ce65'
})

username_prompt = [
    ('class:username_prompt', 'Username: ')
]

message_style = Style.from_dict({
    # User Input
    '': '#0599fc',

    # Prompt
    'message_prompt': '#50ce65'
})
