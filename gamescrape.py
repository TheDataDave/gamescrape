from gamescrape.db import GameDatabase, Game
from gamescrape.scraper import SteamScraper
from collections import namedtuple
import re

def main(game_name, db) -> Game:
    '''
    @param game_name: Name of the game to search for
    @param db: GameDatabase object
    @return: Game object

    Give a game name and the database object, scrapes steams search results
    and returns the first result. If the game is already in the database,
    returns the game from the database.
    '''
    search_term = "+".join(game_name.split(" "))
    url = f"https://store.steampowered.com/search/?term={search_term}"
    ss = SteamScraper(url)
    first_game = ''
    for x, game_json in enumerate(ss.get_games()):
        if x == 0:
            first_game = game_json.get('name')
            game = db.get_game(first_game)
        if game:
            return game
        else:
            db.save_game(game_json)
    db.commit()
    return db.get_game(first_game)

def parse(user_input) -> str:
    '''
    @param user_input: User input
    @return: str

    Parses user input, similiar in nature to argsparse, gets the name and
    optional fields specified in -info:
    id: steam id
    detailed_description: detailed description of the game
    short_description: short description of the game
    pc_requirements: pc requirements of the game
    date: release date of the game
    price: the price of the game on steam
    '''
    # Define the regex pattern
    pattern = r"^\/get-game ([a-zA-Z0-9\s]+)(?:[-info]*)(\s*[a-zA-Z_]*)$"

    # Search for matches in the input string
    match = re.search(pattern, user_input.strip())

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
    return return_game(game_name, args)

def return_game(game_name, args) -> str:
    '''
    @param game_name: Name of the game to search for
    @param args: Info object
    @return: str

    Takes the game name and the info object and returns the requested information
    on the game. If the game is not in the database, returns an error message.
    '''
    db = GameDatabase()
    game = main(game_name, db)
    if game is not None:
        try:
            print("LOG: %s, %s" % (game_name, args))
            if args.info == 'id':
                return("Game Name: %s, Game id: %s" % (game_name, str(game.id)))
            elif args.info == 'detailed_description':
                return("Game Name: %s, Game Description: %s" % (game_name, str(game.detailed_description)))
            elif args.info == 'short_description':
                return("Game Name: %s, Game Description: %s" % (game_name, str(game.short_description)))
            elif args.info == 'pc_requirements':
                return("Game Name: %s, Game PC Requirements: %s" % (game_name, str(game.pc_requirements)))
            elif args.info == 'date' or args.info == 'release_date':
                return("Game Name: %s, Game Release Date: %s" % (game_name, str(game.date)))
            elif args.info == 'price':
                return("Game Name: %s, Game Price: %s" % (game_name, str(game.price)))
            elif args.info is None or args.info == 'N/A':
                return str(game)
            else:
                return(f"{game.name} has no attribute {args.info}, please try your query again.")
        except AttributeError:
            pass
    else:
        return(f"The game: {game_name} was not found.")

    

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Given a games name returns the relevant information via Steams API")

    # Required positional argument
    parser.add_argument('name', type=str,
                        help='Requires a game name to search.')

    # Optional argument
    parser.add_argument('-info', type=str,
                        help='''Return only specific information on the specified game. -id -detailed_description
              -short_description -pc_requirements -url -update_date -price''')

    # Switch
    # parser.add_argument('--switch', action='store_true',
    #                     help='A boolean switch')
    
    args = parser.parse_args()
    print(return_game(args.name, args))