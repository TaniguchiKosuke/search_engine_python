from bs4.element import ContentMetaAttributeValue
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from .models import Article, Index
from .crawler import crawler
import json


class SearchView(ListView):
    """
    検索画面のためのView
    """
    template_name = 'search.html'
    queryset = Index

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('query')
        if query:
            index_qs = Index.objects.filter(keyword__icontains=query)
            if index_qs:
                article_list = list()
                for index in index_qs:
                    index_json = index.index_json
                    index_dict = json.loads(index_json)
                    print('=============================================')
                    print(index_dict)
                    if index_dict['url']:
                        urls = index_dict['url']
                        articles = list()
                        for url in urls:
                            article = Article.objects.filter(url=url).first()
                            articles.append(article)
                        article_list.extend(articles)
                context['object_list'] = article_list
                context['len_articles'] = len(article_list)
                context['query'] = query
            else:
                context['object_list'] = None
                context['query'] = query
        else:
            context['object_list'] = Index.objects.all()[:50]
        return context


class CrawlerSettingsHomeView(TemplateView):
    """
    管理者がクローラーの設定をするためのView
    """
    template_name = 'crawler_settings_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CrawlerSettingsView(TemplateView):
    template_name = 'crawler_settings.html'


def start_crawling(request):
    # seed = 'https://news.yahoo.co.jp/'
    # seed = 'https://ja.wikipedia.org/wiki/%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8'
    # seed = 'https://www.bbc.com/'
    seed = 'https://medium.com/'
    crawler(seed, 2, stop_flag=False)
    return redirect('search_engine:crawler_settings')


def stop_crawling(request):
    crawler(None, None, stop_flag=True)
    return redirect('search_engine:crawler_settings')