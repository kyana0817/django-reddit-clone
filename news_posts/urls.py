from django.urls import path
from . import views

app_name = 'news_posts'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('create-post/', views.CreatePostView.as_view(), name='create_post'),
    path('delete/<int:pk>/', views.DeletePostView.as_view(), name="delete_post")
]