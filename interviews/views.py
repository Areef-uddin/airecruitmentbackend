import time
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from interviews.models import Interview, InterviewFeedback, InterviewStatus
from interviews.serializers import InterviewSerializer, InterviewFeedbackSerializer
from applications.models import JobApplication, ApplicationStatus
from notifications.models import Notification, NotificationType
from ai_services.services import AIService
from accounts.models import User
from jobs.models import Job

# In-memory room state for real-time WebRTC presence
ACTIVE_ROOMS = {}


class InterviewListCreateView(generics.ListCreateAPIView):
    serializer_class = InterviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.is_candidate:
            return Interview.objects.filter(application__candidate=user).select_related('application', 'application__job', 'application__job__company', 'interviewer')
        elif user.is_recruiter or user.is_super_admin:
            if user.is_super_admin:
                return Interview.objects.all().select_related('application', 'application__job', 'application__job__company', 'interviewer')
            return Interview.objects.filter(
                Q(interviewer=user) | Q(application__job__recruiter=user)
            ).distinct().select_related('application', 'application__job', 'application__job__company', 'interviewer')
        return Interview.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer.instance.refresh_from_db()
        output_serializer = self.get_serializer(serializer.instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        application_id = self.request.data.get('application_id')
        candidate_id = self.request.data.get('candidate_id') or self.request.data.get('candidate_user_id')
        job_id = self.request.data.get('job_id')

        if application_id:
            app = get_object_or_404(JobApplication, id=application_id)
        elif candidate_id:
            candidate_user = get_object_or_404(User, id=candidate_id)
            if job_id:
                job = get_object_or_404(Job, id=job_id)
            else:
                job = Job.objects.filter(recruiter=self.request.user).first() or Job.objects.first()
                if not job:
                    job = Job.objects.create(
                        recruiter=self.request.user,
                        title="Technical & Behavioral Evaluation",
                        description="Direct technical screening session.",
                        status="ACTIVE"
                    )
            app, _ = JobApplication.objects.get_or_create(
                job=job,
                candidate=candidate_user,
                defaults={'status': ApplicationStatus.INTERVIEW_SCHEDULED}
            )
        else:
            app = JobApplication.objects.first()
            if not app:
                raise ValueError("Valid application_id or candidate_id is required.")

        app.status = ApplicationStatus.INTERVIEW_SCHEDULED
        app.save(update_fields=['status'])

        scheduled_at = self.request.data.get('scheduled_at') or timezone.now()
        interview = serializer.save(
            application=app,
            interviewer=self.request.user,
            scheduled_at=scheduled_at
        )

        custom_room = self.request.data.get('room')
        meeting_link = self.request.data.get('meeting_link')
        if not meeting_link:
            room_name = custom_room if (custom_room and str(custom_room).strip()) else f"interview_{interview.id}"
            interview.meeting_link = f"/live-interview?room={room_name}&id={interview.id}"
        else:
            interview.meeting_link = meeting_link
        interview.save(update_fields=['meeting_link'])

        # Notify candidate
        Notification.objects.create(
            user=app.candidate,
            title="Interview Invitation Received!",
            message=f"You have been invited by {self.request.user.get_full_name() or self.request.user.email} to join an interview for {app.job.title}.",
            notification_type=NotificationType.INTERVIEW_INVITE,
            link=interview.meeting_link
        )


class InterviewDetailView(generics.RetrieveUpdateAPIView):
    queryset = Interview.objects.all().select_related('application', 'application__job', 'application__job__company', 'interviewer')
    serializer_class = InterviewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'


class InterviewFeedbackCreateView(generics.CreateAPIView):
    serializer_class = InterviewFeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        interview_id = self.kwargs.get('id')
        interview = get_object_or_404(Interview, id=interview_id)
        serializer.save(interview=interview, reviewer=self.request.user)


class InterviewAIEvaluateView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        interview = get_object_or_404(Interview, id=id)
        transcript = request.data.get('transcript', interview.ai_transcript)

        eval_result = AIService.evaluate_interview_session(
            job_title=interview.application.job.title,
            transcript=transcript
        )

        interview.ai_score = eval_result.get('score', 93.0)
        interview.ai_feedback = eval_result.get('feedback', '')
        interview.status = InterviewStatus.COMPLETED
        if transcript:
            interview.ai_transcript = transcript
        interview.save()

        return Response({
            'message': 'Interview evaluated successfully',
            'score': interview.ai_score,
            'feedback': interview.ai_feedback,
            'status': interview.status
        }, status=status.HTTP_200_OK)


ROOM_SIGNALS = {}


class InterviewRoomStatusView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        room = request.query_params.get('room', 'interview_demo').strip()
        interview_param_id = request.query_params.get('id')
        now = time.time()
        room_data = ACTIVE_ROOMS.get(room, {})
        active_participants = [
            p for uid, p in room_data.items()
            if now - p.get('last_seen', 0) < 45
        ]

        interview_info = None
        target_id = None
        if interview_param_id and str(interview_param_id).isdigit():
            target_id = int(interview_param_id)
        elif room.startswith('interview_'):
            try:
                target_id = int(room.replace('interview_', ''))
            except Exception:
                target_id = None

        interview = None
        if target_id:
            interview = Interview.objects.select_related(
                'application__candidate', 'application__job', 'interviewer'
            ).filter(id=target_id).first()

        if not interview and room:
            interview = Interview.objects.select_related(
                'application__candidate', 'application__job', 'interviewer'
            ).filter(meeting_link__icontains=room).first()

        if interview:
            interview_info = {
                'id': interview.id,
                'title': interview.title,
                'job_title': interview.application.job.title,
                'candidate_name': interview.application.candidate.get_full_name() or interview.application.candidate.email,
                'candidate_id': interview.application.candidate.id,
                'recruiter_name': interview.interviewer.get_full_name() if interview.interviewer else 'Recruiter',
                'recruiter_id': interview.interviewer.id if interview.interviewer else None,
                'status': interview.status,
                'meeting_link': interview.meeting_link,
            }

        return Response({
            'room': room,
            'participants': active_participants,
            'participant_count': len(active_participants),
            'interview': interview_info
        }, status=status.HTTP_200_OK)


class InterviewRoomJoinView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        room = request.data.get('room', 'interview_demo').strip()
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else request.data.get('user_id', 999)
        name = user.get_full_name() or user.email if user else request.data.get('name', 'Participant')
        role = user.role if (user and hasattr(user, 'role')) else request.data.get('role', 'CANDIDATE')

        if room not in ACTIVE_ROOMS:
            ACTIVE_ROOMS[room] = {}

        raw_video = request.data.get('video_on', True)
        if isinstance(raw_video, str):
            raw_video = raw_video.lower() in ('true', '1')

        raw_mic = request.data.get('mic_on', True)
        if isinstance(raw_mic, str):
            raw_mic = raw_mic.lower() in ('true', '1')

        ACTIVE_ROOMS[room][str(user_id)] = {
            'user_id': user_id,
            'name': name,
            'role': role,
            'joined_at': time.time(),
            'last_seen': time.time(),
            'video_on': bool(raw_video),
            'mic_on': bool(raw_mic),
        }

        return Response({
            'status': 'joined',
            'room': room,
            'participants': list(ACTIVE_ROOMS[room].values())
        }, status=status.HTTP_200_OK)


class InterviewRoomHeartbeatView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        room = request.data.get('room', 'interview_demo').strip()
        user_id = str(request.user.id) if request.user.is_authenticated else str(request.data.get('user_id', '999'))
        if room in ACTIVE_ROOMS and user_id in ACTIVE_ROOMS[room]:
            ACTIVE_ROOMS[room][user_id]['last_seen'] = time.time()
            if 'video_on' in request.data:
                v = request.data.get('video_on')
                if isinstance(v, str):
                    v = v.lower() in ('true', '1')
                ACTIVE_ROOMS[room][user_id]['video_on'] = bool(v)
            if 'mic_on' in request.data:
                m = request.data.get('mic_on')
                if isinstance(m, str):
                    m = m.lower() in ('true', '1')
                ACTIVE_ROOMS[room][user_id]['mic_on'] = bool(m)
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class InterviewRoomLeaveView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        room = request.data.get('room', 'interview_demo').strip()
        user_id = str(request.user.id) if request.user.is_authenticated else str(request.data.get('user_id', '999'))
        if room in ACTIVE_ROOMS and user_id in ACTIVE_ROOMS[room]:
            del ACTIVE_ROOMS[room][user_id]
        return Response({'status': 'left'}, status=status.HTTP_200_OK)


class InterviewSignalView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        room = request.query_params.get('room', '').strip()
        user_id = str(request.query_params.get('user_id', '')).strip()
        since_id = int(request.query_params.get('since', 0))

        signals = ROOM_SIGNALS.get(room, [])
        new_signals = [
            s for s in signals
            if str(s.get('from_user')) != user_id
            and (not s.get('to_user') or str(s.get('to_user')) in [user_id, 'all', ''])
            and s.get('id', 0) > since_id
        ]
        return Response({'signals': new_signals}, status=status.HTTP_200_OK)

    def post(self, request):
        room = request.data.get('room', '').strip()
        from_user = str(request.data.get('from_user', '')).strip()
        to_user = str(request.data.get('to_user', '')).strip()
        sig_type = request.data.get('type', '')
        payload = request.data.get('payload')

        if not room:
            return Response({'error': 'Room is required'}, status=status.HTTP_400_BAD_REQUEST)

        if room not in ROOM_SIGNALS:
            ROOM_SIGNALS[room] = []

        sig_id = len(ROOM_SIGNALS[room]) + 1
        signal_entry = {
            'id': sig_id,
            'from_user': from_user,
            'to_user': to_user,
            'type': sig_type,
            'payload': payload,
            'timestamp': time.time(),
        }
        ROOM_SIGNALS[room].append(signal_entry)

        if len(ROOM_SIGNALS[room]) > 200:
            ROOM_SIGNALS[room] = ROOM_SIGNALS[room][-200:]

        return Response({'status': 'sent', 'id': sig_id}, status=status.HTTP_200_OK)


class InterviewCleanupDummiesView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        action = 'clean' if 'clean' in request.path else (request.query_params.get('action') or request.GET.get('action', 'inspect'))
        interviews_all = list(Interview.objects.values('id', 'title', 'status', 'created_at'))
        users_all = list(User.objects.values('id', 'email', 'first_name', 'last_name', 'role'))

        if action == 'clean':
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM interviews_interviewfeedback")
                cursor.execute("DELETE FROM interviews_interview")
                cursor.execute("DELETE FROM applications_jobapplication")
                cursor.execute("DELETE FROM candidates_candidateskill")
                cursor.execute("DELETE FROM candidates_candidateprofile")
                cursor.execute("DELETE FROM accounts_user WHERE id IN (5, 6, 7) OR email LIKE '%bhai%' OR email LIKE '%dummy%'")
                row_counts = cursor.rowcount

            ACTIVE_ROOMS.clear()
            ROOM_SIGNALS.clear()

            return Response({
                'status': 'cleaned',
                'raw_affected': row_counts,
                'interviews_remaining': Interview.objects.count(),
                'users_remaining': list(User.objects.values('id', 'email', 'first_name', 'last_name', 'role')),
            })

        return Response({
            'interviews': interviews_all,
            'users': users_all,
        })

