from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, UserRole
from candidates.models import CandidateProfile
from recruiters.models import RecruiterProfile


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'phone_number', 'avatar',
            'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username or obj.email


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name', 'role', 'phone_number', 'company_name']

    def create(self, validated_data):
        company_name = validated_data.pop('company_name', None)
        password = validated_data.pop('password')
        role = validated_data.get('role', UserRole.CANDIDATE)

        user = User.objects.create_user(password=password, **validated_data)

        # Automatically create appropriate profile
        if role == UserRole.CANDIDATE:
            CandidateProfile.objects.create(
                user=user,
                headline="Software Engineer & AI Enthusiast",
                bio="Passionate engineer looking for high impact opportunities.",
                location="Remote / San Francisco"
            )
        elif role == UserRole.RECRUITER:
            from companies.models import Company
            company = None
            if company_name:
                company, _ = Company.objects.get_or_create(
                    name=company_name,
                    defaults={'description': f"{company_name} - Innovative Technology Company", 'industry': 'Technology'}
                )
            RecruiterProfile.objects.create(
                user=user,
                company=company,
                title="Talent Acquisition Partner"
            )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = (attrs.get('email') or '').strip().lower()
        password = attrs.get('password')

        user_obj = User.objects.filter(email__iexact=email).first()
        if not user_obj:
            raise serializers.ValidationError({"detail": "No account found with this email."})

        user = authenticate(request=self.context.get('request'), email=user_obj.email, password=password)
        if not user:
            user = authenticate(request=self.context.get('request'), username=user_obj.email, password=password)
        if not user:
            user = authenticate(request=self.context.get('request'), username=user_obj.username, password=password)
        if not user and user_obj.check_password(password):
            user = user_obj

        if not user:
            raise serializers.ValidationError({"detail": "Incorrect password. Please check your password and try again."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is disabled."})

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
