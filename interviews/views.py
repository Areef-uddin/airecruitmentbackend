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
            role_slug = ""
            if app and app.job and app.job.title:
                role_slug = "".join(c if c.isalnum() else "_" for c in app.job.title).strip("_")
            role_prefix = f"{role_slug}_Interview" if role_slug else "Interview"
            room_name = custom_room if (custom_room and str(custom_room).strip()) else f"{role_prefix}_{interview.id}"
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


import json
from django.db import connection

_TABLES_INITIALIZED = False

def _init_signaling_db():
    global _TABLES_INITIALIZED
    if _TABLES_INITIALIZED:
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_participants_live (
                    room VARCHAR(120) NOT NULL,
                    user_id VARCHAR(60) NOT NULL,
                    name VARCHAR(150) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    video_on BOOLEAN DEFAULT TRUE,
                    mic_on BOOLEAN DEFAULT TRUE,
                    last_seen DOUBLE PRECISION NOT NULL,
                    PRIMARY KEY (room, user_id)
                );
                CREATE TABLE IF NOT EXISTS room_signals_live (
                    id BIGSERIAL PRIMARY KEY,
                    room VARCHAR(120) NOT NULL,
                    from_user VARCHAR(60) NOT NULL,
                    to_user VARCHAR(60) DEFAULT '',
                    sig_type VARCHAR(50) DEFAULT 'webrtc',
                    payload TEXT NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_room_signals_live_rid ON room_signals_live (room, id);
            """)
        _TABLES_INITIALIZED = True
    except Exception:
        pass

ROOM_SIGNALS = {}


class InterviewRoomStatusView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        _init_signaling_db()
        room = request.query_params.get('room', 'interview_demo').strip()
        interview_param_id = request.query_params.get('id')
        now = time.time()
        active_participants = []

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, name, role, video_on, mic_on, last_seen
                    FROM room_participants_live
                    WHERE room = %s AND last_seen > %s
                    ORDER BY last_seen DESC
                """, [room, now - 35])
                for row in cursor.fetchall():
                    active_participants.append({
                        'user_id': row[0],
                        'name': row[1],
                        'role': row[2],
                        'video_on': row[3],
                        'mic_on': row[4],
                        'last_seen': row[5],
                    })
        except Exception:
            room_data = ACTIVE_ROOMS.get(room, {})
            active_participants = [
                p for uid, p in room_data.items()
                if now - p.get('last_seen', 0) < 35
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
                'chat_history': interview.ai_transcript or [],
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
        _init_signaling_db()
        room = request.data.get('room', 'interview_demo').strip()
        user = request.user if request.user.is_authenticated else None
        user_id = str(request.data.get('user_id') or (user.id if user else f"guest_{int(time.time()*1000)%100000}"))
        name = request.data.get('name') or (user.get_full_name() or user.email if user else 'Participant')
        role = request.data.get('role') or (user.role if (user and hasattr(user, 'role')) else 'CANDIDATE')

        raw_video = request.data.get('video_on', True)
        if isinstance(raw_video, str):
            raw_video = raw_video.lower() in ('true', '1')

        raw_mic = request.data.get('mic_on', True)
        if isinstance(raw_mic, str):
            raw_mic = raw_mic.lower() in ('true', '1')

        now = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO room_participants_live (room, user_id, name, role, video_on, mic_on, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (room, user_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        role = EXCLUDED.role,
                        video_on = EXCLUDED.video_on,
                        mic_on = EXCLUDED.mic_on,
                        last_seen = EXCLUDED.last_seen
                """, [room, str(user_id), name, role, bool(raw_video), bool(raw_mic), now])
        except Exception:
            pass

        if room not in ACTIVE_ROOMS:
            ACTIVE_ROOMS[room] = {}

        ACTIVE_ROOMS[room][str(user_id)] = {
            'user_id': user_id,
            'name': name,
            'role': role,
            'joined_at': now,
            'last_seen': now,
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
        _init_signaling_db()
        room = request.data.get('room', 'interview_demo').strip()
        user_id = str(request.data.get('user_id') or (request.user.id if request.user.is_authenticated else '999'))
        now = time.time()

        v_bool = None
        if 'video_on' in request.data:
            v = request.data.get('video_on')
            v_bool = v.lower() in ('true', '1') if isinstance(v, str) else bool(v)

        m_bool = None
        if 'mic_on' in request.data:
            m = request.data.get('mic_on')
            m_bool = m.lower() in ('true', '1') if isinstance(m, str) else bool(m)

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE room_participants_live
                    SET last_seen = %s,
                        video_on = COALESCE(%s, video_on),
                        mic_on = COALESCE(%s, mic_on)
                    WHERE room = %s AND user_id = %s
                """, [now, v_bool, m_bool, room, user_id])
        except Exception:
            pass

        if room in ACTIVE_ROOMS and user_id in ACTIVE_ROOMS[room]:
            ACTIVE_ROOMS[room][user_id]['last_seen'] = now
            if v_bool is not None:
                ACTIVE_ROOMS[room][user_id]['video_on'] = v_bool
            if m_bool is not None:
                ACTIVE_ROOMS[room][user_id]['mic_on'] = m_bool

        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class InterviewRoomLeaveView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        _init_signaling_db()
        room = request.data.get('room', 'interview_demo').strip()
        user_id = str(request.data.get('user_id') or (request.user.id if request.user.is_authenticated else '999'))
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM room_participants_live WHERE room = %s AND user_id = %s", [room, user_id])
        except Exception:
            pass

        if room in ACTIVE_ROOMS and user_id in ACTIVE_ROOMS[room]:
            del ACTIVE_ROOMS[room][user_id]
        return Response({'status': 'left'}, status=status.HTTP_200_OK)


class InterviewSignalView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        _init_signaling_db()
        room = request.query_params.get('room', '').strip()
        user_id = str(request.query_params.get('user_id', '')).strip()
        since_id = int(request.query_params.get('since', 0))

        signals = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, from_user, to_user, sig_type, payload, created_at
                    FROM room_signals_live
                    WHERE room = %s AND from_user != %s AND id > %s
                      AND (to_user = '' OR to_user = %s OR to_user = 'all')
                    ORDER BY id ASC
                    LIMIT 60
                """, [room, user_id, since_id, user_id])
                for row in cursor.fetchall():
                    raw_payload = row[4]
                    parsed_payload = raw_payload
                    try:
                        parsed_payload = json.loads(raw_payload)
                    except Exception:
                        pass
                    signals.append({
                        'id': row[0],
                        'from_user': row[1],
                        'to_user': row[2],
                        'type': row[3],
                        'payload': parsed_payload,
                        'timestamp': row[5],
                    })
        except Exception:
            # Fallback in-memory
            in_mem = ROOM_SIGNALS.get(room, [])
            signals = [
                s for s in in_mem
                if str(s.get('from_user')) != user_id
                and (not s.get('to_user') or str(s.get('to_user')) in [user_id, 'all', ''])
                and s.get('id', 0) > since_id
            ]

        return Response({'signals': signals}, status=status.HTTP_200_OK)

    def post(self, request):
        _init_signaling_db()
        room = request.data.get('room', '').strip()
        from_user = str(request.data.get('from_user', '')).strip()
        to_user = str(request.data.get('to_user', '')).strip()
        sig_type = request.data.get('type', 'webrtc')
        payload = request.data.get('payload')

        if not room:
            return Response({'error': 'Room is required'}, status=status.HTTP_400_BAD_REQUEST)

        payload_str = payload if isinstance(payload, str) else json.dumps(payload)
        now = time.time()
        sig_id = 1

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO room_signals_live (room, from_user, to_user, sig_type, payload, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [room, from_user, to_user, sig_type, payload_str, now])
                row = cursor.fetchone()
                if row:
                    sig_id = row[0]

                # Occasional cleanup: delete signals older than 5 minutes
                if sig_id % 25 == 0:
                    cursor.execute("DELETE FROM room_signals_live WHERE created_at < %s", [now - 300])
        except Exception:
            if room not in ROOM_SIGNALS:
                ROOM_SIGNALS[room] = []
            sig_id = len(ROOM_SIGNALS[room]) + 1
            ROOM_SIGNALS[room].append({
                'id': sig_id,
                'from_user': from_user,
                'to_user': to_user,
                'type': sig_type,
                'payload': payload,
                'timestamp': now,
            })
        # Save chat messages to permanent meeting history
        if sig_type == 'chat':
            try:
                target_it_id = None
                if room.startswith('interview_'):
                    r_id = room.replace('interview_', '')
                    if r_id.isdigit():
                        target_it_id = int(r_id)
                it_obj = None
                if target_it_id:
                    it_obj = Interview.objects.filter(id=target_it_id).first()
                if not it_obj:
                    it_obj = Interview.objects.filter(meeting_link__icontains=room).first()
                if it_obj:
                    history = list(it_obj.ai_transcript or [])
                    msg_dict = payload if isinstance(payload, dict) else (json.loads(payload) if isinstance(payload, str) else {'text': str(payload)})
                    if not history or history[-1].get('text') != msg_dict.get('text'):
                        history.append(msg_dict)
                        it_obj.ai_transcript = history
                        it_obj.save(update_fields=['ai_transcript'])
            except Exception:
                pass

        # Handle meeting ended signal: update Interview and Application status to COMPLETED
        if sig_type == 'meeting_ended':
            try:
                target_it_id = None
                if room.startswith('interview_'):
                    r_id = room.replace('interview_', '')
                    if r_id.isdigit():
                        target_it_id = int(r_id)
                elif '_Interview_' in room:
                    r_id = room.split('_Interview_')[-1]
                    if r_id.isdigit():
                        target_it_id = int(r_id)
                it_obj = None
                if target_it_id:
                    it_obj = Interview.objects.filter(id=target_it_id).first()
                if not it_obj:
                    it_obj = Interview.objects.filter(meeting_link__icontains=room).first()
                if it_obj:
                    it_obj.status = InterviewStatus.COMPLETED
                    it_obj.save(update_fields=['status'])
                    if it_obj.application:
                        it_obj.application.status = ApplicationStatus.INTERVIEW_COMPLETED
                        it_obj.application.save(update_fields=['status'])
                        Notification.objects.create(
                            user=it_obj.application.candidate,
                            title="Interview Concluded",
                            message=f"Your interview session for {it_obj.application.job.title} has completed.",
                            notification_type=NotificationType.SYSTEM_ALERT,
                            link="/candidate/dashboard"
                        )
            except Exception:
                pass

        return Response({'status': 'sent', 'id': sig_id}, status=status.HTTP_200_OK)


class InterviewCleanupDummiesView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        action = 'clean' if 'clean' in request.path else (request.query_params.get('action') or request.GET.get('action', 'inspect'))
        interviews_all = list(Interview.objects.values('id', 'title', 'status', 'created_at'))
        users_all = list(User.objects.values('id', 'email', 'first_name', 'last_name', 'role'))

        if action == 'clean':
            from jobs.models import Job
            from accounts.models import UserRole
            # Remove all dummy accounts
            dummy_emails = ['amira@talentai.io', 'marcus@talentai.io', 'recruiter@talentai.io', 'test@talentai.io', 'candidate@talentai.io']
            User.objects.filter(email__in=dummy_emails).delete()
            # Remove legacy dummy jobs
            Job.objects.filter(title__in=[
                "Senior Full Stack AI Engineer",
                "Lead Flutter & Mobile Systems Architect",
                "Staff Infrastructure & DevOps Engineer",
                "Senior Product Manager (AI Platform)"
            ]).delete()
            # Clear test interviews
            Interview.objects.filter(title__icontains='Demo').delete()

            ACTIVE_ROOMS.clear()
            ROOM_SIGNALS.clear()

            return Response({
                'status': 'cleaned',
                'super_admin': 'admin@talentai.io',
                'interviews_remaining': Interview.objects.count(),
                'jobs_remaining': Job.objects.count(),
                'users_remaining': list(User.objects.values('id', 'email', 'first_name', 'last_name', 'role')),
            })

        return Response({
            'interviews': interviews_all,
            'users': users_all,
        })

