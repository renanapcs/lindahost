import json
import requests
import boto3
import time
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def deploy_to_cloudflare_pages(deployment, cloudflare_config):
    """
    Implementa site estático no Cloudflare Pages
    """
    try:
        # Configurar headers para API do Cloudflare
        headers = {
            'Authorization': f'Bearer {cloudflare_config.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Extrair informações do repositório GitHub
        github_parts = deployment.github_url.rstrip('/').split('/')
        username = github_parts[-2]
        repo_name = github_parts[-1]
        
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # Nome do projeto no Cloudflare
        project_name = f"{deployment.name}-{deployment.id}"[:100]
        
        # Dados para criar o projeto
        project_data = {
            'name': project_name,
            'production_branch': deployment.branch,
            'build_config': {
                'build_command': deployment.build_command or 'npm run build',
                'destination_dir': deployment.output_directory
            },
            'source': {
                'type': 'github',
                'config': {
                    'owner': username,
                    'repo_name': repo_name,
                    'production_branch': deployment.branch,
                    'pr_comments_enabled': True
                }
            }
        }
        
        # Criar projeto no Cloudflare Pages
        create_response = requests.post(
            f'https://api.cloudflare.com/client/v4/accounts/{cloudflare_config.account_id}/pages/projects',
            headers=headers,
            json=project_data,
            timeout=30
        )
        
        if create_response.status_code not in [200, 201]:
            return False, f"Erro ao criar projeto: {create_response.text}"
        
        project_result = create_response.json()
        
        # Iniciar deploy
        deploy_response = requests.post(
            f'https://api.cloudflare.com/client/v4/accounts/{cloudflare_config.account_id}/pages/projects/{project_name}/deployments',
            headers=headers,
            json={'production': True},
            timeout=30
        )
        
        if deploy_response.status_code not in [200, 201]:
            return False, f"Erro ao iniciar deploy: {deploy_response.text}"
        
        deploy_result = deploy_response.json()
        
        # Aguardar conclusão do deploy
        deployment_id = deploy_result['result']['id']
        deployment_status = deploy_result['result']['status']
        
        max_checks = 30  # 30 tentativas com intervalo de 5 segundos
        checks = 0
        
        while deployment_status not in ['success', 'failed'] and checks < max_checks:
            time.sleep(5)
            status_response = requests.get(
                f'https://api.cloudflare.com/client/v4/accounts/{cloudflare_config.account_id}/pages/projects/{project_name}/deployments/{deployment_id}',
                headers=headers,
                timeout=30
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                deployment_status = status_result['result']['status']
            checks += 1
        
        if deployment_status == 'success':
            deployment_url = f"https://{deploy_result['result']['url']}"
            return True, {
                'url': deployment_url,
                'project_name': project_name,
                'deployment_id': deployment_id
            }
        else:
            return False, f"Deploy falhou com status: {deployment_status}"
    
    except Exception as e:
        return False, str(e)

def deploy_to_captain(deployment, server):
    """
    Implementa o código no CapRover
    """
    try:
        headers = {
            'x-namespace': 'captain',
            'Content-Type': 'application/json',
            'x-captain-auth': server.api_key
        }
        
        github_parts = deployment.github_url.rstrip('/').split('/')
        username = github_parts[-2]
        repo_name = github_parts[-1]
        
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        app_name = f"deploy-{deployment.id}"[:30]
        
        data = {
            'appName': app_name,
            'hasPersistentData': False,
            'description': f"Deployment for {deployment.name}",
            'instanceCount': 1,
            'caproverExtra': {
                'containerHttpPort': '80'
            },
            'envVars': [
                {
                    'key': 'APP_NAME',
                    'value': deployment.name
                }
            ],
            'notExposeAsWebApp': False,
            'forceSsl': True,
            'websocketSupport': False,
            'appDeployTokenConfig': {
                'enabled': True,
                'deployToken': f"token-{deployment.id}"
            },
            'appDeploySource': {
                'type': 'git',
                'gitRepository': deployment.github_url,
                'gitBranch': deployment.branch,
                'user': username,
                'password': '',
                'sshKey': server.ssh_key
            }
        }
        
        # Criar aplicação no CapRover
        create_response = requests.post(
            f"{server.url}/api/v2/user/apps/appDefinitions/register",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if create_response.status_code != 200:
            return False, f"Erro ao criar app no CapRover: {create_response.text}"
        
        # Iniciar deploy
        deploy_data = {
            'appName': app_name,
            'deployToken': f"token-{deployment.id}"
        }
        
        deploy_response = requests.post(
            f"{server.url}/api/v2/user/apps/appDefinitions/deploy",
            json=deploy_data,
            headers=headers,
            timeout=30
        )
        
        if deploy_response.status_code == 200:
            return True, {
                'url': f'https://{app_name}.{server.url.replace("https://", "").replace("http://", "")}'
            }
        else:
            return False, f"Erro no deploy: {deploy_response.text}"
    
    except Exception as e:
        return False, str(e)

def deploy_to_aws_ecs(deployment, aws_config):
    """
    Implementa container na AWS ECS como backup
    """
    try:
        session = boto3.Session(
            aws_access_key_id=aws_config.aws_access_key_id,
            aws_secret_access_key=aws_config.aws_secret_access_key,
            region_name=aws_config.aws_region
        )
        
        ecs = session.client('ecs')
        
        # Nome do serviço/task baseado no ID do deployment
        service_name = f"deployment-{deployment.id}"
        
        # Verificar se o cluster existe
        clusters = ecs.list_clusters()
        cluster_arn = None
        
        for cluster in clusters['clusterArns']:
            if aws_config.ecs_cluster_name in cluster:
                cluster_arn = cluster
                break
        
        if not cluster_arn:
            # Criar cluster se não existir
            cluster_response = ecs.create_cluster(
                clusterName=aws_config.ecs_cluster_name
            )
            cluster_arn = cluster_response['cluster']['clusterArn']
        
        # Registrar task definition (simplificado)
        task_def_response = ecs.register_task_definition(
            family=service_name,
            networkMode='awsvpc',
            requiresCompatibilities=['FARGATE'],
            cpu='256',
            memory='512',
            executionRoleArn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
            containerDefinitions=[
                {
                    'name': service_name,
                    'image': 'nginx:alpine',  # Imagem padrão - substituir pela sua
                    'portMappings': [
                        {
                            'containerPort': 80,
                            'protocol': 'tcp'
                        }
                    ],
                    'essential': True,
                    'environment': [
                        {'name': 'APP_NAME', 'value': deployment.name}
                    ]
                }
            ]
        )
        
        task_def_arn = task_def_response['taskDefinition']['taskDefinitionArn']
        
        # Criar serviço
        service_response = ecs.create_service(
            cluster=aws_config.ecs_cluster_name,
            serviceName=service_name,
            taskDefinition=task_def_arn,
            desiredCount=1,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [],  # Preencher com suas subnets
                    'securityGroups': [],  # Preencher com seus security groups
                    'assignPublicIp': 'ENABLED'
                }
            }
        )
        
        # Aqui você precisaria configurar um Application Load Balancer
        # e atualizar o DNS para apontar para o ALB
        
        return True, {
            'url': f'http://{service_name}.elb.{aws_config.aws_region}.amazonaws.com'  # URL exemplo
        }
    
    except Exception as e:
        return False, str(e)

def setup_cloudflare_dns(domain, deployment, cloudflare_config):
    """
    Configura DNS no Cloudflare para um domínio personalizado
    """
    try:
        headers = {
            'Authorization': f'Bearer {cloudflare_config.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Verificar se já existe uma zona para o domínio
        zone_name = '.'.join(domain.name.split('.')[-2:])  # Extrair domínio principal
        
        zones_response = requests.get(
            f'https://api.cloudflare.com/client/v4/zones?name={zone_name}',
            headers=headers,
            timeout=30
        )
        
        if zones_response.status_code != 200:
            return False, f"Erro ao buscar zonas: {zones_response.text}"
        
        zones_data = zones_response.json()
        
        if zones_data['result'] and len(zones_data['result']) > 0:
            zone_id = zones_data['result'][0]['id']
        else:
            # Criar nova zona se não existir
            create_zone_data = {
                'name': zone_name,
                'jump_start': True
            }
            
            create_zone_response = requests.post(
                'https://api.cloudflare.com/client/v4/zones',
                headers=headers,
                json=create_zone_data,
                timeout=30
            )
            
            if create_zone_response.status_code != 200:
                return False, f"Erro ao criar zona: {create_zone_response.text}"
            
            zone_id = create_zone_response.json()['result']['id']
        
        # Criar registro DNS
        dns_data = {
            'type': 'CNAME',
            'name': domain.name,
            'content': deployment.url.replace('https://', '').replace('http://', ''),
            'proxied': True,
            'ttl': 1  # TTL automático com proxy
        }
        
        dns_response = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
            headers=headers,
            json=dns_data,
            timeout=30
        )
        
        if dns_response.status_code != 200:
            return False, f"Erro ao criar registro DNS: {dns_response.text}"
        
        dns_result = dns_response.json()
        
        return True, {
            'zone_id': zone_id,
            'dns_record_id': dns_result['result']['id']
        }
    
    except Exception as e:
        return False, str(e)

def generate_pix_code(amount, reference):
    """
    Gera um código PIX usando um gateway de pagamento
    """
    # Implementação simulada - substituir por integração real com gateway PIX
    pix_code = f"00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-4266554400005204000053039865406{amount:.2f}5802BR5913FIBRA10TEC6008Sao Paulo62070503***6304"
    
    # Calcular expiração (24 horas a partir de agora)
    expiration = timezone.now() + timedelta(hours=24)
    
    return pix_code, expiration

def generate_html_with_deepseek(site_info):
    """
    Gera HTML automaticamente usando a API do DeepSeek
    """
    try:
        # Configurar headers para API do DeepSeek
        headers = {
            'Authorization': 'Bearer sk-your-deepseek-api-key',  # Substituir pela chave real
            'Content-Type': 'application/json'
        }
        
        # Preparar prompt para geração do HTML
        prompt = f"""
        Crie um site HTML moderno e responsivo para uma empresa/pessoa com as seguintes informações:

        Nome do Site: {site_info.site_name}
        Tipo: {site_info.get_site_type_display()}
        Descrição: {site_info.description}
        Empresa/Pessoa: {site_info.company_name}
        Email: {site_info.contact_email}
        Telefone: {site_info.contact_phone or 'Não informado'}
        Endereço: {site_info.address or 'Não informado'}
        
        Redes Sociais:
        - Website: {site_info.website_url or 'Não informado'}
        - Facebook: {site_info.facebook_url or 'Não informado'}
        - Instagram: {site_info.instagram_url or 'Não informado'}
        - LinkedIn: {site_info.linkedin_url or 'Não informado'}
        - Twitter: {site_info.twitter_url or 'Não informado'}
        
        Serviços/Produtos:
        {site_info.services or 'Não informado'}
        
        Palavras-chave: {site_info.keywords or 'Não informado'}
        
        Configurações de Design:
        - Cor Primária: {site_info.primary_color}
        - Cor Secundária: {site_info.secondary_color}
        - Fonte: {site_info.font_family}
        
        Instruções:
        1. Crie um site moderno, responsivo e profissional
        2. Use Bootstrap 5 para responsividade
        3. Inclua seções: Header, Hero, Sobre, Serviços, Contato, Footer
        4. Use as cores especificadas no design
        5. Torne o site otimizado para SEO
        6. Inclua meta tags apropriadas
        7. Use ícones do Bootstrap Icons
        8. Torne o site acessível e rápido
        9. Inclua formulário de contato funcional
        10. Use gradientes e animações sutis
        
        Retorne apenas o código HTML completo, sem explicações adicionais.
        """
        
        # Dados para enviar para a API
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # Fazer requisição para a API do DeepSeek
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_html = result['choices'][0]['message']['content']
            
            # Limpar o HTML gerado (remover markdown se presente)
            if generated_html.startswith('```html'):
                generated_html = generated_html[7:]
            if generated_html.endswith('```'):
                generated_html = generated_html[:-3]
            
            generated_html = generated_html.strip()
            
            return True, generated_html
        else:
            return False, f"Erro na API do DeepSeek: {response.text}"
    
    except Exception as e:
        return False, f"Erro ao gerar HTML: {str(e)}"

def generate_css_with_deepseek(site_info):
    """
    Gera CSS personalizado usando a API do DeepSeek
    """
    try:
        headers = {
            'Authorization': 'Bearer sk-your-deepseek-api-key',  # Substituir pela chave real
            'Content-Type': 'application/json'
        }
        
        prompt = f"""
        Crie um arquivo CSS moderno e responsivo para complementar o site HTML gerado.
        
        Configurações de Design:
        - Cor Primária: {site_info.primary_color}
        - Cor Secundária: {site_info.secondary_color}
        - Fonte: {site_info.font_family}
        
        Instruções:
        1. Crie estilos modernos e profissionais
        2. Use CSS Grid e Flexbox para layouts
        3. Inclua animações sutis e transições suaves
        4. Torne o design responsivo para mobile
        5. Use as cores especificadas como variáveis CSS
        6. Inclua estilos para formulários, botões e cards
        7. Adicione efeitos hover e focus
        8. Otimize para performance
        9. Use gradientes e sombras modernas
        10. Inclua estilos para seções: hero, sobre, serviços, contato
        
        Retorne apenas o código CSS completo, sem explicações adicionais.
        """
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_css = result['choices'][0]['message']['content']
            
            # Limpar o CSS gerado
            if generated_css.startswith('```css'):
                generated_css = generated_css[6:]
            if generated_css.endswith('```'):
                generated_css = generated_css[:-3]
            
            generated_css = generated_css.strip()
            
            return True, generated_css
        else:
            return False, f"Erro na API do DeepSeek: {response.text}"
    
    except Exception as e:
        return False, f"Erro ao gerar CSS: {str(e)}"