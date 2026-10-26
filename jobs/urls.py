from django.urls import path
from jobs.views import JobListView, JobDetailView, SavedJobToggleView, SavedJobListView

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),
    path('saved/', SavedJobListView.as_view(), name='job-saved-list'),
    path('<int:id>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:id>/save/', SavedJobToggleView.as_view(), name='job-save-toggle'),
]
