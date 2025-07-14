from django.urls import path
from ..views.mobile import (
    SchoolAPIListView, SchoolAPIDetailView,
    SchoolReviewAPIListView, CityAPIListView,
    SchoolTypeAPIListView
)

app_name = 'schools_api'

urlpatterns = [
    # Routes API
    path('api/schools/', SchoolAPIListView.as_view(), name='api_school_list'),
    path('api/schools/<int:pk>/', SchoolAPIDetailView.as_view(), name='api_school_detail'),
    path('api/schools/<int:pk>/reviews/', SchoolReviewAPIListView.as_view(), name='api_review_list'),
    path('api/cities/', CityAPIListView.as_view(), name='api_city_list'),
    path('api/types/', SchoolTypeAPIListView.as_view(), name='api_type_list'),
]