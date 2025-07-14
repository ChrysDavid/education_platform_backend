from django.urls import path
from apps.resources.views.web import (
    ResourceCategoryListView,
    ResourceCategoryDetailView,
    ResourceCollectionListView,
    ResourceCollectionDetailView,
    ResourceCollectionCreateView,
    ResourceCollectionUpdateView,
    ResourceCollectionDeleteView,
    ResourceListView
)

app_name = 'resources'

urlpatterns = [
    # URLs pour les catégories de ressources
    path('categories/', ResourceCategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', ResourceCategoryDetailView.as_view(), name='category_detail'),
    
    # URLs pour les ressources
    path('', ResourceListView.as_view(), name='resource_list'),
    
    # URLs pour les collections de ressources
    path('collections/', ResourceCollectionListView.as_view(), name='collection_list'),
    path('collections/<slug:slug>/', ResourceCollectionDetailView.as_view(), name='collection_detail'),
    path('collections/create/', ResourceCollectionCreateView.as_view(), name='collection_create'),
    path('collections/<slug:slug>/update/', ResourceCollectionUpdateView.as_view(), name='collection_update'),
    path('collections/<slug:slug>/delete/', ResourceCollectionDeleteView.as_view(), name='collection_delete'),
]