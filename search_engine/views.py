from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from .models import Index
from .crawler import crawler


class SearchView(ListView):
    template_name = 'search.html'
    queryset = Index

    def get_queryset(self):
        seed = 'https://www.yahoo.co.jp/'
        crawler(seed, 2)
        query = self.request.GET.get('query')
        if query:
            queryset = Index.objects.filter(keyword=query)[:10]
        else:
            queryset = Index.objects.all()[:50]
        return queryset