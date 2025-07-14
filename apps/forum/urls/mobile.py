from django.urls import path
from .. import views

app_name = 'forum'

urlpatterns = [
    # Page d'accueil
    path('', views.ForumHomepageView.as_view(), name='index'),
    
    # Catégories
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Sujets
    path('category/<slug:category_slug>/<slug:topic_slug>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('category/<slug:category_slug>/create/', views.TopicCreateView.as_view(), name='topic_create'),
    
    # Messages
    path('category/<slug:category_slug>/<slug:topic_slug>/posts/create/', views.PostCreateView.as_view(), name='post_create'),
    
    # Actions utilisateur
    path('category/<slug:category_slug>/<slug:topic_slug>/subscribe/', views.subscribe_topic, name='subscribe_topic'),
    path('posts/<int:post_id>/react/', views.react_to_post, name='react_to_post'),
    path('posts/<int:post_id>/report/', views.report_post, name='report_post'),
]