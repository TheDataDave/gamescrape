import re
from collections import namedtuple
def parse(user_input):
    '''Prase user input'''
    # Define the regex pattern
    pattern = r"^\/get-game ([a-zA-Z0-9\s]+)(?:[-info]*)(\s*[a-zA-Z_]*)$"

    # Search for matches in the input string
    match = re.search(pattern, user_input)

    Info = namedtuple('Info', ['info'])

    if match:
        # Extract the game name
        game_name = str(match.group(1)).strip()

        # Extract the info (if provided)
        info = match.group(2) if match.group(2) else 'N/A'

        args = Info(info=str(info).strip())
    else:
        game_name = user_input
        args = Info(info='N/A')
    print("***", game_name, args)
    return (game_name, args)

print(parse("/get-game   baldurs gate   3   -info   id"))
