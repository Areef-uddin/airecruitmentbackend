from django.urls import path
from ai_services.views import (
    AIResumeParseView,
    AIGenerateJobDescriptionView,
    AIMatchCandidateView,
    AIGenerateInterviewQuestionsView,
    AIEvaluateCandidateAnswerView,
    AIAssistantChatView,
    AITranslateView,
    AIGrammarImproveView,
    AIGenerateMCQQuizzesView,
)

urlpatterns = [
    path('resume-parse/', AIResumeParseView.as_view(), name='ai-resume-parse'),
    path('generate-job-description/', AIGenerateJobDescriptionView.as_view(), name='ai-generate-job-description'),
    path('match-candidate/', AIMatchCandidateView.as_view(), name='ai-match-candidate'),
    path('generate-interview-questions/', AIGenerateInterviewQuestionsView.as_view(), name='ai-generate-interview-questions'),
    path('generate-quizzes/', AIGenerateMCQQuizzesView.as_view(), name='ai-generate-quizzes'),
    path('evaluate-answer/', AIEvaluateCandidateAnswerView.as_view(), name='ai-evaluate-answer'),
    path('assistant/', AIAssistantChatView.as_view(), name='ai-assistant-chat'),
    path('translate/', AITranslateView.as_view(), name='ai-translate'),
    path('improve-text/', AIGrammarImproveView.as_view(), name='ai-improve-text'),
]
