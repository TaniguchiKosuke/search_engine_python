import requests
from bs4 import BeautifulSoup
from search_engine.models import Article


def get_page(page_url):
    pass


def add_page_to_index(page_url, html):
    pass


def extract_page_url_links(html):
    pass


def crawler(seed, max_depth):
    to_crawl = {seed}
    crawled = []
    next_depth = []
    depth = 0
    while to_crawl and depth <= max_depth:
        page_url = to_crawl.pop()
        if page_url not in crawled:
            html = get_page(page_url)
            add_page_to_index(page_url, html)
            to_crawl = to_crawl.union(extract_page_url_links(html))
            crawled.append(page_url)
        if not to_crawl:
            to_crawl, next_depth = next_depth, []