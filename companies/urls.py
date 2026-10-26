from django.urls import path
from companies.views import CompanyListView, CompanyDetailView

urlpatterns = [
    path('', CompanyListView.as_view(), name='company-list'),
    path('<int:id>/', CompanyDetailView.as_view(), name='company-detail'),
]
