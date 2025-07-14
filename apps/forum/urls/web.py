from django.urls import path
from .. import views

app_name = 'forum'

urlpatterns = [
    # Mise à jour des sujets
    path('category/<slug:category_slug>/<slug:topic_slug>/update/', views.TopicUpdateView.as_view(), name='topic_update'),
    
    # Modération
    path('category/<slug:category_slug>/<slug:topic_slug>/moderate/', views.moderate_topic, name='moderate_topic'),
    path('posts/<int:post_id>/moderate/', views.moderate_post, name='moderate_post'),
    
    # Mise à jour des messages
    path('posts/<int:post_id>/update/', views.PostUpdateView.as_view(), name='post_update'),
]