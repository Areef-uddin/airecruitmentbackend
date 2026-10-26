from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse

def root_api_view(request):
    # If API client or json requested, return JSON status
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'status': 'online',
            'service': 'TalentAI Recruitment Backend API',
            'version': '1.0.0',
            'environment': 'Production (Render)',
            'endpoints': {
                'admin': '/admin/',
                'auth': '/api/auth/',
                'jobs': '/api/jobs/',
                'candidates': '/api/candidates/',
                'companies': '/api/companies/',
                'applications': '/api/applications/',
                'interviews': '/api/interviews/',
                'ai': '/api/ai/',
            }
        })

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TalentAI Backend API • Online</title>
  <style>
    body {
      background: #080B11;
      color: #FFFFFF;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      box-sizing: border-box;
    }
    .card {
      background: #111422;
      border: 1px solid #232842;
      border-radius: 18px;
      padding: 38px 42px;
      text-align: center;
      max-width: 520px;
      width: 100%;
      box-shadow: 0 16px 50px rgba(0,0,0,0.6);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #10B981;
      padding: 5px 14px;
      border-radius: 100px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
      margin-bottom: 18px;
    }
    .dot {
      width: 8px;
      height: 8px;
      background: #10B981;
      border-radius: 50%;
      margin-right: 8px;
      box-shadow: 0 0 10px #10B981;
    }
    h1 {
      font-size: 24px;
      font-weight: 800;
      margin: 0 0 10px;
      background: linear-gradient(135deg, #FFFFFF, #94A3B8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p {
      color: #94A3B8;
      font-size: 14px;
      margin: 0 0 24px;
      line-height: 1.6;
    }
    .endpoints {
      background: #0B0D17;
      border: 1px solid #1D2138;
      border-radius: 12px;
      padding: 14px 18px;
      margin-bottom: 24px;
      text-align: left;
      font-family: monospace;
      font-size: 12px;
      color: #CBD5E1;
    }
    .endpoints div { margin-bottom: 6px; }
    .endpoints span { color: #8B5CF6; font-weight: bold; }
    .btn {
      display: inline-block;
      background: #8B5CF6;
      color: #FFFFFF;
      padding: 11px 22px;
      border-radius: 10px;
      text-decoration: none;
      font-weight: 600;
      font-size: 13px;
      margin: 4px;
      transition: background 0.2s, transform 0.1s;
    }
    .btn:hover { background: #7C3AED; }
    .btn-secondary {
      background: #1A1D2F;
      border: 1px solid #2B3150;
      color: #E2E8F0;
    }
    .btn-secondary:hover { background: #232840; }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge"><span class="dot"></span>API SERVICE HEALTHY & ONLINE</div>
    <h1>TalentAI Backend API</h1>
    <p>Django REST Framework API is running live on Render connected to PostgreSQL database.</p>
    <div class="endpoints">
      <div><span>GET</span> /api/jobs/ • Public Job Listings</div>
      <div><span>POST</span> /api/auth/login/ • User Authentication</div>
      <div><span>GET</span> /api/candidates/me/ • Candidate Profile</div>
      <div><span>GET</span> /api/interviews/ • Video Interviews</div>
      <div><span>GET</span> /admin/ • Django Administration</div>
    </div>
    <a href="/admin/" class="btn">Django Admin Portal</a>
    <a href="/?format=json" class="btn btn-secondary">JSON Health Check</a>
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
