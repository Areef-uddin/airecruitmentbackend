from rest_framework import serializers
from candidates.models import CandidateProfile, Skill, CandidateSkill
from accounts.serializers import UserSerializer


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category']


class CandidateSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.ReadOnlyField(source='skill.name')
    category = serializers.ReadOnlyField(source='skill.category')

    class Meta:
        model = CandidateSkill
        fields = ['id', 'skill', 'skill_name', 'category', 'years_experience', 'proficiency']


class CandidateProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = CandidateSkillSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'user', 'headline', 'bio', 'location',
            'years_of_experience', 'expected_salary', 'currency',
            'current_company', 'notice_period_days',
            'portfolio_url', 'linkedin_url', 'github_url',
            'is_actively_looking', 'ai_summary', 'skills',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
