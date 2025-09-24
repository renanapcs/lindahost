from django.contrib import admin
from .models import User, Server, AWSIntegration, CloudflareIntegration, Deployment, Domain, Invoice, SiteInfo

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'company', 'credit', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'company']
    ordering = ['-date_joined']

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'role', 'is_active', 'current_usage', 'max_containers']
    list_filter = ['type', 'role', 'is_active']
    search_fields = ['name', 'url']

@admin.register(AWSIntegration)
class AWSIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'aws_region', 'ecs_cluster_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'aws_region']
    search_fields = ['name', 'aws_region']

@admin.register(CloudflareIntegration)
class CloudflareIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_id', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'account_id']

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'deploy_type', 'status', 'url', 'created_at']
    list_filter = ['deploy_type', 'status', 'created_at']
    search_fields = ['name', 'user__username', 'github_url']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'owner', 'price', 'registered_at']
    list_filter = ['status', 'auto_renew']
    search_fields = ['name', 'owner__username']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'description', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['id', 'created_at']

@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'user', 'site_type', 'company_name', 'is_generated', 'created_at']
    list_filter = ['site_type', 'is_generated', 'created_at']
    search_fields = ['site_name', 'company_name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'generation_date']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('site_name', 'site_type', 'description', 'keywords')
        }),
        ('Informações da Empresa', {
            'fields': ('company_name', 'contact_email', 'contact_phone', 'address')
        }),
        ('Redes Sociais', {
            'fields': ('website_url', 'facebook_url', 'instagram_url', 'linkedin_url', 'twitter_url')
        }),
        ('Serviços/Produtos', {
            'fields': ('services',)
        }),
        ('Design', {
            'fields': ('primary_color', 'secondary_color', 'font_family')
        }),
        ('Conteúdo Gerado', {
            'fields': ('generated_html', 'generated_css', 'is_generated', 'generation_date'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('id', 'user', 'deployment', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
