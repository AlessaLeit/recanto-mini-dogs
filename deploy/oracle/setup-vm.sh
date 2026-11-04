#!/usr/bin/env bash
# Endurece uma VM Ubuntu da Oracle Cloud e instala o Docker.
# Rode UMA vez, como usuário normal com sudo (ex.: ubuntu), via SSH com CHAVE:
#   sudo -v && ./deploy/oracle/setup-vm.sh
# ATENÇÃO: desativa login SSH por senha. O script confere se há chave
# autorizada antes, para não te trancar fora.
set -euo pipefail

[ "$(id -u)" -ne 0 ] || { echo "Rode como usuário normal (com sudo), não como root." >&2; exit 1; }

if [ ! -s "$HOME/.ssh/authorized_keys" ]; then
  echo "ERRO: $HOME/.ssh/authorized_keys vazio. Configure a chave SSH antes (senão você perde o acesso)." >&2
  exit 1
fi

echo ">> Atualizando pacotes e ativando atualizações automáticas de segurança"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  unattended-upgrades fail2ban iptables-persistent curl ca-certificates openssl
echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";' | sudo tee /etc/apt/apt.conf.d/20auto-upgrades >/dev/null

echo ">> Endurecendo o SSH (somente chave, sem root)"
sudo tee /etc/ssh/sshd_config.d/99-hardening.conf >/dev/null <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
MaxAuthTries 3
X11Forwarding no
CONF
sudo sshd -t
sudo systemctl reload ssh || sudo systemctl reload sshd

echo ">> fail2ban para SSH"
sudo tee /etc/fail2ban/jail.d/sshd.local >/dev/null <<'CONF'
[sshd]
enabled = true
maxretry = 4
findtime = 10m
bantime = 1h
CONF
sudo systemctl enable --now fail2ban
sudo systemctl restart fail2ban

echo ">> Firewall do host (iptables): libera apenas 22, 80 e 443"
# As imagens Ubuntu da Oracle já vêm com regras em INPUT terminando em REJECT;
# inserimos 80/443 antes dele (idempotente).
for porta in 80 443; do
  sudo iptables -C INPUT -p tcp --dport "$porta" -m conntrack --ctstate NEW -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT 6 -p tcp --dport "$porta" -m conntrack --ctstate NEW -j ACCEPT
done
sudo netfilter-persistent save

echo ">> Instalando Docker"
if ! command -v docker >/dev/null; then
  sudo apt-get install -y docker.io docker-compose-v2 || {
    echo "Pacote docker-compose-v2 indisponível nesta versão do Ubuntu; instale o Docker pela doc oficial." >&2; exit 1; }
  sudo systemctl enable --now docker
fi
sudo usermod -aG docker "$USER"

cat <<'MSG'

Pronto. Falta fazer MANUALMENTE no console da Oracle:
  1. Networking > VCN > Security List (ou NSG): ingress TCP 80 e 443 de 0.0.0.0/0.
     NÃO abra 5432, 8000 nem 8080.
  2. Aponte o DNS do domínio para o IP público da VM.
Saia e entre de novo no SSH (para o grupo docker valer) e siga deploy/oracle/README.md.
MSG
