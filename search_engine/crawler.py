import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .models import Index
import ipadic
import MeCab


def split_to_word(text):
    words = []
    # m = MeCab.Tagger("-Ochasen")
    m = MeCab.Tagger(ipadic.MECAB_ARGS)
    text = str(text).lower()
    node = m.parseToNode(text)
    while node:
        words.append(node.surface)
        node = node.next
    return words


def get_page(page_url):
    r = requests.get(page_url)
    if r.status_code == 200:
        return r.content


def add_to_index(index, keyword, url):
    for entry in index:
        if entry['keyword'] == keyword:
            if not url in entry['url']:
                entry['url'].append(url)
            return
    url = [url]
    Index.objects.create(
        keyword = keyword,
        url =url
    )


def add_page_to_index(index, url, html):
    body_soup = BeautifulSoup(html, "html.parser").find('body')
    for child_tag in body_soup.findChildren():
        if child_tag.name == 'script':
            continue
        child_text = child_tag.text
        for line in child_text.split('\n'):
            line = line.rstrip().lstrip()
            for keyword in split_to_word(line):
                add_to_index(index, keyword, url)


def extract_page_url_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('a')


def crawler(seed,max_depth):    
    to_crawl = {seed}
    crawled = []
    next_depth = []
    index = []
    depth = 0
    while to_crawl and depth <= max_depth:
        page = to_crawl.pop()
        if page not in crawled:
            content = get_page(page)
            add_page_to_index(index, page, content)
            to_crawl.union(next_depth, extract_page_url_links(get_page(page)))
            crawled.append(page)
        if not to_crawl:
            to_crawl, next_depth = next_depth, []
            depth = depth + 1
    return crawled