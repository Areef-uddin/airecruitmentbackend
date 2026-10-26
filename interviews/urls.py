from django.urls import path
from interviews.views import (
    InterviewListCreateView,
    InterviewDetailView,
    InterviewFeedbackCreateView,
    InterviewAIEvaluateView,
    InterviewRoomStatusView,
    InterviewRoomJoinView,
    InterviewRoomHeartbeatView,
    InterviewRoomLeaveView,
    InterviewSignalView,
    InterviewRoomChatView,
    InterviewCleanupDummiesView,
)

urlpatterns = [
    path('', InterviewListCreateView.as_view(), name='interview-list-create'),
    path('cleanup-dummies/', InterviewCleanupDummiesView.as_view(), name='interview-cleanup-dummies'),
    path('cleanup-dummies/clean/', InterviewCleanupDummiesView.as_view(), name='interview-cleanup-dummies-clean'),
    path('<int:id>/', InterviewDetailView.as_view(), name='interview-detail'),
    path('<int:id>/feedback/', InterviewFeedbackCreateView.as_view(), name='interview-feedback'),
    path('<int:id>/ai-evaluate/', InterviewAIEvaluateView.as_view(), name='interview-ai-evaluate'),
    path('room-status/', InterviewRoomStatusView.as_view(), name='interview-room-status'),
    path('room-join/', InterviewRoomJoinView.as_view(), name='interview-room-join'),
    path('room-heartbeat/', InterviewRoomHeartbeatView.as_view(), name='interview-room-heartbeat'),
    path('room-leave/', InterviewRoomLeaveView.as_view(), name='interview-room-leave'),
    path('room-chat/', InterviewRoomChatView.as_view(), name='interview-room-chat'),
    path('signal/', InterviewSignalView.as_view(), name='interview-signal'),
]
