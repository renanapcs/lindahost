"""
URL configuration for lindahost project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/auth/', include('rest_framework.urls')),
    path('api/deployments/create', views.create_deployment, name='create_deployment'),
    path('api/deployments/list', views.list_deployments, name='list_deployments'),
    path('api/domains/register', views.register_domain, name='register_domain'),
    path('api/webhook/pix', views.pix_webhook, name='pix_webhook'),
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('admin/aws-integration', views.aws_integration, name='aws_integration'),
    path('admin/cloudflare-integration', views.cloudflare_integration, name='cloudflare_integration'),
    path('admin/test-aws-connection', views.test_aws_connection, name='test_aws_connection'),
    path('admin/test-cloudflare-connection', views.test_cloudflare_connection, name='test_cloudflare_connection'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
