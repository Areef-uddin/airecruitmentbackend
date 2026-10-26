from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ai_services.services import AIService
from jobs.models import Job
from accounts.models import User


class AIResumeParseView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        file_name = request.data.get('file_name', 'resume.pdf')
        raw_text = request.data.get('raw_text', '')
        result = AIService.parse_resume(file_name=file_name, raw_text=raw_text)
        return Response(result, status=status.HTTP_200_OK)


class AIGenerateJobDescriptionView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        title = request.data.get('title', 'Senior Software Engineer')
        level = request.data.get('experience_level', 'Senior')
        workplace = request.data.get('workplace_type', 'Remote')
        skills = request.data.get('skills', ['Python', 'Flutter', 'Cloud'])
        industry = request.data.get('industry', 'Technology')

        result = AIService.generate_job_description(
            title=title,
            experience_level=level,
            workplace_type=workplace,
            key_skills=skills,
            industry=industry
        )
        return Response(result, status=status.HTTP_200_OK)


class AIMatchCandidateView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        candidate_id = request.data.get('candidate_id')
        job_id = request.data.get('job_id')

        candidate = get_object_or_404(User, id=candidate_id) if candidate_id else request.user
        job = get_object_or_404(Job, id=job_id)

        result = AIService.match_candidate_to_job(candidate_user=candidate, job=job)
        return Response(result, status=status.HTTP_200_OK)


class AIGenerateInterviewQuestionsView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        job_id = request.data.get('job_id')
        title = request.data.get('title')
        skills = request.data.get('skills', [])

        if job_id:
            job = get_object_or_404(Job, id=job_id)
            title = job.title
            skills = list(job.required_skills.values_list('skill__name', flat=True))

        title = title or 'Full Stack Software Engineer'
        questions = AIService.generate_interview_questions(job_title=title, required_skills=skills)
        return Response({'job_title': title, 'questions': questions}, status=status.HTTP_200_OK)


class AIAssistantChatView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        role = getattr(request.user, 'role', 'RECRUITER')
        reply_data = AIService.assistant_chat(user_message=message, user_role=role)
        return Response(reply_data, status=status.HTTP_200_OK)


class AITranslateView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        text = request.data.get('text', '').strip()
        target_language = request.data.get('target_language', 'English').strip()
        if not text:
            return Response({'translated': '', 'original': '', 'target_language': target_language}, status=status.HTTP_200_OK)

        result = AIService.translate_text(text=text, target_language=target_language)
        return Response(result, status=status.HTTP_200_OK)


class AIGrammarImproveView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        text = request.data.get('text', '').strip()
        mode = request.data.get('mode', 'grammar').strip()
        result = AIService.improve_text(text=text, mode=mode)
        return Response(result, status=status.HTTP_200_OK)

