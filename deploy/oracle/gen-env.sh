#!/usr/bin/env bash
# Gera um .env de produção com segredos aleatórios a partir do .env.example.
# Uso: ./deploy/oracle/gen-env.sh pet.seudominio.com seu@email.com
# Não imprime os segredos; leia-os depois direto do arquivo (chmod 600).
set -euo pipefail
cd "$(dirname "$0")/../.."

DOMAIN="${1:?uso: $0 <dominio> <email-admin>}"
ADMIN_EMAIL="${2:?uso: $0 <dominio> <email-admin>}"

[ -e .env ] && { echo "ERRO: .env já existe; não vou sobrescrever." >&2; exit 1; }
command -v openssl >/dev/null || { echo "ERRO: instale openssl." >&2; exit 1; }

rand() { openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c "$1"; }

umask 077
cp .env.example .env

set_var() { # set_var CHAVE VALOR
  local k="$1" v="$2"
  v="${v//\/\\}"; v="${v//&/\&}"; v="${v//|/\|}"
  sed -i "s|^${k}=.*|${k}=${v}|" .env
}

PG_USER="petshop"
PG_PASS="$(rand 32)"
PG_DB="petshop"

set_var POSTGRES_USER "$PG_USER"
set_var POSTGRES_PASSWORD "$PG_PASS"
set_var POSTGRES_DB "$PG_DB"
set_var DATABASE_URL "postgresql://${PG_USER}:${PG_PASS}@postgres_local:5432/${PG_DB}"
set_var SECRET_KEY "$(rand 64)"
set_var ADMIN_EMAIL "$ADMIN_EMAIL"
set_var ADMIN_PASSWORD "$(rand 20)"
set_var EVOLUTION_API_KEY "$(rand 40)"
set_var DEBUG "false"
set_var DOMAIN "$DOMAIN"

chmod 600 .env
echo ".env criado (permissão 600). Veja a senha do admin com:  grep ADMIN_PASSWORD .env"
