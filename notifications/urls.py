from django.urls import path
from notifications.views import NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
]
