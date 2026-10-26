from django.urls import path
from ai_services.views import (
    AIResumeParseView,
    AIGenerateJobDescriptionView,
    AIMatchCandidateView,
    AIGenerateInterviewQuestionsView,
    AIAssistantChatView,
    AITranslateView,
    AIGrammarImproveView,
    AIVoiceQuestionView,
)

urlpatterns = [
    path('resume-parse/', AIResumeParseView.as_view(), name='ai-resume-parse'),
    path('generate-job-description/', AIGenerateJobDescriptionView.as_view(), name='ai-generate-job-description'),
    path('match-candidate/', AIMatchCandidateView.as_view(), name='ai-match-candidate'),
    path('generate-interview-questions/', AIGenerateInterviewQuestionsView.as_view(), name='ai-generate-interview-questions'),
    path('assistant/', AIAssistantChatView.as_view(), name='ai-assistant-chat'),
    path('translate/', AITranslateView.as_view(), name='ai-translate'),
    path('improve-text/', AIGrammarImproveView.as_view(), name='ai-improve-text'),
    path('voice-question/', AIVoiceQuestionView.as_view(), name='ai-voice-question'),
]
