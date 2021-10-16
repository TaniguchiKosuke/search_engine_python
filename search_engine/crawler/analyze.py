from nltk import text
import time
import json
import re

from bs4 import BeautifulSoup
import ipadic
import MeCab
import nltk

from ..models import Index, Article, ToAnalyzePage


# def get_page(page_url):
#     """
#     url取得
#     crawl.pyでも同じ関数を持っているため、ConnectionErrorが発生すると思う。
#     短時間でリクエストしすぎ。
#     """
#     try:
#         proxies_dic = {
#             "http": "http://proxy.example.co.jp:8080",
#             "https": "http://proxy.example.co.jp:8080",}
#         r = requests.get(page_url, timeout=(3.0, 7.5), proxies=proxies_dic, verify=False)
#         time.sleep(3)
#         if r.status_code == 200:
#             return r.content
#     except requests.ConnectionError as e:
#         print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
#         print(str(e))            


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


def judge_japanese(line):
    """
    日本語かどうかを判定する処理
    """
    return True if re.search(r'[ぁ-んァ-ン]', line) else False 


def create_new_article(url, html, content):
    """
    新しいurlを見つけたら、記事のタイトルと共にArticleモデルに保存
    """
    html_head = html.find('head')
    html_body = html.find('body')
    html_title = html_head.find('title')
    if html_title:
        article_title = html_title.get_text()
        if not article_title and html_body.find('h1'):
              article_title = html_body.find('h1').get_text()
              if not article_title and html_body.find('h2'):
                  article_title = html_body.find('h2').get_text()
                  if not article_title and html_body.find('h3'):
                      article_title = html_body.find('h3').get_text()
                      if not article_title and html_body.find('h4'):
                          article_title = html_body.find('h4').get_text()
    else:
        article_title = html_body.find('h1').get_text()
        if not article_title and html_body.find('h2'):
            article_title = html_body.find('h2').get_text()
            if not article_title and html_body.find('h3'):
                article_title = html_body.find('h3').get_text()
                if not article_title and html_body.find('h4'):
                    article_title = html_body.find('h4').get_text()
    if url and article_title and not article_title.isspace():
          Article.objects.create(
              url = url,
              title = article_title,
              content = content)


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


def add_to_index(keyword, url, html, content):
    """
    キーワードとurlをDBに追加
    request:
        keyword: string
        url: string
        html: bs4.element.Tag
    """
    index = Index.objects.filter(keyword=keyword).first()
    article = Article.objects.filter(url=url)
    if not article:
        create_new_article(url, html, content)
    if index:
        print('index exists ==============================')
        index_json = index.index_json
        if index_json:
            url_exist = find_url_in_index(index_json, url, keyword)
            if not url_exist:
                new_index_json = add_index_to_index_json(index_json, url, keyword)
                index.index_json = new_index_json
                index.save()
    else:
        print('index does not exist=================================')
        if keyword and not keyword.isspace():
            index_json = change_index_to_json(keyword, url)
            Index.objects.create(
                keyword = keyword,
                index_json = index_json)


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


def add_page_to_index(url, html):
    """
    取得したページをインデックスに追加
    keywordはmetaタグのテキストか、titleタグのテキストか、h1,h2,h3,h4のテキストから取得
    """
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find('body')
    head = soup.find('head')
    if head:
        head_title_tag = head.find('title')
        head_meta_description = head.find('meta', attrs={'name': 'description'})
        if head_meta_description:
            if head_meta_description['content']:
                child_text = head_meta_description['content']
                split_word(url, soup, child_text)
            else:
                child_text = head_meta_description.get_text()
                split_word(url, soup, child_text)
        if head_title_tag:
            child_text = head_title_tag.get_text()
            split_word(url, soup, child_text)
        if not head_meta_description and not head_title_tag:
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


# def analyze():
#     to_analyze_page = ToAnalyzePage.objects.all()[:10]
#     if to_analyze_page:
#         for page in to_analyze_page:
#             page_url = page.url
#             html = get_page(page_url)
#             if page_url and html:
#                 add_page_to_index(page_url, html)
#                 ToAnalyzePage.objects.get(url=page_url).delete()


def analyze(page_url, html):
    if page_url and html:
        add_page_to_index(page_url, html)
        #解析したページをToAnalyzePageモデルから削除
        ToAnalyzePage.objects.get(url=page_url).delete()