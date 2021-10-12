from nltk import text
import requests
import time
import json
import re
from requests.api import request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import ipadic
import MeCab
import nltk

from .models import Index, Article


def split_to_japanese_word(text):
    """
    MeCabにより、日本語を解析
    品詞に応じて処理
    """
    words = list()
    select_part = ['動詞', '名詞', '形容詞', '形容動詞', '副詞']
    m = MeCab.Tagger(ipadic.MECAB_ARGS)
    #下記の処理をしないとエラーが出る
    text = str(text).lower()
    node = m.parseToNode(text)
    while node:
        if node is not None:
            pos = node.feature.split(',')[0]
            if pos in select_part:
                words.append(node.surface)
        node = node.next
    return words


def split_to_english_word(text):
    """
    英語を解析し、品詞に応じてインデックスのためのkeywordを作成
    """
    # nltk.download('punkt')
    # nltk.download('averaged_perceptron_tagger')
    words = nltk.word_tokenize(text)
    pos = nltk.pos_tag(words)
    words = list()
    select_part = ['PRP', 'NNP', 'VBP', 'NN', 'RB']
    for p in pos:
        word = p[0]
        part = p[1]
        if part in select_part:
            words.append(word)
    return words


def split_word(url, soup, text):
    """
    add_page_to_index関数で使用
    textを分割し、add_to_index関数に渡すための関数
    """
    for line in text.split('\n'):
        line = line.rstrip().lstrip()
        is_japanese = judge_japanese(line)
        if is_japanese and line is not None:
            for keyword in split_to_japanese_word(line):
                add_to_index(keyword, url, soup, text)
        else:
            for keyword in split_to_english_word(line):
                add_to_index(keyword, url, soup, text)


def get_page(page_url):
    """
    指定したurlのページを取得
    """
    r = requests.get(page_url)
    time.sleep(3)
    if r.status_code == 200:
        return r.content


def create_new_article(url, html, content):
    """
    新しいurlを見つけたら、記事のタイトルと共にArticleモデルに保存
    """
    html_head = html.find('head')
    html_body = html.find('body')
    article_title = html_body.find('h1')
    if not article_title:
        article_title = html_body.find('h2')
        if not article_title:
            article_title = html_body.find('h3')
            if not article_title:
                article_title = html_body.find('p')
    if article_title:
        article_title = article_title.get_text()
    if url and article_title:
        Article.objects.create(
            url = url,
            title = article_title,
            content = content)


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


def add_to_index(keyword, url, html, content):
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
                    create_new_article(url, html, content)
                new_index_json = add_index_to_index_json(index_json, url, keyword)
                index.index_json = new_index_json
                index.save()
    else:
        if keyword and not keyword.isspace():
            article = Article.objects.filter(url=url)
            if not article:
                create_new_article(url, html, content)
            index_json = change_index_to_json(keyword, url)
            Index.objects.create(
                keyword = keyword,
                index_json = index_json)


def judge_japanese(line):
    """
    日本語かどうかを判定する処理
    """
    return True if re.search(r'[ぁ-んァ-ン]', line) else False 


def add_page_to_index(url, html):
    """
    取得したページをインデックスに追加
    keywordはmetaタグのテキストか、titleタグのテキストか、h1,h2,h3,h4のテキストから取得
    """
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find('body')
    head_title_tag = soup.find('head').find('title')
    head_meta_description = soup.find('head').find('meta', attrs={'name': 'description'})
    if head_meta_description:
        if head_meta_description['content']:
            print('mata=====================================')
            child_text = head_meta_description['content']
            split_word(url, soup, child_text)
        else:
            print('mata=====================================')
            child_text = head_meta_description.get_text()
            split_word(url, soup, child_text)
    elif head_title_tag:
        print('title=============================')
        child_text = head_title_tag.get_text()
        split_word(url, soup, child_text)
    else:
        print('else======================================')
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
                    split_word(url, soup, child_text)


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
    to_crawl = [seed]
    crawled = []
    next_depth = []
    depth = 0
    while to_crawl and depth <= max_depth and not stop_flag:
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
                # print('new_url_links_list===========================')
                # print(new_url_links_list)
        if not to_crawl:
            to_crawl, next_depth = next_depth, []
            depth += 1
        # print('to_Crawl================================')
        # print(to_crawl)
    return crawled