import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, UserRole
from candidates.models import Skill
from audit_logs.models import AuditLog


def run_seed():
    print("[*] Starting TalentAI Database Initialization (Clean Production State)...")

    # 1. Clean out legacy dummy users and dummy jobs if present
    from jobs.models import Job
    from applications.models import JobApplication
    from interviews.models import Interview
    from resumes.models import Resume
    from messaging.models import Conversation, Message

    dummy_emails = [
        'amira@talentai.io',
        'marcus@talentai.io',
        'recruiter@talentai.io',
        'test@talentai.io',
        'candidate@talentai.io'
    ]

    # Delete dummy users and dummy jobs
    dummy_users = User.objects.filter(email__in=dummy_emails)
    if dummy_users.exists():
        count = dummy_users.count()
        dummy_users.delete()
        print(f"  - Removed {count} legacy dummy users.")

    # Remove dummy jobs created by dummy accounts or legacy sample jobs
    dummy_job_titles = [
        "Senior Full Stack AI Engineer",
        "Lead Flutter & Mobile Systems Architect",
        "Staff Infrastructure & DevOps Engineer",
        "Senior Product Manager (AI Platform)"
    ]
    dummy_jobs = Job.objects.filter(title__in=dummy_job_titles)
    if dummy_jobs.exists():
        j_count = dummy_jobs.count()
        dummy_jobs.delete()
        print(f"  - Removed {j_count} legacy dummy job postings.")

    # 2. Super Admin Account
    admin_user, created = User.objects.get_or_create(
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
    admin_user.role = UserRole.SUPER_ADMIN
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.is_verified = True
    admin_user.save()
    print(f"  + Super Admin verified: admin@talentai.io (pwd: admin123)")

    # 3. Standard Technical Skills Taxonomy (Essential catalog for job creation & candidate matching)
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
        ("JavaScript", "Frontend"),
        ("TypeScript", "Frontend"),
        ("React", "Frontend"),
        ("Node.js", "Backend"),
        ("AWS", "DevOps & Cloud"),
    ]

    for name, cat in skills_data:
        Skill.objects.get_or_create(name=name, defaults={'category': cat})
    print(f"  + Skills taxonomy verified ({len(skills_data)} skills ready)")

    # 4. Audit Log
    AuditLog.objects.create(
        user=admin_user,
        action="SYSTEM_INIT_CLEAN",
        entity_type="SYSTEM",
        entity_id="1",
        ip_address="127.0.0.1",
        details={'status': 'System initialized with Super Admin only. No dummy users or sample jobs.'}
    )
    print("* TalentAI database initialization complete. Clean production state ready.")


if __name__ == '__main__':
    run_seed()
