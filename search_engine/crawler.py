from bs4.element import ContentMetaAttributeValue
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.api import request
from .models import Index, Article
import ipadic
import MeCab
import time
import json


def split_to_word(text):
    """
    MeCabにより、日本語を解析
    格助詞や助動詞などの特に意味のない日本語
    もキーワードとして追加されるのでそこの除外処理が必要かも
    """
    words = []
    m = MeCab.Tagger(ipadic.MECAB_ARGS)
    #下記の処理をしないとエラーが出る
    text = str(text).lower()
    node = m.parseToNode(text)
    while node:
        words.append(node.surface)
        node = node.next
    return words


def get_page(page_url):
    """
    指定したurlのページを取得
    """
    r = requests.get(page_url)
    time.sleep(3)
    if r.status_code == 200:
        return r.content


def create_new_article(url, html):
    """
    新しいurlを見つけたら、記事のタイトルと共にArticleモデルに保存
    """
    article_title = html.find('body').find('h1')
    if not article_title:
        article_title = html.find('body').find('h2')
        if not article_title:
            article_title = html.find('body').find('h3')
            if not article_title:
                article_title = html.find('body').find('p')
    article_title = article_title.get_text()
    meta_description = html.find('head').find('meta', attrs={'name': 'description'})
    if meta_description is not None:
        content = meta_description.get_text().replace('n', '')
    else:
        content = None
    if url and article_title:
        Article.objects.create(
            url = url,
            title = article_title,
            content = content
        )


def change_index_to_json(keyword, url):
    """
    keywordとurlをjsonに変える処理
    request:
        keyword: string
        url: string
    response:json
    {
        "keyword": keyword,
        "url": [url1, url2, ..]
    }
    """
    index_dict = dict()
    index_dict["keyword"] = keyword
    index_dict['url'] = [url]
    index_json = json.dumps(index_dict, ensure_ascii=False)
    return index_json


def find_url_in_index(index_json, url, keyword):
    """
    Indexモデルに指定のkeywordのurlが存在するか判定するための処理
    request:
        index_json:
            {
                "keyword": keyword,
                "url": [url1, url2, url3, ...]
            }
        url: string
        keyrword: string
    response:
        True or False
    """
    index_json = json.loads(index_json)
    if index_json['keyword'] == keyword:
        urls = index_json['url']
        if url in urls:
            return True
        else:
            return False


def add_index_to_index_json(index_json, url, keyword):
    """
    keywordが既に存在し、かつ、urlが存在しないときに、index_jsonに
    urlを追加する処理
        request:
        index_json:json
            {
                "keyword": keyword,
                "url": [url1, url2, url3, ...]
            }
        url: string
        keyrword: string
    """
    index_json = json.loads(index_json)
    if index_json['keyword'] == keyword:
        url_list = index_json['url']
        url_list.append(url)
        index_json = json.dumps(index_json, ensure_ascii=False)
        return index_json


def add_to_index(keyword, url, html):
    """
    キーワードとurlをDBに追加
    request:
        keyword: string
        url: string
        html: bs4.element.Tag
    """
    index = Index.objects.filter(keyword=keyword).first()
    if index:
        index_json = index.index_json
        if index_json:
            url_exist = find_url_in_index(index_json, url, keyword)
            if not url_exist:
                article = Article.objects.filter(url=url)
                if not article:
                    create_new_article(url, html)
                new_index_json = add_index_to_index_json(index_json, url, keyword)
                index.index_json = new_index_json
                index.save()
    else:
        if keyword and not keyword.isspace():
            article = Article.objects.filter(url=url)
            if not article:
                create_new_article(url, html)
            index_json = change_index_to_json(keyword, url)
            Index.objects.create(
                keyword = keyword,
                index_json = index_json
            )


def add_page_to_index(url, html):
    """
    取得したページをインデックスに追加
    """
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find('head')
    body = soup.find('body')
    if head:
        title_tag = head.find('title')
        meta_description = head.find('meta', attrs={'name': 'description'})
        if title_tag:
            child_text = title_tag.get_text()
            for line in child_text.split('\n'):
                line = line.rstrip().lstrip()
                for keyword in split_to_word(line):
                    add_to_index(keyword, url, soup)
        elif meta_description:
            child_text = meta_description.get_text()
            for line in child_text.split('\n'):
                line = line.rstrip().lstrip()
                for keyword in split_to_word(line):
                    add_to_index(keyword, url, soup)
    elif body:
        for child_tag in body.findChildren():
            if child_tag.name == 'script':
                continue
            #以下でh1, h2, h3といったその記事のキーワードになりそうなタグのテキストを取得
            elif child_tag.name == 'h1':
                child_text = child_tag.text
            elif child_tag.name == 'h2':
                child_text = child_tag.text
            elif child_tag.name == 'h3':
                child_text = child_tag.text
            elif child_tag.name == 'h4':
                child_text = child_tag.text
                if child_text:
                    for line in child_text.split('\n'):
                        line = line.rstrip().lstrip()
                        for keyword in split_to_word(line):
                            add_to_index(keyword, url, soup)



def union_url_links(to_crawl, new_url_links_list):
    """
    クローリングするURLに重複がないように
    するための関数
    """
    for new_url_link in new_url_links_list:
        if new_url_link not in to_crawl:
            to_crawl.append(new_url_link)


def extract_page_url_links(html):
    """
    クローリング先のページのaタグのhref属性を取得
    """
    soup = BeautifulSoup(html, 'html.parser')
    a_tags = soup.find_all('a')
    url_links_list = []
    for a_tag in a_tags:
        a_tag_href = a_tag.get('href')
        if a_tag_href:
            if a_tag_href.startswith('http'):
                url_links_list.append(a_tag_href)
            else:
                continue
    return url_links_list


def crawler(seed, max_depth, stop_flag):
    """
    クローラーのmain関数
    """
    to_crawl = [seed]
    crawled = []
    next_depth = []
    depth = 0
    while not stop_flag:
        while to_crawl and depth <= max_depth:
            page = to_crawl.pop()
            if page not in crawled:
                content = get_page(page)
                if content:
                    add_page_to_index(page, content)
                    new_url_links = extract_page_url_links(content)
                    new_url_links_list = []
                    for new_url_link in new_url_links:
                        new_url_link = str(new_url_link)
                        new_url_links_list.append(new_url_link)
                    union_url_links(to_crawl, new_url_links_list)
                    crawled.append(page)
            if not to_crawl:
                to_crawl, next_depth = next_depth, []
                depth += 1
    return crawled