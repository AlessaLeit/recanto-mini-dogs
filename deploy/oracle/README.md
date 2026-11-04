# Deploy seguro na Oracle Cloud (Always Free)

Arquitetura: internet → **Caddy** (HTTPS automático, 80/443) → **nginx** do frontend
(cabeçalhos de segurança + limite de tentativas de login) → **backend** FastAPI →
**Postgres**. Postgres, Evolution API e backend **não** são publicados na internet.

## 0. Antes de começar
- Crie a VM (Ubuntu 22.04/24.04). Se escolher a **Ampere A1 (ARM)**, as imagens
  `alessaleit/pacotesbanho-*` precisam ser publicadas **multi-arch**
  (`linux/amd64,linux/arm64`), senão o container não sobe. Ex. no `docker buildx`:
  `docker buildx build --platform linux/amd64,linux/arm64 -t <imagem> --push .`
- Tenha um domínio (ou um gratuito do DuckDNS) apontando para o IP público da VM.
- **Rebuilde e publique as imagens** do backend e do frontend: as mudanças de
  segurança (autenticação em todas as rotas, nginx.conf) vivem dentro delas.

## 1. Console da Oracle
Na Security List/NSG da VCN, libere ingress TCP **80** e **443** (0.0.0.0/0), além do 22.
Não abra 5432, 8000 nem 8080.

## 2. Na VM
```bash
git clone <seu-repo> pacotesbanho && cd pacotesbanho
./deploy/oracle/setup-vm.sh          # SSH só com chave, fail2ban, firewall, updates, Docker
# saia e entre de novo no SSH
./deploy/oracle/gen-env.sh pet.seudominio.com voce@email.com   # gera .env com segredos aleatórios
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
curl -fsS http://127.0.0.1:8000/health
```
Senha do admin: `grep ADMIN_PASSWORD .env` (guarde num gerenciador de senhas).
O backend recusa subir em produção com `SECRET_KEY` < 32 ou senha de admin < 12 caracteres.

## 3. Contas de acesso (painel oculto)
Acesse `https://SEU_DOMINIO/ale_admin_canil` e entre com a **chave de administração**, que é o
`ADMIN_PASSWORD` do `.env` (`grep ADMIN_PASSWORD .env`). Lá você cria contas, altera senhas
(isso encerra as sessões abertas da conta), desativa ou exclui. A página não tem link no menu.
Na primeira subida, a conta inicial é criada a partir de `ADMIN_EMAIL`/`ADMIN_PASSWORD`;
depois disso o login usa a tabela `usuarios` (senhas em Argon2). Trocar a senha de uma conta
no painel **não** muda a chave de administração; para mudá-la, edite `ADMIN_PASSWORD` no `.env`
e reinicie o backend.

## 4. Backup (obrigatório)
```bash
( crontab -l 2>/dev/null; echo "0 3 * * * $PWD/deploy/oracle/backup.sh >> $PWD/backups/backup.log 2>&1" ) | crontab -
```
Copie `backups/` para fora da VM de vez em quando (ex.: `rclone`). Teste a restauração
uma vez: `gunzip -c backups/pg_X.sql.gz | docker exec -i postgres_db psql -U <POSTGRES_USER> postgres`.

## 5. Manutenção
- Atualizar: `git pull && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d`
- Atualizações do SO são automáticas (unattended-upgrades); reinicie a VM de vez em quando.
- Nunca commite o `.env`. Se vazar, rode `gen-env.sh` de novo (num `.env` removido) e troque tudo.

## O que já está protegido
| Camada | Medida |
|---|---|
| API | Todas as rotas (exceto login e `/health`) exigem JWT; `/docs` desligado em produção; CORS restrito; login com comparação em tempo constante |
| Config | Em produção, recusa segredos fracos ou `DEBUG=true` |
| nginx | 5 tentativas/min por IP no login (429), rate limit geral, CSP, X-Frame-Options, nosniff, sem versão do servidor |
| HTTPS | Caddy com Let's Encrypt + HSTS |
| Containers | `no-new-privileges`, `cap_drop: ALL`, usuário não-root, sem portas de BD/API públicas |
| VM | SSH só por chave, fail2ban, firewall, atualizações automáticas |

## Limitações conhecidas
- A URL `/ale_admin_canil` não é segredo: quem protege é a chave de administração (com limite de 5 tentativas/min por IP). Use uma chave longa.
- O token JWT fica no `localStorage` do navegador (vale 12 h); um XSS no frontend o expõe — a CSP reduz esse risco.
- `evoapicloud/evolution-api:latest` não está fixada numa versão: fixe uma tag testada.
- Não testei estes arquivos numa VM real nem o `nginx -t` (Docker local estava desligado).
