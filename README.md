# Sistema de Gestão de Banho & Tosa
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=AlessaLeit_recanto-mini-dogs&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=AlessaLeit_recanto-mini-dogs)
[![CI](https://github.com/AlessaLeit/recanto-mini-dogs/actions/workflows/ci.yml/badge.svg)](https://github.com/AlessaLeit/recanto-mini-dogs/actions/workflows/ci.yml)

Sistema completo para gerenciamento de pacotes mensais de banho e tosa, controle de clientes/pets, agendamentos e relatórios financeiros.

---

## Telas do Sistema

> As imagens abaixo foram geradas com dados fictícios, criados só para ilustração.

### Agenda

Painel inicial com os indicadores do período, calendário de banhos e os agendamentos do dia selecionado. Abaixo ficam os pacotes que se encerram na data, os que estão em aberto e os atrasados.

![Agenda](docs/screenshots/agenda.png)

### Histórico do cliente

Todos os pacotes do cliente, do mais recente ao mais antigo. Cada bloco lista as datas de banho com o valor de cada dia, fecha com o total e, à direita, mostra os pagamentos recebidos e quanto falta quitar. No topo fica o crédito disponível — pagamento adiantado que entra sozinho no próximo pacote criado.

![Histórico do cliente](docs/screenshots/cliente-historico.png)

### Pacotes

![Pacotes](docs/screenshots/pacotes.png)

### Clientes

![Clientes](docs/screenshots/clientes.png)

### Relatório mensal

Receita prevista, recebida e pendente do mês, com taxa de recebimento e a relação de pacotes em aberto.

![Relatórios](docs/screenshots/relatorios.png)

### Comandas para impressão

Fila dos pacotes fechados de clientes que recebem a comanda em papel. O PDF sai com quatro comandas por folha A4.

![Comandas](docs/screenshots/comandas.png)

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic |
| **Frontend** | Vue 3, Vite, Pinia, Vue Router, Axios |
| **Banco de Dados** | SQLite (desenvolvimento) / PostgreSQL (produção) |
| **Infraestrutura** | Docker, Docker Compose, Nginx |
| **Testes** | pytest, FastAPI TestClient |

---

## Funcionalidades Principais

### 1. Clientes e Pets
- Cadastro de clientes com nome, WhatsApp, endereço e preferência de recebimento da comanda (WhatsApp ou impressa)
- Vários cachorros por cliente, com raça, porte e observações
- Busca de clientes
- **Histórico do cliente:** todos os pacotes, do mais recente ao mais antigo, com as datas de banho e o valor de cada dia, o total do pacote, os pagamentos recebidos e quanto falta quitar

### 2. Pacotes Mensais
- Planos Semanal (4 banhos), Quinzenal (2) ou Mensal (1), com dia da semana fixo
- Agendamentos do mês gerados automaticamente ao criar o pacote
- **Pacotes com mais de um cachorro** da mesma família, com valor de banho próprio para cada pet
- Valor de transporte por pacote
- **Fechamento automático:** quando todos os banhos do ciclo são resolvidos, o pacote fecha, a comanda é enviada e o pacote do mês seguinte é criado sozinho
- Status de pagamento: em aberto, parcial, pago ou atrasado (cliente iniciou um pacote novo sem quitar o anterior)

### 3. Pagamentos e Crédito
- Vários pagamentos por pacote, cada um com sua forma (Pix, dinheiro, débito, crédito)
- **Pagamento adiantado:** o valor fica guardado como crédito do cliente
- **Sobra vira crédito:** pagando mais do que o pacote custa, a diferença fica guardada em vez de se perder dentro do pacote
- O crédito entra sozinho como pagamento no próximo pacote criado, preservando forma e data originais; se for maior que o pacote, o restante fica para o mês seguinte
- Aviso ao registrar adiantamento para cliente com saldo em aberto, para evitar confundir com a baixa de um pacote antigo esquecido

### 4. Agenda
- Calendário mensal e agendamentos do dia, separados por turno (manhã e tarde)
- Presença de cada banho: pendente, concluído ou faltou
- **Presença por pet:** num pacote com dois cachorros, um pode faltar e o outro não, e só os presentes são cobrados
- Itens extras e observações por banho, com valor adicional
- Pacotes que se encerram na data selecionada, pacotes em aberto e pacotes atrasados
- Indicadores filtráveis por dia, semana, mês, ano ou período

### 5. Banhos Avulsos
- Banhos sem pacote, para clientes eventuais, com valor e controle de pagamento próprios

### 6. Comandas
- **Por WhatsApp:** enviada automaticamente ao fechar o pacote, via Evolution API (conexão pelo QR Code na tela de WhatsApp)
- **Impressa:** fila dos pacotes fechados e geração de PDF com quatro comandas por folha A4, no modelo do talão do canil

### 7. Relatórios
- Relatório mensal com banhos realizados, receita prevista, recebida e pendente
- Taxa de recebimento e lista de pacotes em aberto, com o WhatsApp do cliente

### 8. Segurança e Dados
- Acesso por login, com todas as rotas da API exigindo autenticação
- [Backup automático](scripts/backup/LEIAME.md) diário com cópia na nuvem e teste semanal de restauração

---

## Pré-requisitos

- **Python** 3.10+
- **Node.js** 18+
- **Docker** e Docker Compose (opcional, para produção)

---

## Como Executar

### Opção 1: Windows — Start com 1 Clique

Execute o arquivo `start.bat` na raiz do projeto:

```batch
.\start.bat
```

O que o script faz:
1. Cria virtual environment Python (se não existir)
2. Instala dependências do backend
3. Inicia o backend FastAPI em `http://localhost:8000`
4. Instala dependências do frontend (se necessário)
5. Inicia o frontend Vue em `http://localhost:5173`

Acesse:
- **Aplicação:** http://localhost:5173
- **Documentação da API:** http://localhost:8000/docs

---

### Opção 2: Manual (qualquer SO)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (em outro terminal):**
```bash
cd frontend
npm install
npm run dev
```

---

### Opção 3: Docker (Produção)

```bash
# Configure as variáveis de ambiente no arquivo .env
docker-compose up -d
```

Serviços levantados:
- PostgreSQL na porta 5432
- Backend FastAPI na porta 8000
- Frontend Nginx na porta 80

---

## Configuração

Crie um arquivo `backend/.env` com as seguintes variáveis:

### Desenvolvimento (SQLite)
```env
DATABASE_URL=sqlite:///./banho_tosa.db
DEBUG=True
```

### Produção (PostgreSQL via Docker)
```env
DATABASE_URL=postgresql://postgres:senha@postgres_local:5432/pacotesbanho
DEBUG=False
```

**Variáveis do Docker Compose:**
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=senha
POSTGRES_DB=pacotesbanho
BACKEND_PORT=8000
```

---

## Backup dos dados

O sistema roda localmente, então os dados dependem do disco da máquina. A pasta [`scripts/backup`](scripts/backup/LEIAME.md) tem o backup diário automático, com cópias na nuvem (Google Drive ou OneDrive) e em HD externo, rotação dos arquivos antigos e um teste semanal que confirma que os backups restauram. O passo a passo de instalação está no [LEIAME](scripts/backup/LEIAME.md).

---

## Estrutura do Projeto

```
PacotesBanho/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── main.py          # Ponto de entrada
│   │   ├── database.py      # Configuração SQLAlchemy
│   │   ├── models/          # Modelos ORM
│   │   ├── routers/         # Endpoints da API
│   │   ├── schemas/         # Validação Pydantic
│   │   └── services/        # Regras de negócio
│   ├── alembic/             # Migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Aplicação Vue 3
│   ├── src/
│   │   ├── views/           # Páginas (Dashboard, Pacotes, Clientes, Relatórios)
│   │   ├── components/      # Componentes reutilizáveis
│   │   ├── stores/          # Estado Pinia
│   │   ├── api/             # Cliente HTTP
│   │   └── router/          # Rotas Vue Router
│   ├── package.json
│   └── Dockerfile
├── test/                    # Testes de integração
├── docker-compose.yml
├── start.bat                # Start 1-clique (Windows)
└── README.md
```

---

## API — Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/v1/clientes/` | Listar clientes |
| `POST` | `/api/v1/clientes/` | Criar cliente |
| `GET` | `/api/v1/cachorros/` | Listar cachorros |
| `POST` | `/api/v1/cachorros/` | Criar cachorro |
| `GET` | `/api/v1/pacotes/` | Listar pacotes |
| `POST` | `/api/v1/pacotes/` | Criar pacote (gera agendamentos) |
| `POST` | `/api/v1/pacotes/{id}/pagar` | Registrar pagamento |
| `GET` | `/api/v1/agendamentos/` | Listar agendamentos |
| `PUT` | `/api/v1/agendamentos/{id}` | Atualizar status de presença |
| `GET` | `/api/v1/agendamentos/dashboard/{data}` | Dashboard do dia |
| `GET` | `/api/v1/relatorios/mensal` | Relatório mensal |
| `GET` | `/health` | Health check |

Documentação interativa: http://localhost:8000/docs

---

## Testes

O projeto inclui testes de integração automatizados:

```bash
cd test
python run_integration.tests.py
```

Cenários testados:
- Cadastro de cliente válido e inválido
- Criação de pacote com geração automática de agendamentos
- Registro de pagamento
- Visualização de banhos no calendário
- Edição de status de presença

Para executar com pytest:
```bash
cd backend
pytest
```

---

## Autor

Desenvolvido para gestão do **Canil Recanto Mini Dogs**.

