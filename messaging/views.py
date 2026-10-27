from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from messaging.models import Conversation, Message
from messaging.serializers import ConversationSerializer, MessageSerializer
from accounts.models import User, UserRole
from candidates.models import CandidateProfile
from ai_services.services import AIService


class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.conversations.all().order_by('-updated_at')

    def create(self, request, *args, **kwargs):
        recipient_id = request.data.get('recipient_id')
        subject = request.data.get('subject', 'Direct Message')
        initial_message = request.data.get('message', '').strip()

        if not recipient_id:
            return Response({'error': 'recipient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        recipient = get_object_or_404(User, id=recipient_id)

        # Check if conversation already exists between these two users
        existing_conv = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()

        if existing_conv:
            if initial_message:
                Message.objects.create(
                    conversation=existing_conv,
                    sender=request.user,
                    body=initial_message
                )
                existing_conv.save()
            return Response(ConversationSerializer(existing_conv).data, status=status.HTTP_200_OK)

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
        return conv.messages.all().order_by('created_at')

    def perform_create(self, serializer):
        conv_id = self.kwargs.get('conversation_id')
        conv = get_object_or_404(Conversation, id=conv_id, participants=self.request.user)
        serializer.save(conversation=conv, sender=self.request.user)
        conv.save()  # touch updated_at


class ChatContactsView(generics.GenericAPIView):
    """
    Returns available contacts for 1-on-1 direct chatting.
    - If Recruiter / Admin: Returns candidates (including applicant candidates and registered candidates).
    - If Candidate: Returns recruiters and company talent partners.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        contacts = []

        if user.is_recruiter or user.is_super_admin:
            # Recruiter looking for candidates
            candidate_users = User.objects.filter(role=UserRole.CANDIDATE).exclude(id=user.id).order_by('-created_at')
            for c_user in candidate_users:
                # Find if existing conversation exists
                conv = Conversation.objects.filter(participants=user).filter(participants=c_user).first()
                last_msg = None
                unread_count = 0
                if conv:
                    last_obj = conv.messages.order_by('-created_at').first()
                    if last_obj:
                        last_msg = {
                            'body': last_obj.body,
                            'created_at': last_obj.created_at.isoformat(),
                            'is_me': last_obj.sender_id == user.id,
                        }
                    unread_count = conv.messages.filter(sender=c_user, is_read=False).count()

                headline = 'Candidate'
                if hasattr(c_user, 'candidate_profile'):
                    headline = c_user.candidate_profile.headline or 'Software Engineer'

                contacts.append({
                    'id': c_user.id,
                    'name': c_user.get_full_name() or c_user.username or c_user.email,
                    'email': c_user.email,
                    'role': 'CANDIDATE',
                    'headline': headline,
                    'conversation_id': conv.id if conv else None,
                    'last_message': last_msg,
                    'unread_count': unread_count,
                })
        else:
            # Candidate looking for recruiters / company contacts
            recruiter_users = User.objects.filter(role__in=[UserRole.RECRUITER, UserRole.SUPER_ADMIN]).exclude(id=user.id)
            for r_user in recruiter_users:
                conv = Conversation.objects.filter(participants=user).filter(participants=r_user).first()
                last_msg = None
                unread_count = 0
                if conv:
                    last_obj = conv.messages.order_by('-created_at').first()
                    if last_obj:
                        last_msg = {
                            'body': last_obj.body,
                            'created_at': last_obj.created_at.isoformat(),
                            'is_me': last_obj.sender_id == user.id,
                        }
                    unread_count = conv.messages.filter(sender=r_user, is_read=False).count()

                headline = 'Talent Recruiter'
                if hasattr(r_user, 'recruiter_profile') and r_user.recruiter_profile.company:
                    headline = f"{r_user.recruiter_profile.title} @ {r_user.recruiter_profile.company.name}"

                contacts.append({
                    'id': r_user.id,
                    'name': r_user.get_full_name() or r_user.username or r_user.email,
                    'email': r_user.email,
                    'role': r_user.role,
                    'headline': headline,
                    'conversation_id': conv.id if conv else None,
                    'last_message': last_msg,
                    'unread_count': unread_count,
                })

        return Response({'contacts': contacts, 'count': len(contacts)}, status=status.HTTP_200_OK)


class ChatAISuggestionsView(generics.GenericAPIView):
    """
    AI message auto-suggestions powered by Google Gemini for 1-on-1 chatting.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        last_message = request.data.get('last_message', '').strip()
        context_text = request.data.get('context', '').strip()
        role = getattr(request.user, 'role', 'RECRUITER')

        system_prompt = (
            f"You are an AI assistant in a professional recruitment chat platform. "
            f"The user speaking is a {role}. "
            f"Generate 3-4 natural, polite, and professional quick-reply suggestions for them. "
            f"Return JSON strictly in the format: {{\"suggestions\": [\"reply 1\", \"reply 2\", \"reply 3\"]}}"
        )
        user_prompt = f"Last message in chat: \"{last_message}\"\nContext: {context_text}"

        llm_resp = AIService._call_llm(system_prompt, user_prompt, temperature=0.3)
        suggestions = []

        if llm_resp:
            try:
                import json
                clean_json = llm_resp.replace('```json', '').replace('```', '').strip()
                parsed = json.loads(clean_json)
                suggestions = parsed.get('suggestions', [])
            except Exception:
                pass

        if not suggestions:
            # Fallback high quality smart replies
            if role == 'RECRUITER':
                suggestions = [
                    "Hello! Thank you for applying. We are impressed with your profile.",
                    "Would you be available for a 30-minute technical interview this week?",
                    "Could you please share your updated resume and preferred timing?",
                    "Looking forward to our upcoming interview session!"
                ]
            else:
                suggestions = [
                    "Thank you for reaching out! Yes, I am available this week.",
                    "I would love to learn more about the role and team.",
                    "I am available for an interview. Please let me know what time works best.",
                    "Sounds great! Looking forward to connecting."
                ]

        return Response({'suggestions': suggestions[:4]}, status=status.HTTP_200_OK)
