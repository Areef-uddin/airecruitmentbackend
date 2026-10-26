from rest_framework import serializers
from resumes.models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            'id', 'file', 'file_url', 'file_name', 'file_size', 'file_type',
            'extracted_text', 'parsed_data', 'is_primary', 'ai_parsed',
            'parsed_at', 'uploaded_at'
        ]
        read_only_fields = ['id', 'file_url', 'file_size', 'file_type', 'extracted_text', 'parsed_data', 'ai_parsed', 'parsed_at', 'uploaded_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
