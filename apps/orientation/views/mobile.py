from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
import django.db.models as models

from ..models import (
    AssessmentType, AssessmentQuestion, Assessment, AssessmentAnswer,
    SkillCategory, Skill, CareerField, CareerPath, OrientationPath,
    OrientationCareerPath, StudentSkill
)
from ..forms import (
    AssessmentTypeForm, AssessmentQuestionForm, AssessmentForm, AssessmentAnswerForm,
    SkillCategoryForm, SkillForm, CareerFieldForm, CareerPathForm, OrientationPathForm,
    OrientationCareerPathForm, StudentSkillForm, TakeAssessmentForm
)


class IsStudentMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est un étudiant.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.type == 'student'
    
    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être étudiant pour accéder à cette page."))
        return redirect('home')


class AssessmentListView(LoginRequiredMixin, ListView):
    """
    Liste des évaluations.
    """
    model = Assessment
    template_name = 'orientation/assessment_list.html'
    context_object_name = 'assessments'
    
    def get_queryset(self):
        queryset = Assessment.objects.select_related('student', 'advisor', 'assessment_type')
        
        # Filtrer selon le type d'utilisateur
        if self.request.user.type == 'student':
            # Un étudiant ne voit que ses propres évaluations
            return queryset.filter(student=self.request.user)
        
        elif self.request.user.type == 'advisor':
            # Un conseiller voit les évaluations qu'il a créées ou qui lui sont assignées
            return queryset.filter(models.Q(advisor=self.request.user) | models.Q(created_by=self.request.user))
        
        # Les administrateurs voient tout
        return queryset


class AssessmentDetailView(LoginRequiredMixin, DetailView):
    """
    Détails d'une évaluation.
    """
    model = Assessment
    template_name = 'orientation/assessment_detail.html'
    context_object_name = 'assessment'
    
    def get_queryset(self):
        queryset = Assessment.objects.select_related('student', 'advisor', 'assessment_type')
        
        # Filtrer selon le type d'utilisateur
        if self.request.user.type == 'student':
            # Un étudiant ne voit que ses propres évaluations
            return queryset.filter(student=self.request.user)
        
        elif self.request.user.type == 'advisor':
            # Un conseiller voit les évaluations qu'il a créées ou qui lui sont assignées
            return queryset.filter(models.Q(advisor=self.request.user) | models.Q(created_by=self.request.user))
        
        # Les administrateurs voient tout
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les réponses à l'évaluation
        context['answers'] = AssessmentAnswer.objects.filter(
            assessment=self.object
        ).select_related('question')
        
        return context


class TakeAssessmentView(LoginRequiredMixin, IsStudentMixin, FormView):
    """
    Vue pour répondre à une évaluation.
    """
    template_name = 'orientation/take_assessment.html'
    form_class = TakeAssessmentForm
    
    def dispatch(self, request, *args, **kwargs):
        # Récupérer l'évaluation
        self.assessment = get_object_or_404(
            Assessment,
            pk=self.kwargs['pk'],
            student=self.request.user
        )
        
        # Vérifier si l'évaluation peut être prise
        if self.assessment.status == 'completed':
            messages.error(request, _("Cette évaluation a déjà été complétée."))
            return redirect('orientation:assessment_detail', pk=self.assessment.pk)
        
        # Marquer comme en cours si nécessaire
        if self.assessment.status == 'pending':
            self.assessment.start()
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['assessment'] = self.assessment
        return kwargs
    
    def form_valid(self, form):
        # Enregistrer les réponses
        form.save()
        
        messages.success(self.request, _("Merci d'avoir complété cette évaluation."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orientation:assessment_detail', kwargs={'pk': self.assessment.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assessment'] = self.assessment
        
        # Ajouter le temps restant si applicable
        if self.assessment.assessment_type.time_limit_minutes and self.assessment.start_time:
            time_limit_seconds = self.assessment.assessment_type.time_limit_minutes * 60
            elapsed_seconds = (timezone.now() - self.assessment.start_time).total_seconds()
            remaining_seconds = max(0, time_limit_seconds - elapsed_seconds)
            
            context['remaining_seconds'] = remaining_seconds
        
        return context