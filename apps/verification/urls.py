from django.urls import path
from . import views

app_name = 'verification'

urlpatterns = [
    path('', views.verification_list, name='verification_list'),
    path('user/<int:user_id>/', views.user_verification_detail, name='user_verification_detail'),
]