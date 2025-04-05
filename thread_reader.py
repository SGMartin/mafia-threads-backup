import math
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#
# SGMartin 2025: Adapted from mv mafia bot
#


# Helper functions
def fetch_html(url: str) -> BeautifulSoup:
    """Fetch and parse HTML from a given URL."""
    retries = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retries)
    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    try:
        response = session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return BeautifulSoup("", 'html.parser')


def get_total_pages(html: BeautifulSoup) -> int:
    """Extract the total number of pages from the page navigation panel."""
    try:
        panel = html.find('div', id='bottompanel')
        last_page_link = panel.find_all('a')[-2].text
        return int(last_page_link)
    except (AttributeError, IndexError, ValueError):
        return 1


def get_posts_from_page(game_thread: str, author: str, page: int) -> list:
    """Retrieve posts for a specific author on a specific page."""
    url = f"{game_thread}?u={author}&pagina={page}"
    html = fetch_html(url)
    return html.find_all('div', attrs={'data-num': True, 'data-autor': True})


def request_page_count(game_thread: str) -> int:
    """Retrieve the total number of pages in the game thread."""
    html = fetch_html(game_thread)
    return get_total_pages(html)


def get_page_number_from_post(post_id: int) -> int:
    """Calculate the page number of a given post based on 30 posts per page."""
    return math.ceil(post_id / 30)


def get_thread_title(html: BeautifulSoup) -> str:
    """Extract the thread title."""
    try:
        title = html.find("meta", property="og:title").get("content")
        return title
    except (ValueError):
        return None
