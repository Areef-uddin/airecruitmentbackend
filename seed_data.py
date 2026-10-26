import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, UserRole
from companies.models import Company, CompanyMembership
from candidates.models import CandidateProfile, Skill, CandidateSkill, ProficiencyLevel
from recruiters.models import RecruiterProfile
from jobs.models import Job, JobType, WorkplaceType, ExperienceLevel, JobStatus, JobSkill
from applications.models import JobApplication, ApplicationStatus
from resumes.models import Resume
from interviews.models import Interview, InterviewType, InterviewStatus
from notifications.models import Notification, NotificationType
from messaging.models import Conversation, Message
from audit_logs.models import AuditLog


def run_seed():
    print("[*] Starting TalentAI Database Seeding...")

    # 1. Super Admin
    admin_user, _ = User.objects.get_or_create(
        email='admin@talentai.io',
        defaults={
            'username': 'superadmin',
            'first_name': 'Alexander',
            'last_name': 'Wright',
            'role': UserRole.SUPER_ADMIN,
            'is_staff': True,
            'is_superuser': True,
            'is_verified': True
        }
    )
    admin_user.set_password('admin123')
    admin_user.save()
    print("  + Super Admin ready: admin@talentai.io (pwd: admin123)")

    # 2. Companies
    c1, _ = Company.objects.get_or_create(
        name="NexusAI Technologies",
        defaults={
            'description': "Next-generation intelligence platform powering autonomous enterprise recruiting and talent orchestration.",
            'industry': "Artificial Intelligence",
            'company_size': "250-500 employees",
            'headquarters': "San Francisco, CA",
            'website': "https://nexusai.io",
            'is_verified': True,
            'verification_date': timezone.now()
        }
    )

    c2, _ = Company.objects.get_or_create(
        name="Apex Cloud Networks",
        defaults={
            'description': "High-performance distributed cloud orchestration and hyper-scale infrastructure solutions.",
            'industry': "Cloud Infrastructure",
            'company_size': "500-1000 employees",
            'headquarters': "Seattle, WA",
            'website': "https://apexcloud.net",
            'is_verified': True,
            'verification_date': timezone.now()
        }
    )

    c3, _ = Company.objects.get_or_create(
        name="Hyperion FinTech",
        defaults={
            'description': "Next-generation decentralized finance and cross-border instant settlement network.",
            'industry': "Financial Technology",
            'company_size': "100-250 employees",
            'headquarters': "New York, NY",
            'website': "https://hyperionfin.com",
            'is_verified': True
        }
    )
    print("  + Companies created: NexusAI, Apex Cloud, Hyperion FinTech")

    # 3. Recruiter
    recruiter_user, _ = User.objects.get_or_create(
        email='recruiter@talentai.io',
        defaults={
            'username': 'sarah_recruiter',
            'first_name': 'Sarah',
            'last_name': 'Jenkins',
            'role': UserRole.RECRUITER,
            'is_verified': True,
            'phone_number': '+1 (415) 882-9011'
        }
    )
    recruiter_user.set_password('recruiter123')
    recruiter_user.save()

    recruiter_profile, _ = RecruiterProfile.objects.get_or_create(
        user=recruiter_user,
        defaults={
            'company': c1,
            'title': 'Head of Global Talent Acquisition',
            'department': 'Talent & Culture',
            'bio': 'Specializing in scaling engineering teams and building high-impact AI organizations.'
        }
    )
    recruiter_profile.company = c1
    recruiter_profile.save()

    CompanyMembership.objects.get_or_create(
        company=c1,
        user=recruiter_user,
        defaults={'role': 'ADMIN'}
    )
    print("  + Recruiter ready: recruiter@talentai.io (pwd: recruiter123)")

    # 4. Candidates
    amira_user, _ = User.objects.get_or_create(
        email='amira@talentai.io',
        defaults={
            'username': 'amira_candidate',
            'first_name': 'Amira',
            'last_name': 'Patel',
            'role': UserRole.CANDIDATE,
            'is_verified': True,
            'phone_number': '+1 (510) 932-4110'
        }
    )
    amira_user.set_password('candidate123')
    amira_user.save()

    amira_profile, _ = CandidateProfile.objects.get_or_create(
        user=amira_user,
        defaults={
            'headline': 'Senior Full-Stack & AI Engineer | Flutter, Python, LLMs',
            'bio': 'Passionate builder with 6+ years shipping production cross-platform apps and LLM-powered services. Proven track record in high-velocity startups.',
            'location': 'San Francisco, CA (Open to Remote)',
            'years_of_experience': 6.0,
            'expected_salary': 185000.00,
            'current_company': 'InnovateLabs',
            'notice_period_days': 15,
            'github_url': 'https://github.com/amira-eng',
            'linkedin_url': 'https://linkedin.com/in/amira-patel',
            'ai_summary': 'Top 5% match for Senior Engineering roles. Exceptional problem solving, architectural clarity, and strong communication skills.'
        }
    )

    marcus_user, _ = User.objects.get_or_create(
        email='marcus@talentai.io',
        defaults={
            'username': 'marcus_candidate',
            'first_name': 'Marcus',
            'last_name': 'Vance',
            'role': UserRole.CANDIDATE,
            'is_verified': True,
            'phone_number': '+1 (650) 412-8871'
        }
    )
    marcus_user.set_password('candidate123')
    marcus_user.save()

    marcus_profile, _ = CandidateProfile.objects.get_or_create(
        user=marcus_user,
        defaults={
            'headline': 'Lead Flutter Architect & Mobile Specialist',
            'bio': '8 years crafting responsive web and mobile experiences. Expert in Riverpod, clean MVVM, and offline-first reactive architectures.',
            'location': 'Austin, TX',
            'years_of_experience': 8.0,
            'expected_salary': 195000.00,
            'current_company': 'SwiftScale Mobile',
            'notice_period_days': 30
        }
    )
    print("  + Candidates created: Amira Patel (amira@talentai.io) & Marcus Vance (marcus@talentai.io)")

    # 5. Skills
    skills_data = [
        ("Python", "Programming"),
        ("Dart", "Programming"),
        ("Flutter", "Mobile & Web"),
        ("Django", "Backend"),
        ("Django REST Framework", "Backend"),
        ("PostgreSQL", "Database"),
        ("Docker", "DevOps & Cloud"),
        ("Riverpod", "Mobile & Web"),
        ("GoRouter", "Mobile & Web"),
        ("System Design", "Architecture"),
        ("Machine Learning", "AI & Data"),
        ("LLM Prompt Engineering", "AI & Data"),
        ("REST APIs", "Backend"),
        ("GraphQL", "Backend"),
        ("Kubernetes", "DevOps & Cloud"),
    ]

    skill_objs = {}
    for name, cat in skills_data:
        s, _ = Skill.objects.get_or_create(name=name, defaults={'category': cat})
        skill_objs[name] = s

    # Assign skills to Amira
    for skill_name, prof, years in [
        ("Python", ProficiencyLevel.EXPERT, 6.0),
        ("Flutter", ProficiencyLevel.EXPERT, 5.0),
        ("Django", ProficiencyLevel.ADVANCED, 5.0),
        ("PostgreSQL", ProficiencyLevel.ADVANCED, 4.0),
        ("Machine Learning", ProficiencyLevel.INTERMEDIATE, 3.0),
        ("System Design", ProficiencyLevel.ADVANCED, 5.0),
        ("REST APIs", ProficiencyLevel.EXPERT, 6.0),
    ]:
        CandidateSkill.objects.get_or_create(
            candidate=amira_profile,
            skill=skill_objs[skill_name],
            defaults={'proficiency': prof, 'years_experience': years}
        )

    # Assign skills to Marcus
    for skill_name, prof, years in [
        ("Dart", ProficiencyLevel.EXPERT, 7.0),
        ("Flutter", ProficiencyLevel.EXPERT, 7.0),
        ("Riverpod", ProficiencyLevel.EXPERT, 5.0),
        ("GoRouter", ProficiencyLevel.EXPERT, 4.0),
        ("System Design", ProficiencyLevel.ADVANCED, 6.0),
    ]:
        CandidateSkill.objects.get_or_create(
            candidate=marcus_profile,
            skill=skill_objs[skill_name],
            defaults={'proficiency': prof, 'years_experience': years}
        )
    print("  + Skills catalog populated & assigned to candidates")

    # 6. Resumes
    r1, _ = Resume.objects.get_or_create(
        candidate=amira_user,
        file_name="Amira_Patel_Senior_AI_Engineer_2026.pdf",
        defaults={
            'file_size': 428000,
            'file_type': 'pdf',
            'is_primary': True,
            'ai_parsed': True,
            'parsed_at': timezone.now(),
            'extracted_text': "Amira Patel - Senior Full Stack & AI Engineer. Expertise in Flutter, Dart, Python, Django, Cloud, and Machine Learning.",
            'parsed_data': {
                'summary': "Accomplished Senior Full Stack and AI Engineer with deep background architecting high-performance systems and intuitive cross-platform client applications.",
                'skills': ["Python", "Flutter", "Dart", "Django", "PostgreSQL", "Machine Learning", "System Design"],
                'experience_years': 6.0,
                'education': [
                    {'degree': 'B.S. in Computer Science', 'institution': 'Stanford University', 'year': '2020'}
                ],
                'certifications': ['AWS Certified Solutions Architect', 'Google Professional Cloud Architect']
            }
        }
    )

    # 7. Jobs
    job1, _ = Job.objects.get_or_create(
        title="Lead Full-Stack AI Engineer",
        company=c1,
        defaults={
            'recruiter': recruiter_user,
            'description': "We are searching for a visionary Lead Full-Stack AI Engineer to spearhead our next-generation automated recruiting and evaluation platform. You will build resilient real-time services, integrate generative AI workflows, and design stunning user interfaces.",
            'responsibilities': "- Architect and scale end-to-end AI applications using Python, Django, and Flutter.\n- Lead technical design reviews and mentor engineers.\n- Build ultra-responsive desktop web and mobile client interfaces.\n- Optimize AI pipeline throughput and latency.",
            'requirements': "- 5+ years building production applications in Python, Django, and modern client frameworks (Flutter preferred).\n- Hands-on experience integrating LLM APIs and prompt engineering.\n- Strong foundation in relational database schema design and distributed caching.\n- Passion for sleek product design and exceptional user experience.",
            'benefits': "- Competitive compensation package ($175k - $210k + Equity).\n- Fully remote or hybrid in San Francisco office.\n- Top-tier medical, dental, and vision insurance.\n- $3,000 annual continuous education and conference budget.",
            'job_type': JobType.FULL_TIME,
            'workplace_type': WorkplaceType.REMOTE,
            'experience_level': ExperienceLevel.LEAD,
            'min_salary': 175000.00,
            'max_salary': 210000.00,
            'currency': 'USD',
            'location': 'San Francisco, CA / Remote',
            'status': JobStatus.ACTIVE,
            'views_count': 142
        }
    )

    job2, _ = Job.objects.get_or_create(
        title="Senior Flutter & Mobile Architect",
        company=c1,
        defaults={
            'recruiter': recruiter_user,
            'description': "Join NexusAI to pioneer our responsive Flutter web and native Android recruitment applications. Work directly with design leaders to craft fluid, delightful experiences.",
            'responsibilities': "- Build clean, testable, and highly responsive Flutter components across desktop web and Android.\n- Implement MVVM architecture with Riverpod and GoRouter.\n- Ensure 60fps animations and flawless responsive layout adaptations.",
            'requirements': "- 4+ years of professional Flutter & Dart development.\n- Deep mastery of state management (Riverpod/Bloc) and clean architecture.\n- Experience with REST API consumption, caching, and secure token storage.",
            'benefits': "- Comprehensive benefits and wellness stipend.\n- Equity grants and annual bonus.",
            'job_type': JobType.FULL_TIME,
            'workplace_type': WorkplaceType.HYBRID,
            'experience_level': ExperienceLevel.SENIOR,
            'min_salary': 160000.00,
            'max_salary': 190000.00,
            'currency': 'USD',
            'location': 'San Francisco, CA',
            'status': JobStatus.ACTIVE,
            'views_count': 98
        }
    )

    job3, _ = Job.objects.get_or_create(
        title="Staff Machine Learning Platform Engineer",
        company=c2,
        defaults={
            'recruiter': recruiter_user,
            'description': "Apex Cloud is seeking a Staff ML Platform Engineer to build scalable evaluation, inference, and orchestration infrastructure.",
            'responsibilities': "- Build distributed model serving infrastructure with sub-100ms P99 latencies.\n- Automate model monitoring, drift detection, and automated evaluations.",
            'requirements': "- Extensive track record deploying ML pipelines in Kubernetes.\n- Mastery of Python, C++, and high-throughput streaming systems.",
            'benefits': "- Competitive Silicon Valley package with significant equity.",
            'job_type': JobType.FULL_TIME,
            'workplace_type': WorkplaceType.REMOTE,
            'experience_level': ExperienceLevel.LEAD,
            'min_salary': 190000.00,
            'max_salary': 240000.00,
            'currency': 'USD',
            'location': 'Seattle, WA / Remote',
            'status': JobStatus.ACTIVE,
            'views_count': 185
        }
    )

    # Link skills to jobs
    for j, req_skills in [
        (job1, ["Python", "Django", "Flutter", "PostgreSQL", "System Design", "Machine Learning"]),
        (job2, ["Flutter", "Dart", "Riverpod", "GoRouter", "REST APIs"]),
        (job3, ["Python", "Docker", "Kubernetes", "System Design", "Machine Learning"]),
    ]:
        for s_name in req_skills:
            if s_name in skill_objs:
                JobSkill.objects.get_or_create(job=j, skill=skill_objs[s_name], defaults={'is_mandatory': True})

    print("  + Jobs created with skills: Lead Full-Stack AI Engineer, Senior Flutter Architect, Staff ML Platform Engineer")

    # 8. Applications & AI Match Scores
    app1, _ = JobApplication.objects.get_or_create(
        job=job1,
        candidate=amira_user,
        defaults={
            'resume': r1,
            'cover_letter': "I have spent the past 6 years building production web/mobile systems and AI architectures. The mission of NexusAI closely aligns with my passion for intelligent workflows.",
            'status': ApplicationStatus.INTERVIEW_SCHEDULED,
            'ai_match_score': 93.0,
            'ai_match_explanation': "Candidate demonstrated exceptional technical mastery in Python, Flutter, and Django. Demonstrated 6 years of hands-on production delivery with high algorithmic aptitude.",
            'ai_matched_skills': ["Python", "Django", "Flutter", "PostgreSQL", "Machine Learning", "System Design"],
            'ai_missing_skills': []
        }
    )

    app2, _ = JobApplication.objects.get_or_create(
        job=job2,
        candidate=marcus_user,
        defaults={
            'status': ApplicationStatus.SHORTLISTED,
            'ai_match_score': 91.5,
            'ai_match_explanation': "Extensive 8 years Flutter ecosystem mastery. Outstanding match for lead architecture and responsive web/mobile orchestration.",
            'ai_matched_skills': ["Flutter", "Dart", "Riverpod", "GoRouter", "REST APIs"],
            'ai_missing_skills': []
        }
    )
    print("  + Applications created with AI match scores (Amira: 93%, Marcus: 91.5%)")

    # 9. Live Interview Session (Directly matching the uploaded reference image!)
    interview1, _ = Interview.objects.get_or_create(
        application=app1,
        title="AI Interview Session: Technical Screening",
        defaults={
            'interview_type': InterviewType.AI_SCREENING,
            'interviewer': recruiter_user,
            'scheduled_at': timezone.now() - timedelta(hours=2),
            'duration_minutes': 30,
            'meeting_link': "/live-interview?room=interview_1&id=1",
            'status': InterviewStatus.COMPLETED,
            'ai_score': 93.0,
            'ai_feedback': "Candidate demonstrated strong technical knowledge in Python and JavaScript. Communication skills excellent with clear explanations of complex concepts.",
            'ai_transcript': [
                {
                    'speaker': 'Nora',
                    'role': 'AI Interviewer',
                    'text': 'How do you research prospects and validate architectural assumptions?'
                },
                {
                    'speaker': 'Amira',
                    'role': 'Candidate',
                    'text': 'I check LinkedIn, company news, and use Crunchbase to evaluate customer domain models and scale requirements.'
                },
                {
                    'speaker': 'Amira',
                    'role': 'Candidate',
                    'text': 'Where do SDRs and product engineers here typically identify bottleneck patterns?'
                },
                {
                    'speaker': 'Nora',
                    'role': 'AI Interviewer',
                    'text': 'Inbound lists, LinkedIn, and target accounts telemetry.'
                }
            ]
        }
    )
    print("  + Reference-image interview session created (Nora & Amira, 93 score, exact transcript)")

    # 10. Notifications
    Notification.objects.get_or_create(
        user=amira_user,
        title="AI Interview Completed: 93/100 Score",
        defaults={
            'message': "Your AI Screening Session with Nora has been evaluated. You scored in the top 3% of applicants!",
            'notification_type': NotificationType.AI_MATCH,
            'link': f"/interviews/{interview1.id}",
            'is_read': False
        }
    )

    Notification.objects.get_or_create(
        user=recruiter_user,
        title="Top Candidate Alert: Amira Patel (93% Match)",
        defaults={
            'message': "Amira Patel completed the AI screening session with exceptional marks. Recommend scheduling final team round.",
            'notification_type': NotificationType.APPLICATION_UPDATE,
            'link': f"/recruiter/applications/{app1.id}",
            'is_read': False
        }
    )

    # 11. Conversation
    conv1, _ = Conversation.objects.get_or_create(
        subject="Interview Follow-up: Lead Full-Stack AI Engineer"
    )
    conv1.participants.add(recruiter_user, amira_user)
    Message.objects.get_or_create(
        conversation=conv1,
        sender=recruiter_user,
        defaults={
            'body': "Hi Amira! We reviewed your AI screening session with Nora. The technical feedback was stellar (93 score). We'd love to discuss next steps!"
        }
    )

    # 12. Audit Log
    AuditLog.objects.create(
        user=admin_user,
        action="SYSTEM_INIT_SEED",
        entity_type="SYSTEM",
        entity_id="1",
        details={'status': 'Seed completed successfully', 'entities_created': ['Admin', 'Recruiter', 'Candidates', 'Jobs', 'Interviews']}
    )

    print("* Database seed completed successfully! All entities ready.")


if __name__ == '__main__':
    run_seed()
