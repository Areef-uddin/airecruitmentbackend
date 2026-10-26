import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from interviews.models import Interview
from applications.models import JobApplication

print("--- USERS ---")
for u in User.objects.all():
    print(f"User {u.id}: email={u.email}, name={u.first_name} {u.last_name}, role={u.role}")

print("\n--- INTERVIEWS ---")
for i in Interview.objects.all():
    cand = i.application.candidate if i.application else "None"
    cand_name = f"{cand.first_name} {cand.last_name}" if cand != "None" else "None"
    print(f"Interview {i.id}: title={i.title}, status={i.status}, room={i.room_id}, candidate={cand_name}, link={i.meeting_link}")
