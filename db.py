from typing import List
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Double
from sqlalchemy.orm import Mapped, sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy import Column as _Column, DateTime, MetaData
from datetime import datetime

import sqlalchemy as sa

# DECLARE BASE
Base = declarative_base()
# Declare a metadata object
metadata = MetaData()

# MAIN INTERACTION WITH DB
def extract_data(json_obj, obj_attrs):
    '''Recursively extract relevant data from JSON object'''

    def _extract_data(json_obj):
        '''Recursive inner-function to extract data from JSON object'''
        _extracted_data = {}
        for key, value in json_obj.items():
            if key == "price_overview":
                _extracted_data['price'] = value            
            elif isinstance(value, dict):
                # If the value is another JSON object, recursively extract data
                _extracted_data.update(_extract_data(value))
            else:
                # Otherwise, directly add the value to the extracted data
                _extracted_data[key] = value
        return _extracted_data
    
    extracted_data = _extract_data(json_obj)
    # Filter out attributes that are not present in the Game class
    return {key: value for key, value in extracted_data.items() if key in obj_attrs}

    

class GameDatabase:
    def __init__(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def __del__(self) -> None:
        '''On garbage collection close session'''
        self.session.close()

    def commit(self) -> None:
        '''Commit the session'''
        self.session.commit()

    def extract_data_and_create(self, json_data):
        '''Extract the relevant data from the JSON object to build 
        the Game, Publisher, Developer, Price and Package objects'''
        # Wouldn't let me use posistional arguments, so used KW instead
        publishers = [Publisher(**{'name':publisher}) for publisher in json_data['publishers']]
        developers = [Developer(**{'name':developer}) for developer in json_data['developers']]
        # Price unpacks cleanly
        price_overview = json_data.get('price_overview', {})
        price_attrs = {
            'currency': price_overview.get('currency', 'N/A'),
            'initial': price_overview.get('initial', 0),
            'final': price_overview.get('final', 0),
            'discount_percent': price_overview.get('discount_percent', 0),
            'initial_formatted': price_overview.get('initial_formatted', ''),
            'final_formatted': price_overview.get('final_formatted', '$0.00')
        }
        price = Price(**price_attrs)  # Pass individual attributes to Price constructor
        # Date
        json_data['date'] = str(json_data.get('release_date', 'N/A').get('date'))
        # PC Requirements
        requirements = json_data.get('pc_requirements', {'minimum':'N/A'})['minimum'] if not isinstance(json_data['pc_requirements'], list) else None
        json_data['pc_requirements'] = requirements
        # Filter for only the attrs that our table needs
        game = Game(**{k:v for k, v in json_data.items() if k in Game.__table__.columns.keys()})
        game.publishers += publishers
        game.developers += developers
        game.price = price

        return game

    def save_game(self, game_json):
        '''Save a new game to the DB if it doesn't exist'''
        self.verify_tables_exist()


        # Create a new instance of the Game class with the filtered JSON object
        game = self.extract_data_and_create(game_json)
        
        # Add the new game object to the session and commit
        self.session.add(game)

    def get_game(self, game_name):
        '''Query for a game via name and return the closest result based on game name'''
        self.verify_tables_exist()
        def calculate_distances(game_name, games) -> Game:
            '''
            Calculate the levenshtein distance between two names to return the most
            accurate result
            '''
            def _levenshtein(s1, s2) -> int:
                if len(s1) < len(s2):
                    return _levenshtein(s2, s1)

                # len(s1) >= len(s2)
                if len(s2) == 0:
                    return len(s1)

                previous_row = range(len(s2) + 1)
                for i, c1 in enumerate(s1):
                    current_row = [i + 1]
                    for j, c2 in enumerate(s2):
                        insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
                        deletions = current_row[j] + 1       # than s2
                        substitutions = previous_row[j] + (c1 != c2)
                        current_row.append(min(insertions, deletions, substitutions))
                    previous_row = current_row

                return previous_row[-1]
            results = sorted([(_levenshtein(game_name, str(game.name)), game) for game in games],
                             key=lambda x: x[0])
            return results[0][1] # Best Result

        # Find the game with the closest levenshtein distance
        games = self.session.query(Game).all()
        # Return None if no games exist
        if games:
            return calculate_distances(game_name, games)
        
    
    def verify_tables_exist(self):
        '''Verify that the tables exist in the DB'''
        insp = sa.inspect(self.engine)
        if not insp.has_table("games"):
            Base.metadata.create_all(self.engine)


# CREATE ASSOCIATIVE TABLES
game_genre_association = Table(
    'game_genre_association',
    Base.metadata,
    Column('game_id', Integer, ForeignKey('games.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

game_developer_association = Table(
    'game_developer_association',
    Base.metadata,
    Column('game_id', Integer, ForeignKey('games.id')),
    Column('developer_id', Integer, ForeignKey('developers.id'))
)

game_publisher_association = Table(
    'game_publisher_association',
    Base.metadata,
    Column('game_id', Integer, ForeignKey('games.id')),
    Column('publisher_id', Integer, ForeignKey('publishers.id'))
)


# CREATE TABLES
class Game(Base):
    '''ORM Representation of the table games'''
    __tablename__ = 'games'
    # __table_args__ = {'sqlite_autoincrement': True}  # Ensure autoincrement for SQLite

    id: Mapped[int] = Column(Integer, primary_key=True) 
    name: Mapped[str] = Column(String)
    detailed_description: Mapped[str] = Column(String)
    short_description: Mapped[str] = Column(String)
    date = Column(String)
    pc_requirements: Mapped[str] = Column(String)
    update_date: Mapped[str] = Column(DateTime, default=func.now())

    price = relationship("Price", back_populates="game")
    price_id = Column(Integer, ForeignKey('prices.id'))
    
    genres: Mapped[List["Genre"]] = relationship('Genre', secondary=game_genre_association, back_populates='games')
    developers: Mapped[List["Developer"]] = relationship('Developer', secondary=game_developer_association, back_populates='games')
    publishers: Mapped[List["Publisher"]] = relationship('Publisher', secondary=game_publisher_association, back_populates='games')

    def __repr__(self):
        return f'''Name: {self.name}, Description: {self.detailed_description}, Short Description: {self.short_description}, Release Date: {self.date}, 
        PC Requirements: {self.pc_requirements}, Price: {self.price}, Generes: {self.genres}, 
        Developers: {self.developers}, Publishers: {self.publishers}'''


class Price(Base):
    '''ORM Representation of the table price_overviews'''
    __tablename__ = 'prices'
    __table_args__ = {'sqlite_autoincrement': True}  # Ensure autoincrement for SQLite

    id = Column(Integer, primary_key=True, autoincrement=True)

    currency: Mapped[str] = Column(String)
    initial: Mapped[float] = Column(Double)
    final: Mapped[float] = Column(Double)
    discount_percent: Mapped[float] = Column(Double)
    initial_formatted: Mapped[str] = Column(String)
    final_formatted: Mapped[str] = Column(String)

    game: Mapped["Game"] = relationship("Game", back_populates='price', foreign_keys='Game.price_id')

    def __repr__(self):
        return f'{self.final_formatted}'

    
class Genre(Base):
    '''ORM Representation of the table genres'''
    __tablename__ = 'genres'
    __table_args__ = {'sqlite_autoincrement': True}  # Ensure autoincrement for SQLite

    id = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String)

    games: Mapped[List["Game"]] = relationship('Game', secondary=game_genre_association, back_populates='genres')

    def __repr__(self):
        return f'{self.name})'
    
class Developer(Base):
    '''ORM Representation of the table developers'''
    __tablename__ = 'developers'
    __table_args__ = {'sqlite_autoincrement': True}  # Ensure autoincrement for SQLite

    id = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String)

    games: Mapped[List["Game"]] = relationship('Game', secondary=game_developer_association, back_populates='developers')

    def __repr__(self):
        return f'{self.name}'
    
class Publisher(Base):
    '''ORM Representation of the table publishers'''
    __tablename__ = 'publishers'
    __table_args__ = {'sqlite_autoincrement': True}  # Ensure autoincrement for SQLite

    id = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String)

    games: Mapped[List["Game"]] = relationship('Game', secondary=game_publisher_association, back_populates='publishers')

    def __repr__(self):
        return f'{self.name}'