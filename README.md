# 🚀 Banho & Tosa - Pet Shop Manager (Simplificado)

## 🎯 O que é
Sistema completo **Backend Python/FastAPI + Frontend Vue.js** para gerenciar:
- 👤 Clientes
- 🐶 Cachorros  
- 📦 Pacotes mensais (banho/tosa)
- 🛁 Banhos realizados
- 💰 Pagamentos e relatórios

## ✅ Instalação Ultra-Simples (Windows Native)

**Pré-requisitos:**
```
- Python 3.10+ 
- Node.js 18+
```

**🚀 1-CLIQUE para Rodar

**🔧 Configuração Banco (.env):**
- **Local (start.bat):** SQLite automático em `backend/banho_tosa.db` (✅ sem Docker)
- **Docker:** Descomente PostgreSQL em `backend/.env`

Exemplo `backend/.env`:
```env
DATABASE_URL=sqlite:///./banho_tosa.db
# Para Docker: postgresql://postgres:senha@db:5432/pacotesbanho
DEBUG=True
```

```bash
# No diretório do projeto
.\start.bat
```

**O que acontece:**
- Backend FastAPI → http://localhost:8000 (API + /docs)
- Frontend Vue → http://localhost:5173 (UI completa)

## 🔌 Como funciona a conexão
```
Frontend (5173) → Proxy Vite → Backend (8000/api/v1)
✅ Sem CORS errors, puro proxy local
```

## 📱 Funcionalidades
```
✅ CRUD Completo: Clientes → Cachorros → Pacotes → Banhos
✅ Pacotes abertos/faturados
✅ Dashboard + Relatórios
✅ SQLite automático (sem config)
```

## 🛠️ Comandos Avançados

**Somente Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Somente Frontend:**
```bash
cd frontend  
npm install
npm run dev
```

**Docs API:**
http://localhost:8000/docs (Swagger)

**Build Prod:**
```bash
# Backend
cd backend && alembic upgrade head  # Se Postgres

# Frontend  
cd frontend && npm run build
```

## 🐳 Docker (Opcional - Produção)
```bash
docker-compose up -d  # Postgres + Backend + Frontend Nginx
```

## 📈 Estrutura
```
PacotesBanho/
├── backend/         # FastAPI + SQLite
├── frontend/        # Vue3 + Vite + Pinia
├── start.bat        # 1-Clique Magic ✨
└── README.md        # Você está aqui!
```

## 🤔 Problemas?
```
❌ Backend não inicia → pip install -r backend/requirements.txt
❌ Frontend erro API → Verifique start.bat (backend primeiro)
❌ Porta ocupada → Mate processos 8000/5173
```

**🧪 Teste Rápido da API (PowerShell):**
```powershell
python -c "import requests; r=requests.get('http://localhost:8000/api/v1/clientes'); print(r.json()[:1])"
```

**Problemas comuns resolvidos:**
```
❌ Porta 8000 ocupada → taskkill /F /IM uvicorn.exe
❌ Frontend não conecta → start.bat (backend primeiro!)
❌ "DB não conectado" → DB funcionando, teste API acima
```

**Feito para funcionar em 30s!** 🎉


---
*Simplificado por BLACKBOXAI*

Para usar:

start.bat
http://localhost:5173 (frontend)
http://localhost:8000/docs (API)