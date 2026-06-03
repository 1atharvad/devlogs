from django.urls import path

from .views import ChatView, SearchView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="blog-rag-chat"),
    path("search/", SearchView.as_view(), name="blog-rag-search"),
]
