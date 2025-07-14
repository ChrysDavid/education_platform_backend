from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q, Avg, Count, Prefetch
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.cache import cache

from ..models import (
    SchoolType, City, School, Department, Program,
    Facility, SchoolContact, SchoolReview, SchoolMedia, SchoolEvent
)
from ..forms import (
    SchoolSearchForm, SchoolReviewForm
)
from ..permissions import IsSchoolOwnerOrAdmin, CanReviewSchool


class SchoolListView(ListView):
    model = School
    template_name = 'schools/school_list.html'
    context_object_name = 'schools'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = School.objects.filter(is_active=True)
        
        form = SchoolSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            school_type = form.cleaned_data.get('school_type')
            city = form.cleaned_data.get('city')
            has_facilities = form.cleaned_data.get('has_facilities')
            min_rating = form.cleaned_data.get('min_rating')
            is_verified = form.cleaned_data.get('is_verified')
            
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(city__name__icontains=search) |
                    Q(school_type__name__icontains=search)
                )
            
            if school_type:
                queryset = queryset.filter(school_type=school_type)
            
            if city:
                queryset = queryset.filter(city=city)
            
            if has_facilities:
                for facility_type in has_facilities:
                    queryset = queryset.filter(facilities__facility_type=facility_type).distinct()
            
            if min_rating:
                school_ids_with_min_rating = SchoolReview.objects.filter(
                    is_public=True
                ).values('school').annotate(
                    avg_rating=Avg('rating')
                ).filter(
                    avg_rating__gte=float(min_rating)
                ).values_list('school', flat=True)
                queryset = queryset.filter(id__in=school_ids_with_min_rating)
            
            if is_verified:
                queryset = queryset.filter(is_verified=True)
        
        return queryset.select_related('school_type', 'city').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_public=True)),
            review_count=Count('reviews', filter=Q(reviews__is_public=True)))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SchoolSearchForm(self.request.GET)
        context['school_types'] = SchoolType.objects.all()
        context['cities'] = City.objects.filter(is_active=True)
        return context


class SchoolTypeListView(ListView):
    model = SchoolType
    template_name = 'schools/school_type_list.html'
    context_object_name = 'school_types'
    
    def get_queryset(self):
        return SchoolType.objects.annotate(
            school_count=Count('schools', filter=Q(schools__is_active=True))
        ).order_by('name')


class CityListView(ListView):
    model = City
    template_name = 'schools/city_list.html'
    context_object_name = 'cities'
    
    def get_queryset(self):
        return City.objects.filter(is_active=True).annotate(
            school_count=Count('schools', filter=Q(schools__is_active=True))
        ).order_by('name')


class SchoolDetailView(DetailView):
    model = School
    template_name = 'schools/school_detail.html'
    context_object_name = 'school'
    
    def get_queryset(self):
        return School.objects.filter(is_active=True).select_related(
            'school_type', 'city'
        ).prefetch_related(
            'departments', 'programs', 'facilities', 'contacts', 
            Prefetch('reviews', queryset=SchoolReview.objects.filter(is_public=True).select_related('user')),
            Prefetch('media', queryset=SchoolMedia.objects.filter(is_public=True)),
            Prefetch('events', queryset=SchoolEvent.objects.filter(is_public=True))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        school = self.object
        cache_key = f'school_rating_{school.id}'
        avg_rating = cache.get(cache_key)
        
        if avg_rating is None:
            avg_rating = school.reviews.filter(is_public=True).aggregate(
                Avg('rating')
            )['rating__avg']
            cache.set(cache_key, avg_rating, 86400)
        
        context['avg_rating'] = avg_rating
        
        review_count_key = f'school_review_count_{school.id}'
        review_count = cache.get(review_count_key)
        
        if review_count is None:
            review_count = school.reviews.filter(is_public=True).count()
            cache.set(review_count_key, review_count, 86400)
        
        context['review_count'] = review_count
        
        if self.request.user.is_authenticated:
            existing_review = SchoolReview.objects.filter(
                user=self.request.user, school=school
            ).first()
            
            if existing_review:
                context['user_review'] = existing_review
                context['review_form'] = SchoolReviewForm(
                    instance=existing_review, 
                    user=self.request.user, 
                    school=school
                )
            else:
                context['review_form'] = SchoolReviewForm(
                    user=self.request.user, 
                    school=school
                )
        
        context['upcoming_events'] = school.events.filter(
            is_public=True
        ).exclude(
            is_past=True
        ).order_by('start_date')[:5]
        
        return context


class DepartmentListView(ListView):
    model = Department
    template_name = 'schools/department_list.html'
    context_object_name = 'departments'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return Department.objects.filter(
            school=self.school, is_active=True
        ).annotate(
            program_count=Count('programs')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class DepartmentDetailView(DetailView):
    model = Department
    template_name = 'schools/department_detail.html'
    context_object_name = 'department'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['school_slug'], is_active=True)
        return Department.objects.filter(
            school=self.school, slug=self.kwargs['slug'], is_active=True
        ).select_related('school').prefetch_related('programs')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        context['programs'] = Program.objects.filter(
            department=self.object, is_active=True
        )
        return context


class ProgramListView(ListView):
    model = Program
    template_name = 'schools/program_list.html'
    context_object_name = 'programs'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return Program.objects.filter(
            school=self.school, is_active=True
        ).select_related('department')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class ProgramDetailView(DetailView):
    model = Program
    template_name = 'schools/program_detail.html'
    context_object_name = 'program'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['school_slug'], is_active=True)
        return Program.objects.filter(
            school=self.school, slug=self.kwargs['slug'], is_active=True
        ).select_related('school', 'department')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class FacilityListView(ListView):
    model = Facility
    template_name = 'schools/facility_list.html'
    context_object_name = 'facilities'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return Facility.objects.filter(
            school=self.school, is_active=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolContactListView(ListView):
    model = SchoolContact
    template_name = 'schools/contact_list.html'
    context_object_name = 'contacts'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return SchoolContact.objects.filter(
            school=self.school, is_active=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolMediaListView(ListView):
    model = SchoolMedia
    template_name = 'schools/media_list.html'
    context_object_name = 'media_items'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return SchoolMedia.objects.filter(
            school=self.school, is_public=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolEventListView(ListView):
    model = SchoolEvent
    template_name = 'schools/event_list.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return SchoolEvent.objects.filter(
            school=self.school, is_public=True
        ).order_by('start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        context['upcoming_events'] = self.get_queryset().exclude(is_past=True)
        context['past_events'] = self.get_queryset().filter(is_past=True)
        return context


class SchoolEventDetailView(DetailView):
    model = SchoolEvent
    template_name = 'schools/event_detail.html'
    context_object_name = 'event'
    pk_url_kwarg = 'pk'
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['school_slug'], is_active=True)
        return SchoolEvent.objects.filter(
            school=self.school, is_public=True
        ).select_related('school')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolReviewListView(ListView):
    model = SchoolReview
    template_name = 'schools/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        return SchoolReview.objects.filter(
            school=self.school, is_public=True
        ).select_related('user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        
        cache_key = f'school_rating_{self.school.id}'
        avg_rating = cache.get(cache_key)
        
        if avg_rating is None:
            avg_rating = self.school.reviews.filter(is_public=True).aggregate(
                Avg('rating')
            )['rating__avg']
            cache.set(cache_key, avg_rating, 86400)
        
        context['avg_rating'] = avg_rating
        
        if self.request.user.is_authenticated:
            existing_review = SchoolReview.objects.filter(
                user=self.request.user, school=self.school
            ).first()
            
            if existing_review:
                context['user_review'] = existing_review
                context['review_form'] = SchoolReviewForm(
                    instance=existing_review,
                    user=self.request.user,
                    school=self.school
                )
            else:
                context['review_form'] = SchoolReviewForm(
                    user=self.request.user,
                    school=self.school
                )
        
        return context


class SchoolReviewCreateView(LoginRequiredMixin, CreateView):
    model = SchoolReview
    form_class = SchoolReviewForm
    template_name = 'schools/review_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        
        existing_review = SchoolReview.objects.filter(
            user=request.user, school=self.school
        ).first()
        
        if existing_review:
            messages.warning(request, _("Vous avez déjà évalué cet établissement. Vous pouvez modifier votre évaluation existante."))
            return redirect('schools:edit_review', slug=self.school.slug, pk=existing_review.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['school'] = self.school
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.school = self.school
        form.instance.is_public = True
        messages.success(self.request, _("Votre avis a été ajouté avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('schools:school_detail', kwargs={'slug': self.school.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = SchoolReview
    form_class = SchoolReviewForm
    template_name = 'schools/review_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        review = self.get_object()
        
        if review.user != request.user and not request.user.is_staff:
            messages.error(request, _("Vous n'êtes pas autorisé à modifier cet avis."))
            return redirect('schools:school_detail', slug=self.school.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['school'] = self.school
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre avis a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('schools:school_detail', kwargs={'slug': self.school.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        context['is_update'] = True
        return context


class SchoolReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = SchoolReview
    template_name = 'schools/review_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.school = get_object_or_404(School, slug=self.kwargs['slug'], is_active=True)
        review = self.get_object()
        
        if review.user != request.user and not request.user.is_staff:
            messages.error(request, _("Vous n'êtes pas autorisé à supprimer cet avis."))
            return redirect('schools:school_detail', slug=self.school.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        messages.success(self.request, _("Votre avis a été supprimé avec succès."))
        return reverse('schools:school_detail', kwargs={'slug': self.school.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolSearchView(FormView):
    form_class = SchoolSearchForm
    template_name = 'schools/school_search.html'
    
    def form_valid(self, form):
        params = {}
        for key, value in form.cleaned_data.items():
            if value:
                if isinstance(value, list):
                    params[key] = ','.join(str(v) for v in value)
                else:
                    params[key] = value
        
        url = reverse('schools:school_list')
        if params:
            url += '?' + '&'.join([f"{key}={value}" for key, value in params.items()])
        
        return redirect(url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school_types'] = SchoolType.objects.all()
        context['cities'] = City.objects.filter(is_active=True)
        return context


class SchoolFilterByTypeView(ListView):
    model = School
    template_name = 'schools/school_list.html'
    context_object_name = 'schools'
    paginate_by = 12
    
    def get_queryset(self):
        self.school_type = get_object_or_404(SchoolType, slug=self.kwargs['type_slug'])
        return School.objects.filter(
            school_type=self.school_type, is_active=True
        ).select_related('school_type', 'city').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_public=True)),
            review_count=Count('reviews', filter=Q(reviews__is_public=True))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school_type'] = self.school_type
        context['filter_title'] = _("Établissements de type : %(type)s") % {'type': self.school_type.name}
        context['school_types'] = SchoolType.objects.all()
        context['cities'] = City.objects.filter(is_active=True)
        return context


class SchoolFilterByCityView(ListView):
    model = School
    template_name = 'schools/school_list.html'
    context_object_name = 'schools'
    paginate_by = 12
    
    def get_queryset(self):
        self.city = get_object_or_404(City, pk=self.kwargs['city_id'], is_active=True)
        return School.objects.filter(
            city=self.city, is_active=True
        ).select_related('school_type', 'city').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_public=True)),
            review_count=Count('reviews', filter=Q(reviews__is_public=True))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['city'] = self.city
        context['filter_title'] = _("Établissements à %(city)s") % {'city': self.city.name}
        context['school_types'] = SchoolType.objects.all()
        context['cities'] = City.objects.filter(is_active=True)
        return context