from django.urls import path
from apps.resources.views.mobile import (
    ResourceCategoryAPIListView, ResourceAPIListView,
    ResourceAPIDetailView, ResourceReviewAPIListCreateView
)

app_name = 'resources_api'

urlpatterns = [
    # API
    path('categories/', ResourceCategoryAPIListView.as_view(), name='api_category_list'),
    path('resources/', ResourceAPIListView.as_view(), name='api_resource_list'),
    path('resources/<slug:slug>/', ResourceAPIDetailView.as_view(), name='api_resource_detail'),
    path('resources/<slug:slug>/reviews/', ResourceReviewAPIListCreateView.as_view(), name='api_resource_reviews'),
]