# Guia de Contribuição - LindaHost

Obrigado por considerar contribuir com o LindaHost! Este documento fornece diretrizes para contribuir com o projeto.

## 🚀 Como Contribuir

### 1. Fork e Clone

1. Faça um fork do repositório
2. Clone seu fork localmente:
   ```bash
   git clone https://github.com/SEU_USUARIO/lindahost.git
   cd lindahost
   ```

### 2. Configuração do Ambiente

1. Crie um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

### 3. Desenvolvimento

1. Crie uma branch para sua feature:
   ```bash
   git checkout -b feature/nome-da-feature
   ```

2. Faça suas alterações seguindo as convenções do projeto

3. Execute os testes (quando disponíveis):
   ```bash
   python manage.py test
   ```

4. Execute as migrações se necessário:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### 4. Commit e Push

1. Adicione suas alterações:
   ```bash
   git add .
   ```

2. Faça commit com uma mensagem descritiva:
   ```bash
   git commit -m "feat: adiciona nova funcionalidade X"
   ```

3. Push para sua branch:
   ```bash
   git push origin feature/nome-da-feature
   ```

### 5. Pull Request

1. Abra um Pull Request no GitHub
2. Descreva suas alterações detalhadamente
3. Aguarde a revisão da equipe

## 📋 Convenções

### Commits

Use o padrão [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `style:` formatação
- `refactor:` refatoração
- `test:` testes
- `chore:` tarefas de manutenção

### Código

- Use Python 3.8+
- Siga o PEP 8 para estilo de código
- Use type hints quando possível
- Documente funções e classes importantes
- Escreva testes para novas funcionalidades

### Django

- Use nomes descritivos para modelos e campos
- Adicione `__str__` methods nos modelos
- Use migrations para alterações no banco
- Configure admin.py para novos modelos

## 🐛 Reportando Bugs

1. Verifique se o bug já foi reportado
2. Use o template de issue do GitHub
3. Inclua:
   - Descrição detalhada
   - Passos para reproduzir
   - Ambiente (OS, Python, Django versões)
   - Logs de erro (se houver)

## 💡 Sugerindo Melhorias

1. Verifique se a melhoria já foi sugerida
2. Descreva claramente o problema
3. Explique sua solução proposta
4. Considere implementar você mesmo se possível

## 🔒 Segurança

Para reportar vulnerabilidades de segurança:

1. **NÃO** abra uma issue pública
2. Envie um email para: security@lindahost.com
3. Aguarde resposta antes de divulgar

## 📞 Suporte

- GitHub Issues: Para bugs e melhorias
- Discord: [Servidor LindaHost](https://discord.gg/lindahost)
- Email: suporte@lindahost.com

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a licença MIT.

---

Obrigado por contribuir com o LindaHost! 🚀