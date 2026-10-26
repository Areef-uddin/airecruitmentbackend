from rest_framework import generics, permissions, status
from rest_framework.response import Response
from candidates.models import CandidateProfile, Skill, CandidateSkill
from candidates.serializers import CandidateProfileSerializer, SkillSerializer, CandidateSkillSerializer
from jobs.models import Job, JobStatus


class CandidateMeView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        profile, _ = CandidateProfile.objects.get_or_create(user=self.request.user)
        return profile


class SkillListView(generics.ListCreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None


class CandidateSkillManageView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        skill_id = request.data.get('skill_id')
        skill_name = request.data.get('skill_name')
        years = request.data.get('years_experience', 1.0)
        proficiency = request.data.get('proficiency', 'INTERMEDIATE')

        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)

        if skill_id:
            skill = Skill.objects.get(id=skill_id)
        elif skill_name:
            skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
        else:
            return Response({'error': 'Skill id or name is required'}, status=status.HTTP_400_BAD_REQUEST)

        cs, created = CandidateSkill.objects.update_or_create(
            candidate=profile,
            skill=skill,
            defaults={'years_experience': years, 'proficiency': proficiency}
        )

        return Response(CandidateSkillSerializer(cs).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, pk=None):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        CandidateSkill.objects.filter(candidate=profile, id=pk).delete()
        return Response({'message': 'Skill removed'}, status=status.HTTP_204_NO_CONTENT)


class CandidateRecommendedJobsView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        user_skills = set(profile.skills.values_list('skill__name', flat=True))

        active_jobs = Job.objects.filter(status=JobStatus.ACTIVE).select_related('company').prefetch_related('required_skills__skill')

        recommendations = []
        for job in active_jobs:
            job_skills = set(job.required_skills.values_list('skill__name', flat=True))
            if not job_skills:
                match_pct = 75.0
                matched = list(user_skills)[:3]
                missing = []
            else:
                matched = list(user_skills.intersection(job_skills))
                missing = list(job_skills.difference(user_skills))
                match_pct = round((len(matched) / len(job_skills)) * 100, 1)

            # Boost if candidate experience aligns with job experience
            recommendations.append({
                'id': job.id,
                'title': job.title,
                'company_name': job.company.name,
                'company_logo': job.company.logo_url or (job.company.logo.url if job.company.logo else ''),
                'location': job.location,
                'job_type': job.job_type,
                'workplace_type': job.workplace_type,
                'min_salary': float(job.min_salary) if job.min_salary else None,
                'max_salary': float(job.max_salary) if job.max_salary else None,
                'currency': job.currency,
                'match_percentage': max(match_pct, 45.0),  # Baseline floor
                'matched_skills': matched,
                'missing_skills': missing,
                'ai_rationale': f"Strong alignment in {', '.join(matched[:3]) if matched else 'core competencies'}."
            })

        # Sort descending by match percentage
        recommendations.sort(key=lambda x: x['match_percentage'], reverse=True)

        return Response({'results': recommendations[:10]}, status=status.HTTP_200_OK)
