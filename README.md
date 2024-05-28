# Gamescrape
useage:
gamescrape <game name> [options]

The following options are available:

-info: Get additional information about the game, such as its release date, genre, and developer.
-id: Get the game's unique identifier.

For example, to get the release date of the game "Baldur's Gate 3", you would run the following command:
```rb
gamescrape "Baldur's Gate 3" -info release_date
```

Output
The gamescrape package outputs the game data in a human-readable format. The following fields are included in the output:

id: steam id
detailed_description: detailed description of the game
short_description: short description of the game
pc_requirements: pc requirements of the game
date: release date of the game
price: the price of the game on steam

The following are some examples of how to use the gamescrape package:
### Get the release date of the game "Baldur's Gate 3"
```rb
gamescrape "Baldur's Gate 3" -info release_date
```

### Get the Price score of the game "Cyberpunk 2077"
```rb
gamescrape "Cyberpunk 2077" -info price
```

### Get the PC Requirements of the game "The Witcher 3: Wild Hunt"
```rb
gamescrape "The Witcher 3: Wild Hunt" -info pc_requirements
```

### Get all of the data for the game "Elden Ring"
```rb
gamescrape "Elden Ring"
```
