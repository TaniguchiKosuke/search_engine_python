from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from .models import Index
from .crawler import crawler
import json


class SearchView(ListView):
    """
    検索画面のためのView
    """
    template_name = 'search.html'
    queryset = Index

    def get_queryset(self):
        query = self.request.GET.get('query')
        if query:
            index = Index.objects.filter(keyword=query).first()
            if index:
                index_json = index.index_json
                index_dict = json.loads(index_json)
                print('=============================================')
                print(index_dict)
                if index_dict['url']:
                    queryset = list()
                    urls = index_dict['url']
                    for url in urls:
                        queryset.append(url)
                    return queryset
            else:
                queryset = None
        else:
            queryset = Index.objects.all()[:50]
        return queryset


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
    seed = 'https://news.yahoo.co.jp/'
    crawler(seed, 2, stop_flag=False)
    return redirect('search_engine:crawler_settings')


def stop_crawling(request):
    crawler(None, None, stop_flag=True)
    return redirect('search_engine:crawler_settings')