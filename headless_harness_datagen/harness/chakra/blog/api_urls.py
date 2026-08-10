from django.urls import path
from .api_views import PostListCreateView, PostDetailView, CategoryListCreateView, CategoryDetailView, CommentListCreateView

app_name = 'blog_api'

urlpatterns = [
    path('posts/', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
]