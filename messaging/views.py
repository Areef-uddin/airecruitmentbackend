from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from messaging.models import Conversation, Message
from messaging.serializers import ConversationSerializer, MessageSerializer
from accounts.models import User


class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.conversations.all()

    def create(self, request, *args, **kwargs):
        recipient_id = request.data.get('recipient_id')
        subject = request.data.get('subject', 'Recruitment Conversation')
        initial_message = request.data.get('message', '')

        if not recipient_id:
            return Response({'error': 'recipient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        recipient = get_object_or_404(User, id=recipient_id)

        conv = Conversation.objects.create(subject=subject)
        conv.participants.add(request.user, recipient)

        if initial_message:
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                body=initial_message
            )

        return Response(ConversationSerializer(conv).data, status=status.HTTP_201_CREATED)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        conv_id = self.kwargs.get('conversation_id')
        conv = get_object_or_404(Conversation, id=conv_id, participants=self.request.user)
        # Mark incoming messages as read
        conv.messages.exclude(sender=self.request.user).update(is_read=True)
        return conv.messages.all()

    def perform_create(self, serializer):
        conv_id = self.kwargs.get('conversation_id')
        conv = get_object_or_404(Conversation, id=conv_id, participants=self.request.user)
        serializer.save(conversation=conv, sender=self.request.user)
        conv.save()  # touch updated_at
