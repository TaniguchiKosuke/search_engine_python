from django.shortcuts import render
from django.views.generic.list import ListView
from search_engine.models import Article


class SearchView(ListView):
    template_name = 'search.html'
    queryset = Article