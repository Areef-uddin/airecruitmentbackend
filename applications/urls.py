from django.urls import path
from applications.views import ApplyJobView, ApplicationListView, ApplicationDetailView, ApplicationStatusUpdateView

urlpatterns = [
    path('', ApplicationListView.as_view(), name='application-list'),
    path('<int:id>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('<int:id>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),
    path('apply/<int:job_id>/', ApplyJobView.as_view(), name='job-apply'),
]
