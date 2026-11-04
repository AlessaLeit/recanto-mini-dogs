# Backup do banco de dados

Scripts que fazem backup diário do banco, guardam cópias em mais de um lugar e conferem toda semana se os backups continuam restaurando.

| Arquivo | Para que serve |
|---|---|
| `backup.ps1` | Gera o backup, confere se ele é íntegro, copia para os destinos e apaga os antigos |
| `restaurar.ps1` | Restaura um backup — com modo de teste que não toca nos dados reais |
| `agendar.ps1` | Cria as tarefas automáticas no Agendador do Windows (rodar uma vez) |
| `backup.config.example.json` | Modelo da configuração |

## Por que mais de uma cópia

Os dados do sistema ficam num volume do Docker, dentro do disco virtual do Docker Desktop. Eles se perdem se:

- o disco da máquina falhar (comum em computadores antigos);
- alguém usar **"Clean / Purge data"** ou **"Reset to factory defaults"** no Docker Desktop, ou desinstalá-lo;
- a máquina for roubada, ou houver incêndio ou alagamento.

Por isso cada backup vai para três lugares: a pasta local, a nuvem (Google Drive ou OneDrive) e, se estiver conectado, um HD externo.

---

## Instalação (uma vez, na máquina onde o sistema roda)

### 1. Docker Desktop abrindo com o Windows

No Docker Desktop: **Settings → General → "Start Docker Desktop when you sign in"**. O script de backup tenta abrir o Docker se ele estiver fechado, mas é melhor que já esteja aberto.

### 2. Pasta sincronizada com a nuvem

**Google Drive:** instale o [Google Drive para computador](https://www.google.com/drive/download/) e entre com a conta. Ele cria uma unidade, normalmente `G:\Meu Drive`. Confira no Explorador de Arquivos qual letra apareceu.

**OneDrive:** já vem no Windows. A pasta costuma ser `C:\Users\<usuário>\OneDrive`.

> Coloque na nuvem **apenas os arquivos de backup**. Nunca sincronize a pasta de dados do Postgres ou do Docker: o sincronizador mexe nos arquivos enquanto o banco está gravando e os corrompe.

Os backups contêm dados pessoais dos clientes. **Ative a verificação em duas etapas** na conta do Google/Microsoft usada para isso.

### 3. Configuração

Copie `backup.config.example.json` para `backup.config.json` (na mesma pasta) e ajuste:

```json
{
  "pastaLocal": "C:\\RecantoBackups",
  "destinos": [
    "G:\\Meu Drive\\Backups Recanto Mini Dogs",
    "E:\\Backups Recanto Mini Dogs"
  ],
  "manterDiarios": 30,
  "manterMensais": 12
}
```

| Campo | Significado |
|---|---|
| `pastaLocal` | Onde o backup é gerado primeiro. Também guarda os logs |
| `destinos` | Pastas que recebem uma cópia. Pode ter quantas quiser |
| `manterDiarios` | Quantos backups recentes manter (30 = último mês) |
| `manterMensais` | Além desses, mantém o último backup de cada mês, até esse número de meses |

Dois detalhes:

- No JSON, toda barra invertida é **dupla**: `C:\\RecantoBackups`.
- Um destino numa unidade desconectada (o HD externo fora da USB) **não é erro**: o script avisa no log e segue com os outros.

Para usar o OneDrive no lugar do Google Drive, basta trocar o caminho. Nada mais muda.

### 4. Testar manualmente

Abra o PowerShell **nesta pasta** e rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\backup.ps1
powershell -ExecutionPolicy Bypass -File .\restaurar.ps1 -Teste
```

O primeiro deve terminar com `Backup concluído com sucesso`. O segundo restaura o backup num banco temporário e mostra uma tabela com a quantidade de registros "No backup" e "Hoje", que devem bater.

### 5. Agendar

```powershell
powershell -ExecutionPolicy Bypass -File .\agendar.ps1
```

Isso cria duas tarefas no Agendador de Tarefas do Windows:

- **Backup diário** às 18h (mude com `-Horario 17:30`);
- **Teste de restauração** toda segunda ao meio-dia (mude com `-HorarioTeste 13:00`).

Se o computador estiver desligado no horário, a tarefa roda assim que ele for ligado. Para remover as tarefas: `.\agendar.ps1 -Remover`.

---

## No dia a dia

**O backup está rodando?** Abra `C:\RecantoBackups\ultimo_backup_ok.txt`: mostra a data do último backup que deu certo. O histórico completo fica em `backup.log`. Também dá para conferir pelo site do Google Drive se os arquivos novos estão chegando.

Vale olhar isso uma vez por semana. Backup automático que parou de rodar em silêncio é o tipo de problema que só aparece quando já é tarde.

---

## Recuperar os dados

### Voltar a um backup na mesma máquina

```powershell
powershell -ExecutionPolicy Bypass -File .\restaurar.ps1 -Arquivo "G:\Meu Drive\Backups Recanto Mini Dogs\recanto_2026-10-20_1800.dump"
```

O script pede para digitar `RESTAURAR` e, **antes de trocar os dados**, faz um backup de segurança do estado atual (`pre-restauracao_*.dump` na pasta local). Se o backup escolhido for o errado, é só restaurar esse arquivo de segurança. O backend é parado durante a troca e volta sozinho no final.

Sem `-Arquivo`, ele usa o backup mais recente da pasta local.

### Máquina nova (a antiga quebrou)

1. Instale o Docker Desktop e o sistema normalmente (`docker compose up -d`), com um `.env` configurado.
2. Instale o Google Drive e espere os backups sincronizarem.
3. Crie o `backup.config.json` e restaure o backup mais recente, como acima.

O `.env` antigo **não** é necessário para recuperar os dados: a restauração funciona numa instalação nova com senhas novas. Mesmo assim, vale guardar uma cópia dele num lugar seguro (um gerenciador de senhas, por exemplo) para reinstalar com o mesmo login e a mesma chave do WhatsApp.

## O que o backup não cobre

- **Sessão do WhatsApp:** depois de reinstalar, basta ler o QR Code de novo na tela de WhatsApp.
- **Código do sistema:** fica no GitHub.
