from django.urls import path
from .. import views

app_name = 'messaging'

urlpatterns = [
    # Gestion des conversations
    path('<int:pk>/update/', views.ConversationUpdateView.as_view(), name='conversation_update'),
    path('<int:pk>/delete/', views.ConversationDeleteView.as_view(), name='conversation_delete'),
    
    # Gestion des participants
    path('<int:conversation_id>/participants/add/', views.ParticipantAddView.as_view(), name='participant_add'),
    path('<int:conversation_id>/participants/<int:participant_id>/remove/', views.ParticipantRemoveView.as_view(), name='participant_remove'),
    path('<int:conversation_id>/participants/<int:participant_id>/update/', views.ParticipantUpdateView.as_view(), name='participant_update'),
]