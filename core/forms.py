from django import forms
from .models import AWSIntegration, CloudflareIntegration

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