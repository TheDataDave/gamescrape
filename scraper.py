from bs4 import BeautifulSoup
import requests


class Scraper:
    '''Superclass that defines common HTTP get logic'''
    def __init__(self, url):
        self.url = url
    
    def get_html(self) -> bytes:
        '''Gets the HTML from the URL'''
        response = requests.get(self.url)
        return response.content

    def parse_html(self):
        raise NotImplementedError("Please subclass this class and implement logic...")

class SteamScraper(Scraper):
    '''
    Scrapes the Steam website for top 10 results IDs based on a users query of a game name
    overriding the parse_html method in the parent class.
    '''
    def __init__(self, url, result_limit=10) -> None:
        super().__init__(url)
        self.result_limit = result_limit

    def _parse_html(self) -> list:
        '''Overrides parents method to parse the HTML from the website for top 10 results IDs'''
        # Get HTML and Build BeautifulSoup parser
        html = self.get_html()
        soup = BeautifulSoup(html, 'html.parser')
        game_elements = soup.find_all("a", class_="search_result_row ds_collapse_flag")

        # Get ID's of each result
        # Grab top 10 results
        ids = []
        for game_element in game_elements:
            href = game_element['href']
            href_parts = href.split("/")
            # [3]: App/Bundle [4]: ID
            if href_parts[3].lower().strip() == "app": # Apps only no bundles
                ids.append(href_parts[4])
            if len(ids) >= self.result_limit: # Break after we hit the result limit
                break
        return ids


    def get_games(self):
        '''Returns a list of games in JSON format'''
        for id in self._parse_html():
            url = f"https://store.steampowered.com/api/appdetails?appids={id}"
            result = requests.get(url).json().get(id).get('data')
            result['id'] = id
            yield result



def main():
    ss = SteamScraper("https://store.steampowered.com/search/?term=baldurs+gate+3")
    for result in ss.get_games():
        name = result.get('name')
        short_desc = result.get('price_overview')
        print(f'{name}: {short_desc}\n')




if __name__ == '__main__':
    main()