from django.urls import path
from resumes.views import ResumeListCreateView, ResumeDetailView

urlpatterns = [
    path('', ResumeListCreateView.as_view(), name='resume-list-create'),
    path('<int:id>/', ResumeDetailView.as_view(), name='resume-detail'),
]
