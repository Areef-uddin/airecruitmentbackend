from django.urls import path
from candidates.views import CandidateMeView, SkillListView, CandidateSkillManageView, CandidateRecommendedJobsView

urlpatterns = [
    path('me/', CandidateMeView.as_view(), name='candidate-me'),
    path('skills/', SkillListView.as_view(), name='skill-list'),
    path('skills/manage/', CandidateSkillManageView.as_view(), name='candidate-skill-create'),
    path('skills/manage/<int:pk>/', CandidateSkillManageView.as_view(), name='candidate-skill-delete'),
    path('recommended-jobs/', CandidateRecommendedJobsView.as_view(), name='candidate-recommended-jobs'),
]
