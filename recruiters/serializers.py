from rest_framework import serializers
from recruiters.models import RecruiterProfile
from accounts.serializers import UserSerializer
from companies.serializers import CompanySerializer


class RecruiterProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = RecruiterProfile
        fields = ['id', 'user', 'company', 'company_id', 'title', 'department', 'phone', 'bio', 'is_verified', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def update(self, instance, validated_data):
        company_id = validated_data.pop('company_id', None)
        if company_id:
            from companies.models import Company
            try:
                instance.company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        return super().update(instance, validated_data)
