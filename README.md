# Inventory Flow

**Plataforma multioperador para contagem, validação e reconciliação de inventário físico.**

Inventory Flow é uma aplicação full stack desenvolvida para operações de inventário físico e demonstração em portfólio. O sistema reúne snapshot de catálogo, bipagem por SKU/EAN, controle de concorrência entre operadores, validação de divergências, filas de recontagem, histórico de auditoria, controle de acesso por perfil, exportação para Excel e uma camada de integração com ERP.

> Este repositório utiliza exclusivamente dados sintéticos de demonstração. Nenhum nome de empresa, catálogo privado, quantidade real de estoque, dado de usuário, URL de produção ou credencial está incluído.

## Por que este projeto existe

Inventários controlados por planilhas se tornam frágeis quando várias pessoas contam ao mesmo tempo. Operadores podem duplicar trabalho, sobrescrever informações, perder o controle das ruas já conferidas e gerar recontagens ambíguas.

O Inventory Flow transforma esse processo em um fluxo operacional controlado, com responsáveis definidos, bloqueios concorrentes e reconciliação determinística.

```text
Sincronização do catálogo
        ↓
Snapshot imutável
        ↓
Contagem multioperador por rua
        ↓
Validação
        ↓
Diferença = Contagem Física - Estoque do Sistema
        ↓
OK / FALTA / SOBRA
        ↓
Recontagem opcional com SKU reservado
        ↓
Resolução final + histórico de auditoria
```

## Stack tecnológica

- **Frontend:** Next.js 16, React 19, TypeScript
- **Backend:** FastAPI, Python 3.12
- **Persistência:** SQLAlchemy; SQLite para demonstração sem configuração e URL compatível com PostgreSQL/Supabase para ambientes hospedados
- **Autenticação:** sessões opacas gerenciadas no servidor com cookies HttpOnly
- **Autorização:** permissões RBAC validadas no backend
- **Camada ERP:** provedor sintético de demonstração + provedor opcional Bling via OAuth 2.0
- **Exportações:** OpenPyXL
- **Deploy:** Docker, serviço único e uma única URL pública

## Principais recursos

- Visão geral responsiva com progresso do inventário.
- Snapshot imutável do inventário antes do início da contagem.
- Bipagem física por rua usando SKU ou EAN.
- Reserva multioperador com heartbeat e TTL.
- Restauração da rua ativa e da sessão de recontagem após F5.
- Validação determinística: `contagem física - snapshot do sistema`.
- Classificação automática das divergências como falta ou sobra.
- Fila de recontagem com um SKU reservado para uma única sessão de navegador por vez.
- Fluxo opcional de **Próximo item**, sem loop automático.
- Aprovação manual de divergências para exceções supervisionadas.
- Trilha de auditoria e consulta ao histórico de inventários.
- Exportação da validação para Excel.
- Administração de usuários e permissões.
- Módulo de **Integrações** exclusivo para administradores, com metadados seguros do banco de dados, status do ERP, métricas e histórico de sincronização.
- Cenários de demonstração que levam diretamente aos estados de Bipagem, Validação ou Recontagem.
- Implementação OAuth 2.0 do Bling mantida separada do provedor público de demonstração.

## Contas de demonstração

Na primeira inicialização, a aplicação cria estes usuários fictícios:

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Administrador | `admin@inventoryflow.demo` | `Demo123!` |
| Supervisor | `supervisor@inventoryflow.demo` | `Demo123!` |
| Operador | `operator@inventoryflow.demo` | `Demo123!` |

Para a demonstração pública, mantenha:

```env
ALLOW_EXTERNAL_CONNECTIONS=false
```

## Permissões

| Módulo | Operador | Supervisor | Administrador |
| --- | :---: | :---: | :---: |
| Visão geral | ✓ | ✓ | ✓ |
| Preparar inventário |  | ✓ | ✓ |
| Bipagem | ✓ | ✓ | ✓ |
| Validação |  | ✓ | ✓ |
| Recontagem | ✓ | ✓ | ✓ |
| Histórico |  | ✓ | ✓ |
| Usuários |  |  | ✓ |
| Integrações |  |  | ✓ |

As permissões são armazenadas por usuário e verificadas por dependências do FastAPI. Ocultar uma opção de menu no frontend não é considerado uma barreira de autorização.

## Base de demonstração

O gerador de seed cria **420 produtos fictícios distribuídos em 18 ruas de estoque**. Nomes de produtos, marcas, identificadores semelhantes a EAN, localizações e quantidades são valores sintéticos e determinísticos gerados em tempo de execução.

A tela **Integrações** oferece três cenários:

- **Bipagem:** várias ruas já estão finalizadas e as restantes podem ser reservadas e contadas.
- **Validação:** todas as ruas estão finalizadas e o snapshot contém faltas e sobras deliberadas.
- **Recontagem:** SKUs divergentes selecionados já estão inseridos na fila de recontagem multioperador.

Isso permite demonstrar o sistema sem precisar concluir manualmente centenas de bipagens.

## Configuração local — Windows PowerShell

### 1. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

O banco de dados padrão é SQLite e não exige configuração externa.

### 2. Frontend

Abra outro terminal:

```powershell
cd frontend
npm install
npm run build
```

Copie a exportação estática para o FastAPI:

```powershell
Remove-Item -Recurse -Force ..\backend\static -ErrorAction SilentlyContinue
Copy-Item -Recurse .\out ..\backend\static
```

### 3. Executar

```powershell
cd ..\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 10000 --reload
```

Abra:

```text
http://127.0.0.1:10000
```

A documentação da API está disponível em:

```text
http://127.0.0.1:10000/api/docs
```

## Banco PostgreSQL / compatível com Supabase

Altere apenas a variável de ambiente:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
```

A aplicação cria as tabelas na inicialização. O arquivo `database/schema.sql` está incluído como referência legível do schema principal.

## Provedores ERP

### Provedor de demonstração

Configuração padrão:

```env
ERP_PROVIDER=demo
ALLOW_EXTERNAL_CONNECTIONS=false
```

Esse provedor carrega o catálogo sintético de produtos e é seguro para um deploy público de portfólio.

### Provedor Bling

O adaptador do Bling é opcional e nenhuma credencial real é armazenada neste repositório.

```env
ERP_PROVIDER=demo
ALLOW_EXTERNAL_CONNECTIONS=true
BLING_CLIENT_ID=
BLING_CLIENT_SECRET=
BLING_REDIRECT_URI=http://127.0.0.1:10000/api/v1/integrations/bling/callback
TOKEN_ENCRYPTION_KEY=
```

Para gerar uma chave Fernet:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Quando configurada, a tela **Integrações** pode iniciar o fluxo OAuth. Os tokens de acesso e renovação são criptografados antes de serem persistidos.

Para uma demonstração pública, mantenha as conexões externas desativadas.

## Modelo de concorrência

A tabela genérica `resource_locks` protege o trabalho operacional:

```text
BIPAGEM
inventário + rua + usuário + sessão do navegador + expires_at

RECONTAGEM
inventário + SKU + usuário + sessão do navegador + expires_at
```

A mesma sessão de navegador pode renovar o próprio bloqueio após um F5. Outro operador ou outra sessão recebe HTTP `409` até que a reserva seja liberada explicitamente ou expire por inatividade.

## Destaques de segurança

- Hash de senhas com PBKDF2-HMAC-SHA256 e salt individual por usuário.
- Sessões de autenticação opacas persistidas no servidor.
- Cookies de sessão HttpOnly e SameSite.
- Verificação de permissões no backend em todas as rotas protegidas.
- Nenhum segredo de ERP ou senha de banco de dados é retornado ao navegador.
- OAuth externo desativado por padrão em ambientes de demonstração.
- Tokens OAuth externos criptografados com Fernet quando a integração está habilitada.
- Script de verificação do repositório procura referências a marcas privadas e padrões de credenciais.

Consulte [`docs/security.md`](docs/security.md) para mais detalhes.

## Testes

Na raiz do projeto, com as dependências do backend instaladas:

```powershell
$env:PYTHONPATH="backend"
pytest -q
python scripts\verify_portfolio.py
```

Os testes de integração cobrem:

- fórmula de reconciliação;
- geração do seed sintético e visão geral;
- cenário de validação;
- idempotência da reserva de rua após recarregar a página;
- prevenção de colisão entre operadores;
- reserva de recontagem por SKU;
- retorno de uma recontagem ainda divergente para Validação.

## Docker

```bash
docker build -t inventoryflow .
docker run --rm -p 10000:10000 inventoryflow
```

Ou:

```bash
docker compose up --build
```

## Render

O arquivo `render.yaml` está incluído para um deploy Docker em serviço único. O frontend Next.js compilado é copiado para a imagem do FastAPI, permitindo que a demonstração utilize uma única URL pública.

Para uma demonstração de portfólio, o SQLite embutido é suficiente porque o estado sintético pode ser recriado. Para histórico persistente em ambiente hospedado, configure uma `DATABASE_URL` PostgreSQL no serviço de hospedagem.

## Estrutura do projeto

```text
inventoryflow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   └── services/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
├── database/
├── docs/
├── scripts/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── render.yaml
└── README.md
```

## Decisões de arquitetura

A edição de portfólio remove intencionalmente ajustes operacionais específicos de uma empresa. A reconciliação principal é universal: um snapshot do estoque do sistema é comparado com a contagem física.

Ajustes específicos de domínio podem ser adicionados posteriormente como políticas independentes, sem alterar os mecanismos de bipagem, concorrência e recontagem.

O acesso ao ERP é abstraído por uma camada de provedores. A aplicação pública continua totalmente demonstrável sem qualquer conta de terceiros, enquanto a base de código preserva uma integração OAuth com um ERP real.

## Licença

Este projeto foi desenvolvido para demonstração técnica, portfólio e avaliação educacional. O uso, reprodução ou distribuição deve respeitar a licença definida para este repositório.
