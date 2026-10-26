from django.urls import path
from analytics.views import AdminDashboardView, AdminUserManagementView

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('users/', AdminUserManagementView.as_view(), name='admin-users-list'),
    path('users/<int:pk>/', AdminUserManagementView.as_view(), name='admin-user-toggle'),
]
