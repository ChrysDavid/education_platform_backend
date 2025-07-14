from django.urls import path
from .. import views

app_name = 'orientation'

urlpatterns = [
    # Évaluations
    path('assessments/', views.AssessmentListView.as_view(), name='assessment_list'),
    path('assessments/<int:pk>/', views.AssessmentDetailView.as_view(), name='assessment_detail'),
    path('assessments/<int:pk>/take/', views.TakeAssessmentView.as_view(), name='take_assessment'),
]