from django.urls import path
from messaging.views import (
    ConversationListCreateView,
    MessageListCreateView,
    ChatContactsView,
    ChatAISuggestionsView,
)

urlpatterns = [
    path('conversations/', ConversationListCreateView.as_view(), name='conversation-list-create'),
    path('conversations/<int:conversation_id>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('contacts/', ChatContactsView.as_view(), name='chat-contacts'),
    path('ai-suggestions/', ChatAISuggestionsView.as_view(), name='chat-ai-suggestions'),
]
