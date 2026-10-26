from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    CANDIDATE = 'CANDIDATE', 'Candidate'
    RECRUITER = 'RECRUITER', 'Recruiter'
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
        db_index=True,
    )
    phone_number = models.CharField(max_length=20, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_candidate(self):
        return self.role == UserRole.CANDIDATE

    @property
    def is_recruiter(self):
        return self.role == UserRole.RECRUITER

    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN or self.is_superuser
