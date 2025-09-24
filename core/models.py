import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from encrypted_model_fields.fields import EncryptedCharField

class User(AbstractUser):
    CLIENT = 'client'
    ADMIN = 'admin'
    STAFF = 'staff'
    ROLE_CHOICES = [
        (CLIENT, 'Cliente'),
        (ADMIN, 'Administrador'),
        (STAFF, 'Equipe'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CLIENT)
    company = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

class Server(models.Model):
    CAPROVER = 'caprover'
    AWS_ECS = 'aws_ecs'
    TYPE_CHOICES = [
        (CAPROVER, 'CapRover'),
        (AWS_ECS, 'AWS ECS'),
    ]
    
    PRIMARY = 'primary'
    BACKUP = 'backup'
    ROLE_CHOICES = [
        (PRIMARY, 'Primário'),
        (BACKUP, 'Backup'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=CAPROVER)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=PRIMARY)
    url = models.URLField(validators=[URLValidator()])
    api_key = EncryptedCharField(max_length=200)
    ssh_key = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    max_containers = models.IntegerField(default=10)
    current_usage = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()} - {self.get_role_display()})"
    
    def can_accept_deployment(self):
        return self.current_usage < self.max_containers

class AWSIntegration(models.Model):
    name = models.CharField(max_length=100, default="Configuração AWS Principal")
    aws_access_key_id = EncryptedCharField(max_length=100)
    aws_secret_access_key = EncryptedCharField(max_length=100)
    aws_region = models.CharField(max_length=50, default='us-east-1')
    ecs_cluster_name = models.CharField(max_length=100, default='caprover-backup')
    ssh_private_key = models.TextField(blank=True, null=True)
    ssh_public_key = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.aws_region}"

class CloudflareIntegration(models.Model):
    name = models.CharField(max_length=100, default="Configuração Cloudflare Principal")
    api_token = EncryptedCharField(max_length=200)
    account_id = models.CharField(max_length=100)
    default_zone_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.account_id}"

class Deployment(models.Model):
    STATIC = 'static'
    CONTAINER = 'container'
    DEPLOY_TYPE_CHOICES = [
        (STATIC, 'Estático (Cloudflare)'),
        (CONTAINER, 'Container (CapRover/AWS)'),
    ]
    
    PENDING = 'pending'
    BUILDING = 'building'
    SUCCESS = 'success'
    FAILED = 'failed'
    STATUS_CHOICES = [
        (PENDING, 'Pendente'),
        (BUILDING, 'Construindo'),
        (SUCCESS, 'Sucesso'),
        (FAILED, 'Falhou'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deployments')
    name = models.CharField(max_length=100)
    deploy_type = models.CharField(max_length=10, choices=DEPLOY_TYPE_CHOICES, default=CONTAINER)
    github_url = models.URLField(validators=[URLValidator()])
    branch = models.CharField(max_length=100, default='main')
    build_command = models.CharField(max_length=200, blank=True, null=True)
    output_directory = models.CharField(max_length=100, default='dist')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    url = models.URLField(blank=True, null=True)
    custom_domain = models.ForeignKey('Domain', on_delete=models.SET_NULL, null=True, blank=True, related_name='deployment_set')
    server = models.ForeignKey(Server, on_delete=models.SET_NULL, null=True, blank=True)
    cloudflare_project_name = models.CharField(max_length=100, blank=True, null=True)
    cloudflare_deployment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Domain(models.Model):
    AVAILABLE = 'available'
    PENDING = 'pending'
    REGISTERED = 'registered'
    LINKED = 'linked'
    STATUS_CHOICES = [
        (AVAILABLE, 'Disponível'),
        (PENDING, 'Pendente'),
        (REGISTERED, 'Registrado'),
        (LINKED, 'Vinculado'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=AVAILABLE)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='domains')
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True, blank=True, related_name='domains')
    cloudflare_zone_id = models.CharField(max_length=100, blank=True, null=True)
    cloudflare_dns_record_id = models.CharField(max_length=100, blank=True, null=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    auto_renew = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Invoice(models.Model):
    PENDING = 'pending'
    PAID = 'paid'
    CANCELED = 'canceled'
    STATUS_CHOICES = [
        (PENDING, 'Pendente'),
        (PAID, 'Pago'),
        (CANCELED, 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    pix_code = models.TextField(blank=True, null=True)
    pix_expiration = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.user.username}"

class SiteInfo(models.Model):
    """Modelo para armazenar informações do site para geração automática"""
    
    BUSINESS = 'business'
    PORTFOLIO = 'portfolio'
    BLOG = 'blog'
    ECOMMERCE = 'ecommerce'
    LANDING = 'landing'
    TYPE_CHOICES = [
        (BUSINESS, 'Site Empresarial'),
        (PORTFOLIO, 'Portfólio'),
        (BLOG, 'Blog'),
        (ECOMMERCE, 'E-commerce'),
        (LANDING, 'Landing Page'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='site_infos')
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='site_info', null=True, blank=True)
    
    # Informações básicas
    site_name = models.CharField(max_length=200, verbose_name="Nome do Site")
    site_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=BUSINESS, verbose_name="Tipo de Site")
    description = models.TextField(verbose_name="Descrição")
    keywords = models.TextField(blank=True, null=True, verbose_name="Palavras-chave (separadas por vírgula)")
    
    # Informações da empresa/pessoa
    company_name = models.CharField(max_length=200, verbose_name="Nome da Empresa/Pessoa")
    contact_email = models.EmailField(verbose_name="Email de Contato")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")
    
    # Redes sociais
    website_url = models.URLField(blank=True, null=True, verbose_name="Website")
    facebook_url = models.URLField(blank=True, null=True, verbose_name="Facebook")
    instagram_url = models.URLField(blank=True, null=True, verbose_name="Instagram")
    linkedin_url = models.URLField(blank=True, null=True, verbose_name="LinkedIn")
    twitter_url = models.URLField(blank=True, null=True, verbose_name="Twitter")
    
    # Serviços/Produtos
    services = models.TextField(blank=True, null=True, verbose_name="Serviços/Produtos (um por linha)")
    
    # Configurações de design
    primary_color = models.CharField(max_length=7, default="#0d6efd", verbose_name="Cor Primária")
    secondary_color = models.CharField(max_length=7, default="#6c757d", verbose_name="Cor Secundária")
    font_family = models.CharField(max_length=100, default="Inter", verbose_name="Fonte")
    
    # Conteúdo gerado
    generated_html = models.TextField(blank=True, null=True, verbose_name="HTML Gerado")
    generated_css = models.TextField(blank=True, null=True, verbose_name="CSS Gerado")
    
    # Status
    is_generated = models.BooleanField(default=False, verbose_name="HTML Gerado")
    generation_date = models.DateTimeField(blank=True, null=True, verbose_name="Data de Geração")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Informação do Site"
        verbose_name_plural = "Informações dos Sites"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.site_name} - {self.user.username}"