from django import forms
from .models import AWSIntegration, CloudflareIntegration, SiteInfo

class AWSIntegrationForm(forms.ModelForm):
    class Meta:
        model = AWSIntegration
        fields = ['name', 'aws_access_key_id', 'aws_secret_access_key', 'aws_region', 
                 'ecs_cluster_name', 'ssh_private_key', 'ssh_public_key', 'is_active']
        widgets = {
            'aws_access_key_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AKIAIOSFODNN7EXAMPLE'}),
            'aws_secret_access_key': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'}),
            'aws_region': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('us-east-1', 'US East (N. Virginia)'),
                ('us-east-2', 'US East (Ohio)'),
                ('us-west-1', 'US West (N. California)'),
                ('us-west-2', 'US West (Oregon)'),
                ('sa-east-1', 'South America (São Paulo)'),
            ]),
            'ecs_cluster_name': forms.TextInput(attrs={'class': 'form-control'}),
            'ssh_private_key': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '-----BEGIN RSA PRIVATE KEY-----...'}),
            'ssh_public_key': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD...'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'aws_access_key_id': 'AWS Access Key ID',
            'aws_secret_access_key': 'AWS Secret Access Key',
            'ssh_private_key': 'Chave SSH Privada',
            'ssh_public_key': 'Chave SSH Pública',
        }

class CloudflareIntegrationForm(forms.ModelForm):
    class Meta:
        model = CloudflareIntegration
        fields = ['name', 'api_token', 'account_id', 'default_zone_id', 'is_active']
        widgets = {
            'api_token': forms.PasswordInput(attrs={'class': 'form-control'}),
            'account_id': forms.TextInput(attrs={'class': 'form-control'}),
            'default_zone_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'api_token': 'API Token',
            'account_id': 'Account ID',
            'default_zone_id': 'Default Zone ID (Opcional)',
        }
        help_texts = {
            'account_id': 'Encontre no painel do Cloudflare em Overview > right-hand sidebar',
            'api_token': 'Crie um token com permissões para Pages e DNS',
        }

class SiteInfoForm(forms.ModelForm):
    class Meta:
        model = SiteInfo
        fields = [
            'site_name', 'site_type', 'description', 'keywords',
            'company_name', 'contact_email', 'contact_phone', 'address',
            'website_url', 'facebook_url', 'instagram_url', 'linkedin_url', 'twitter_url',
            'services', 'primary_color', 'secondary_color', 'font_family'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Minha Empresa'
            }),
            'site_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva brevemente seu negócio ou projeto...'
            }),
            'keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'palavra1, palavra2, palavra3...'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da sua empresa ou seu nome'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contato@empresa.com'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Endereço completo da empresa'
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.empresa.com'
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/empresa'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/empresa'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/company/empresa'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/empresa'
            }),
            'services': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Liste seus serviços ou produtos principais (um por linha)'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'font_family': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('Inter', 'Inter'),
                ('Roboto', 'Roboto'),
                ('Open Sans', 'Open Sans'),
                ('Lato', 'Lato'),
                ('Montserrat', 'Montserrat'),
                ('Poppins', 'Poppins'),
            ]),
        }
        labels = {
            'site_name': 'Nome do Site',
            'site_type': 'Tipo de Site',
            'description': 'Descrição',
            'keywords': 'Palavras-chave',
            'company_name': 'Nome da Empresa/Pessoa',
            'contact_email': 'Email de Contato',
            'contact_phone': 'Telefone',
            'address': 'Endereço',
            'website_url': 'Website',
            'facebook_url': 'Facebook',
            'instagram_url': 'Instagram',
            'linkedin_url': 'LinkedIn',
            'twitter_url': 'Twitter',
            'services': 'Serviços/Produtos',
            'primary_color': 'Cor Primária',
            'secondary_color': 'Cor Secundária',
            'font_family': 'Fonte',
        }
        help_texts = {
            'keywords': 'Separe as palavras-chave por vírgula',
            'services': 'Liste um serviço ou produto por linha',
            'primary_color': 'Cor principal do site',
            'secondary_color': 'Cor secundária para detalhes',
        }