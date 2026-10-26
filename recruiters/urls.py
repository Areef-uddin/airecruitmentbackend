from django.urls import path
from recruiters.views import RecruiterDashboardView, RecruiterMeView, RecruiterCandidateSearchView

urlpatterns = [
    path('me/', RecruiterMeView.as_view(), name='recruiter-me'),
    path('dashboard/', RecruiterDashboardView.as_view(), name='recruiter-dashboard'),
    path('candidates/', RecruiterCandidateSearchView.as_view(), name='recruiter-candidates-search'),
]
