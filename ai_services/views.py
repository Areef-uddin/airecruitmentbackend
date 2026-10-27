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


from django.utils import timezone

class AIGenerateInterviewQuestionsView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        job_id = request.data.get('job_id')
        interview_id = request.data.get('interview_id')
        title = request.data.get('title')
        skills = request.data.get('skills', [])
        resume_text = request.data.get('resume_text', '')
        job_desc = request.data.get('job_description', '')

        if interview_id:
            from interviews.models import Interview
            it = Interview.objects.filter(id=interview_id).select_related('application', 'application__job', 'application__candidate', 'application__resume').first()
            if it and it.application:
                if it.application.job:
                    title = title or it.application.job.title
                    job_desc = job_desc or it.application.job.description
                    if not skills:
                        skills = list(it.application.job.required_skills.values_list('skill__name', flat=True))
                if it.application.resume:
                    resume_text = resume_text or it.application.resume.extracted_text or str(it.application.resume.parsed_data)
                elif it.application.candidate:
                    resume_text = resume_text or f"Candidate: {it.application.candidate.get_full_name()}"

        elif job_id:
            job = get_object_or_404(Job, id=job_id)
            title = title or job.title
            job_desc = job_desc or job.description
            if not skills:
                skills = list(job.required_skills.values_list('skill__name', flat=True))

        if not resume_text:
            from resumes.models import Resume
            primary_resume = Resume.objects.filter(candidate=request.user, is_primary=True).first() or Resume.objects.filter(candidate=request.user).first()
            if primary_resume:
                resume_text = primary_resume.extracted_text or str(primary_resume.parsed_data)

        title = title or 'Software Engineer'
        questions = AIService.generate_interview_questions(
            job_title=title,
            required_skills=skills,
            resume_text=resume_text,
            job_description=job_desc
        )
        return Response({'job_title': title, 'questions': questions}, status=status.HTTP_200_OK)


class AIEvaluateCandidateAnswerView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        question = request.data.get('question', '').strip()
        answer = request.data.get('answer', '').strip()
        job_title = request.data.get('job_title', 'Software Engineer')
        resume_text = request.data.get('resume_text', '')
        interview_id = request.data.get('interview_id')

        turn_eval = AIService.evaluate_candidate_turn(
            question=question,
            answer=answer,
            job_title=job_title,
            resume_text=resume_text
        )

        if interview_id:
            from interviews.models import Interview
            it = Interview.objects.filter(id=interview_id).first()
            if it:
                history = it.ai_transcript or []
                history.append({
                    'speaker': 'Nora',
                    'text': question,
                    'timestamp': timezone.now().isoformat()
                })
                history.append({
                    'speaker': request.user.get_full_name() or 'Candidate',
                    'text': answer,
                    'score': turn_eval.get('score', 85),
                    'timestamp': timezone.now().isoformat()
                })
                it.ai_transcript = history
                it.save(update_fields=['ai_transcript'])

        return Response(turn_eval, status=status.HTTP_200_OK)


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

