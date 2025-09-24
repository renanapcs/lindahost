import json
import requests
import boto3
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Deployment, Domain, Invoice, Server, User, AWSIntegration, CloudflareIntegration, SiteInfo
from .utils import generate_pix_code, deploy_to_captain, deploy_to_aws_ecs, deploy_to_cloudflare_pages, setup_cloudflare_dns, generate_html_with_deepseek, generate_css_with_deepseek
from .forms import AWSIntegrationForm, CloudflareIntegrationForm, SiteInfoForm

def is_admin(user):
    return user.role == User.ADMIN

@login_required
@user_passes_test(is_admin)
def aws_integration(request):
    aws_config = AWSIntegration.objects.first()
    
    if request.method == 'POST':
        form = AWSIntegrationForm(request.POST, instance=aws_config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuração AWS salva com sucesso!')
            return redirect('aws_integration')
    else:
        form = AWSIntegrationForm(instance=aws_config)
    
    return render(request, 'admin/aws_integration.html', {
        'form': form,
        'aws_config': aws_config
    })

@login_required
@user_passes_test(is_admin)
def cloudflare_integration(request):
    cloudflare_config = CloudflareIntegration.objects.first()
    
    if request.method == 'POST':
        form = CloudflareIntegrationForm(request.POST, instance=cloudflare_config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuração Cloudflare salva com sucesso!')
            return redirect('cloudflare_integration')
    else:
        form = CloudflareIntegrationForm(instance=cloudflare_config)
    
    return render(request, 'admin/cloudflare_integration.html', {
        'form': form,
        'cloudflare_config': cloudflare_config
    })

@login_required
@user_passes_test(is_admin)
def test_aws_connection(request):
    aws_config = AWSIntegration.objects.first()
    
    if not aws_config:
        return JsonResponse({'success': False, 'message': 'Nenhuma configuração AWS encontrada'})
    
    try:
        session = boto3.Session(
            aws_access_key_id=aws_config.aws_access_key_id,
            aws_secret_access_key=aws_config.aws_secret_access_key,
            region_name=aws_config.aws_region
        )
        
        ec2 = session.client('ec2')
        regions = ec2.describe_regions()
        
        return JsonResponse({
            'success': True, 
            'message': f'Conexão AWS bem-sucedida na região {aws_config.aws_region}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro na conexão AWS: {str(e)}'})

@login_required
@user_passes_test(is_admin)
def test_cloudflare_connection(request):
    cloudflare_config = CloudflareIntegration.objects.first()
    
    if not cloudflare_config:
        return JsonResponse({'success': False, 'message': 'Nenhuma configuração Cloudflare encontrada'})
    
    try:
        headers = {
            'Authorization': f'Bearer {cloudflare_config.api_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'https://api.cloudflare.com/client/v4/accounts/{cloudflare_config.account_id}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return JsonResponse({
                'success': True, 
                'message': 'Conexão Cloudflare bem-sucedida'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': f'Erro na conexão Cloudflare: {response.text}'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro na conexão Cloudflare: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def create_deployment(request):
    try:
        data = json.loads(request.body)
        github_url = data.get('github_url')
        name = data.get('name')
        branch = data.get('branch', 'main')
        deploy_type = data.get('deploy_type', Deployment.CONTAINER)
        build_command = data.get('build_command')
        output_directory = data.get('output_directory', 'dist')
        custom_domain = data.get('custom_domain', None)
        
        if request.user.credit <= 0:
            return JsonResponse({'error': 'Crédito insuficiente. Por favor, adicione crédito à sua conta.'}, status=400)
        
        deployment = Deployment(
            user=request.user,
            name=name,
            github_url=github_url,
            branch=branch,
            deploy_type=deploy_type,
            build_command=build_command,
            output_directory=output_directory,
            status=Deployment.PENDING
        )
        
        if custom_domain:
            domain = Domain.objects.filter(name=custom_domain, owner=request.user).first()
            if domain:
                deployment.custom_domain = domain
        
        deployment.save()
        
        # Escolher o tipo de deploy
        if deploy_type == Deployment.STATIC:
            # Deploy estático no Cloudflare Pages
            cloudflare_config = CloudflareIntegration.objects.filter(is_active=True).first()
            
            if not cloudflare_config:
                deployment.status = Deployment.FAILED
                deployment.save()
                return JsonResponse({'error': 'Nenhuma configuração Cloudflare disponível'}, status=500)
            
            success, result = deploy_to_cloudflare_pages(deployment, cloudflare_config)
            
            if success:
                deployment.status = Deployment.SUCCESS
                deployment.url = result.get('url')
                deployment.cloudflare_project_name = result.get('project_name')
                deployment.cloudflare_deployment_id = result.get('deployment_id')
                
                # Configurar domínio personalizado se especificado
                if deployment.custom_domain:
                    domain_success, domain_result = setup_cloudflare_dns(
                        deployment.custom_domain, deployment, cloudflare_config
                    )
                    
                    if domain_success:
                        deployment.custom_domain.status = Domain.LINKED
                        deployment.custom_domain.cloudflare_zone_id = domain_result.get('zone_id')
                        deployment.custom_domain.cloudflare_dns_record_id = domain_result.get('dns_record_id')
                        deployment.custom_domain.save()
                
                # Cobrar do usuário
                request.user.credit -= 0.20  # Valor menor para sites estáticos
                request.user.save()
            else:
                deployment.status = Deployment.FAILED
        else:
            # Deploy de container - tentar primeiro no CapRover
            server = Server.objects.filter(is_active=True, type=Server.CAPROVER, role=Server.PRIMARY).first()
            
            if server and server.can_accept_deployment():
                deployment.server = server
                success, result = deploy_to_captain(deployment, server)
                
                if success:
                    deployment.status = Deployment.SUCCESS
                    deployment.url = result.get('url')
                    server.current_usage += 1
                    server.save()
                    
                    # Configurar domínio personalizado se especificado
                    if deployment.custom_domain:
                        cloudflare_config = CloudflareIntegration.objects.filter(is_active=True).first()
                        if cloudflare_config:
                            domain_success, domain_result = setup_cloudflare_dns(
                                deployment.custom_domain, deployment, cloudflare_config
                            )
                            
                            if domain_success:
                                deployment.custom_domain.status = Domain.LINKED
                                deployment.custom_domain.cloudflare_zone_id = domain_result.get('zone_id')
                                deployment.custom_domain.cloudflare_dns_record_id = domain_result.get('dns_record_id')
                                deployment.custom_domain.save()
                    
                    # Cobrar do usuário
                    request.user.credit -= 0.50
                    request.user.save()
                else:
                    deployment.status = Deployment.FAILED
                    # Tentar servidor de backup
                    backup_server = Server.objects.filter(
                        is_active=True, 
                        type=Server.AWS_ECS, 
                        role=Server.BACKUP
                    ).first()
                    
                    if backup_server and backup_server.can_accept_deployment():
                        deployment.server = backup_server
                        aws_config = AWSIntegration.objects.filter(is_active=True).first()
                        
                        if aws_config:
                            success, result = deploy_to_aws_ecs(deployment, aws_config)
                            
                            if success:
                                deployment.status = Deployment.SUCCESS
                                deployment.url = result.get('url')
                                backup_server.current_usage += 1
                                backup_server.save()
                                
                                # Cobrar do usuário
                                request.user.credit -= 0.50
                                request.user.save()
                            else:
                                deployment.status = Deployment.FAILED
            else:
                deployment.status = Deployment.FAILED
                deployment.save()
                return JsonResponse({'error': 'Nenhum servidor disponível'}, status=500)
        
        deployment.save()
        
        return JsonResponse({
            'deployment_id': str(deployment.id),
            'status': deployment.status,
            'url': deployment.url
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def list_deployments(request):
    deployments = Deployment.objects.filter(user=request.user).order_by('-created_at')
    data = [{
        'id': str(d.id),
        'name': d.name,
        'deploy_type': d.deploy_type,
        'status': d.status,
        'url': d.url,
        'created_at': d.created_at
    } for d in deployments]
    
    return JsonResponse({'deployments': data})

@login_required
@require_http_methods(["POST"])
def register_domain(request):
    try:
        data = json.loads(request.body)
        domain_name = data.get('domain_name')
        
        domain = Domain.objects.filter(name=domain_name).first()
        if domain and domain.status != Domain.AVAILABLE:
            return JsonResponse({'error': 'Domínio não disponível'}, status=400)
        
        if not domain:
            domain = Domain(name=domain_name, status=Domain.PENDING)
        else:
            domain.status = Domain.PENDING
        
        domain.owner = request.user
        domain.price = 49.90
        domain.save()
        
        invoice = Invoice(
            user=request.user,
            description=f"Registro de domínio: {domain_name}",
            amount=domain.price,
            status=Invoice.PENDING
        )
        
        pix_code, expiration = generate_pix_code(invoice.amount, f"DOMAIN_{domain_name}")
        invoice.pix_code = pix_code
        invoice.pix_expiration = expiration
        invoice.save()
        
        # Enviar email para financeiro (implementar)
        
        return JsonResponse({
            'domain_id': domain.id,
            'invoice_id': str(invoice.id),
            'pix_code': pix_code,
            'expiration': expiration
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def pix_webhook(request):
    try:
        data = json.loads(request.body)
        invoice_id = data.get('invoice_id')
        invoice = Invoice.objects.get(id=invoice_id)
        
        if data.get('status') == 'approved':
            invoice.status = Invoice.PAID
            invoice.paid_at = timezone.now()
            invoice.save()
            
            if invoice.description.startswith('Registro de domínio'):
                domain_name = invoice.description.split(': ')[1]
                domain = Domain.objects.get(name=domain_name)
                domain.status = Domain.REGISTERED
                domain.registered_at = timezone.now()
                domain.expires_at = timezone.now() + timezone.timedelta(days=365)
                domain.save()
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_deployments = Deployment.objects.count()
    total_invoices = Invoice.objects.count()
    pending_invoices = Invoice.objects.filter(status=Invoice.PENDING).count()
    active_servers = Server.objects.filter(is_active=True).count()
    
    recent_deployments = Deployment.objects.all().order_by('-created_at')[:10]
    recent_invoices = Invoice.objects.all().order_by('-created_at')[:10]
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    
    aws_config = AWSIntegration.objects.filter(is_active=True).first()
    aws_status = "Configurado" if aws_config else "Não configurado"
    
    cloudflare_config = CloudflareIntegration.objects.filter(is_active=True).first()
    cloudflare_status = "Configurado" if cloudflare_config else "Não configurado"
    
    server_status = []
    for server in Server.objects.all():
        server_status.append({
            'name': server.name,
            'type': server.get_type_display(),
            'role': server.get_role_display(),
            'usage': f"{server.current_usage}/{server.max_containers}",
            'status': 'Ativo' if server.is_active else 'Inativo'
        })
    
    return render(request, 'admin/dashboard.html', {
        'total_users': total_users,
        'total_deployments': total_deployments,
        'total_invoices': total_invoices,
        'pending_invoices': pending_invoices,
        'active_servers': active_servers,
        'recent_deployments': recent_deployments,
        'recent_invoices': recent_invoices,
        'recent_users': recent_users,
        'aws_status': aws_status,
        'cloudflare_status': cloudflare_status,
        'server_status': server_status,
        'aws_config': aws_config,
        'cloudflare_config': cloudflare_config
    })

def home(request):
    """Página inicial do sistema"""
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    """Dashboard do usuário"""
    user_deployments = Deployment.objects.filter(user=request.user).order_by('-created_at')[:5]
    user_domains = Domain.objects.filter(owner=request.user).order_by('-created_at')[:5]
    
    return render(request, 'core/dashboard.html', {
        'deployments': user_deployments,
        'domains': user_domains,
        'user': request.user
    })

@login_required
def site_info_list(request):
    """Lista todas as informações de sites do usuário"""
    site_infos = SiteInfo.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/site_info_list.html', {
        'site_infos': site_infos
    })

@login_required
def site_info_create(request):
    """Criar nova informação de site"""
    if request.method == 'POST':
        form = SiteInfoForm(request.POST)
        if form.is_valid():
            site_info = form.save(commit=False)
            site_info.user = request.user
            site_info.save()
            messages.success(request, 'Informações do site salvas com sucesso!')
            return redirect('site_info_detail', pk=site_info.pk)
    else:
        form = SiteInfoForm()
    
    return render(request, 'core/site_info_form.html', {
        'form': form,
        'title': 'Criar Informações do Site',
        'action': 'create'
    })

@login_required
def site_info_detail(request, pk):
    """Visualizar detalhes de uma informação de site"""
    site_info = get_object_or_404(SiteInfo, pk=pk, user=request.user)
    return render(request, 'core/site_info_detail.html', {
        'site_info': site_info
    })

@login_required
def site_info_edit(request, pk):
    """Editar informações de site"""
    site_info = get_object_or_404(SiteInfo, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SiteInfoForm(request.POST, instance=site_info)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informações do site atualizadas com sucesso!')
            return redirect('site_info_detail', pk=site_info.pk)
    else:
        form = SiteInfoForm(instance=site_info)
    
    return render(request, 'core/site_info_form.html', {
        'form': form,
        'site_info': site_info,
        'title': 'Editar Informações do Site',
        'action': 'edit'
    })

@login_required
@require_http_methods(["POST"])
def site_info_generate_html(request, pk):
    """Gerar HTML automaticamente usando DeepSeek"""
    site_info = get_object_or_404(SiteInfo, pk=pk, user=request.user)
    
    try:
        # Gerar HTML
        html_success, html_result = generate_html_with_deepseek(site_info)
        
        if html_success:
            # Gerar CSS
            css_success, css_result = generate_css_with_deepseek(site_info)
            
            # Salvar resultados
            site_info.generated_html = html_result
            site_info.generated_css = css_result if css_success else ""
            site_info.is_generated = True
            site_info.generation_date = timezone.now()
            site_info.save()
            
            messages.success(request, 'HTML gerado com sucesso!')
            return JsonResponse({
                'success': True,
                'message': 'HTML gerado com sucesso!',
                'html': html_result,
                'css': css_result if css_success else ""
            })
        else:
            messages.error(request, f'Erro ao gerar HTML: {html_result}')
            return JsonResponse({
                'success': False,
                'message': f'Erro ao gerar HTML: {html_result}'
            })
    
    except Exception as e:
        messages.error(request, f'Erro interno: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })

@login_required
def site_info_preview(request, pk):
    """Visualizar preview do HTML gerado"""
    site_info = get_object_or_404(SiteInfo, pk=pk, user=request.user)
    
    if not site_info.is_generated or not site_info.generated_html:
        messages.error(request, 'HTML ainda não foi gerado para este site.')
        return redirect('site_info_detail', pk=pk)
    
    return render(request, 'core/site_info_preview.html', {
        'site_info': site_info
    })

@login_required
@require_http_methods(["POST"])
def site_info_deploy(request, pk):
    """Fazer deploy do HTML gerado para um deployment"""
    site_info = get_object_or_404(SiteInfo, pk=pk, user=request.user)
    
    if not site_info.is_generated or not site_info.generated_html:
        return JsonResponse({
            'success': False,
            'message': 'HTML ainda não foi gerado para este site.'
        })
    
    try:
        # Aqui você pode implementar a lógica para fazer deploy do HTML gerado
        # Por exemplo, criar um repositório temporário ou usar um serviço de hospedagem
        
        # Por enquanto, vamos apenas retornar sucesso
        messages.success(request, 'Deploy iniciado com sucesso!')
        return JsonResponse({
            'success': True,
            'message': 'Deploy iniciado com sucesso!'
        })
    
    except Exception as e:
        messages.error(request, f'Erro no deploy: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': f'Erro no deploy: {str(e)}'
        })