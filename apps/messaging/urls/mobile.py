from django.urls import path
from .. import views

app_name = 'messaging'

urlpatterns = [
    # Conversations
    path('', views.ConversationListView.as_view(), name='conversation_list'),
    path('<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('create/', views.ConversationCreateView.as_view(), name='conversation_create'),
    path('direct/<int:recipient_id>/', views.DirectMessageCreateView.as_view(), name='direct_message_create'),
    path('direct/', views.DirectMessageCreateView.as_view(), name='direct_message_create_no_recipient'),
    
    # Messages
    path('<int:conversation_id>/messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/mark-as-read/', views.mark_message_as_read, name='mark_message_as_read'),
    path('<int:pk>/mark-as-read/', views.mark_conversation_as_read, name='mark_conversation_as_read'),
    path('messages/<int:message_id>/react/', views.add_reaction, name='add_reaction'),
]