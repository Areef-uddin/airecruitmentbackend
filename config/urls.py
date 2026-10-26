from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def root_api_view(request):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TalentAI API Server</title>
  <meta http-equiv="refresh" content="2;url=http://localhost:3000">
  <style>
    body {
      background: #0D0E15;
      color: #FFFFFF;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      background: #13141F;
      border: 1px solid #2E324D;
      border-radius: 16px;
      padding: 36px 44px;
      text-align: center;
      max-width: 480px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.6);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #10B981;
      padding: 4px 12px;
      border-radius: 100px;
      font-size: 12px;
      font-weight: bold;
      margin-bottom: 16px;
    }
    .dot { width: 8px; height: 8px; background: #10B981; border-radius: 50%; margin-right: 6px; }
    h1 { font-size: 22px; margin: 0 0 10px; }
    p { color: #94A3B8; font-size: 14px; margin: 0 0 24px; line-height: 1.5; }
    .btn {
      display: inline-block;
      background: #6366F1;
      color: #FFFFFF;
      padding: 12px 24px;
      border-radius: 10px;
      text-decoration: none;
      font-weight: 600;
      font-size: 14px;
      margin: 6px;
      transition: background 0.2s;
    }
    .btn-secondary {
      background: #1E2030;
      border: 1px solid #2E324D;
      color: #E2E8F0;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge"><span class="dot"></span>API Server Online</div>
    <h1>TalentAI Backend API</h1>
    <p>Django REST Backend is running smoothly on port 8000.<br>Redirecting to Web Application in 2 seconds...</p>
    <a href="http://localhost:3000" class="btn">Open Web App (localhost:3000) ↗</a>
    <a href="/admin/" class="btn btn-secondary">Admin Portal</a>
  </div>
</body>
</html>"""
    return HttpResponse(html_content, content_type='text/html')

urlpatterns = [
    path('', root_api_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/candidates/', include('candidates.urls')),
    path('api/companies/', include('companies.urls')),
    path('api/recruiters/', include('recruiters.urls')),
    path('api/recruiter/', include('recruiters.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/resumes/', include('resumes.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/interviews/', include('interviews.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/ai/', include('ai_services.urls')),
    path('api/admin/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
