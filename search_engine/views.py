from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from .models import Index
from .crawler import crawler


class SearchView(ListView):
    """
    検索画面のためのView
    """
    template_name = 'search.html'
    queryset = Index

    def get_queryset(self):
        # seed = 'https://www.yahoo.co.jp/'
        seed = 'https://news.yahoo.co.jp/'
        # crawler(seed, 2)
        query = self.request.GET.get('query')
        if query:
            queryset = Index.objects.filter(keyword=query)[:10]
        else:
            queryset = Index.objects.all()[:50]
        return queryset


class CrawlerSettingsView(TemplateView):
    """
    管理者がクローラーの設定をするためのView
    """
    template_name = 'crawler_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context