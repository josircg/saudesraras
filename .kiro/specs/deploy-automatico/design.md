# Design Document

## Overview

O deploy automático executa o script shell versionado (`deploy.sh`) concentra todos os passos de atualização, e a view `system_update` apenas o invoca e exibe o resultado. Isso resolve três problemas do fluxo atual: (1) a captura incorreta da saída dos management commands, (2) o reinício do serviço que mata o próprio request, e (3) a lógica de deploy espalhada e frágil dentro da view. O deploy é sempre **local** (mesmo host do Django), então nenhuma ferramenta de execução remota (Fabric/SSH) é necessária.

Este documento descreve o estado atual e o alvo da mudança.

## Architecture

### Estado atual (in-process)
```
GET /system_update/  (sem auth — @staff_member_required comentado)
   ▼
system_update (utils/views.py)
   ├── os_run('git pull', cwd=BASE_DIR)
   ├── os_run('git pull', cwd=BASE_DIR/tema)
   ├── call_command('collectstatic')   → retorna None → log += None  ✗ TypeError
   ├── call_command('migrate')         → retorna None
   └── os_run('supervisorctl restart <serviço>')  ← mata o worker no request
```

### Alvo (Opção B — script versionado)
```
GET /system_update/  (@staff_member_required ativo)
   ▼
system_update (utils/views.py)
   └── os_run('bash deploy.sh', cwd=BASE_DIR)   # captura stdout/stderr e código de saída
          │
          ▼
      deploy.sh  (set -euo pipefail)
          1. git pull                       (raiz do projeto)
          2. git pull                       (tema/, se existir)
          3. $VENV/bin/python manage.py migrate
          4. $VENV/bin/python manage.py collectstatic --noinput
          5. restart assíncrono do serviço  (nohup/at/setsid, para não derrubar o request)
   ▼
render deploy.html (log + mensagem de sucesso/erro conforme código de saída)
```

## Components and Interfaces

### `deploy.sh` (novo, versionado na raiz do projeto)
- **Contrato**: executa os passos em ordem, aborta no primeiro erro (`set -e`), imprime cada passo no stdout e retorna código de saída != 0 em falha.
- **Parametrização**: lê caminhos de variáveis de ambiente com defaults derivados — `PROJECT_DIR` (default `BASE_DIR`), `VENV_DIR` (ex.: `/var/webapp/saudesraras`), `SUPERVISOR_SERVICE` (default `saudesraras`). Evita valores fixos de um único servidor (Requisito 5.5).
- **Reinício desacoplado**: o restart do supervisor é disparado de forma que não bloqueie nem derrube o processo que respondeu ao request — por exemplo `setsid`/`nohup ... &` ou `at now`, agendando o restart para logo após o script retornar.
- **Tema opcional**: só roda `git pull` em `tema/` se o diretório existir (consistente com o settings, que condiciona o app `tema` à existência da pasta).

### `system_update(request)` (refatorada, `utils/views.py`)
- Reativa `@staff_member_required`.
- Invoca `deploy.sh` via `os_run` com `cwd=BASE_DIR`, capturando saída e tratando erro.
- Monta o log a partir da saída do script (não mais da concatenação do retorno dos management commands).
- Mantém o template `deploy.html` como superfície de exibição.

### `os_run` (`utils/apps.py`) — reuso
- Continua sendo o executor. Para invocar o script, passar o comando como **lista** (`['bash', 'deploy.sh']`) evita a fragilidade do `split(" ")`.

### `execute_deploy_tema` — consolidação
- Deve passar a reutilizar o `deploy.sh` (ou um subconjunto parametrizado dele) em vez de duplicar `git pull` do tema + `collectstatic`. O bloco de código Fabric comentado pode ser removido.

## Data Models

Não há modelos de dados envolvidos. As dependências são de ambiente/sistema:

| Elemento | Papel |
|---|---|
| `settings.BASE_DIR` | Raiz do projeto; `cwd` do `git pull` e do script |
| `settings.DEBUG` | Gate do reinício do serviço |
| venv | Python/pip que executam migrate/collectstatic que será calculado pela view |
| supervisor (`saudesraras`) | Serviço reiniciado ao final |
| submódulo `tema/` | Repositório de tema com `git pull` próprio (opcional) |

## Correctness Properties

Invariantes do fluxo de deploy:

- **Acesso restrito**: o deploy só é disparável por usuário de staff autenticado.
- **Fonte única de verdade dos passos**: a sequência de deploy existe em um único lugar (`deploy.sh`); a view não reimplementa os passos.
- **Falha para cedo**: qualquer passo que falhe aborta o deploy; passos seguintes não executam sobre um estado inconsistente.
- **Resposta antes do restart**: o reinício do serviço nunca impede o envio da resposta HTTP do deploy que o disparou.
- **DEBUG não reinicia**: em ambiente de desenvolvimento, o serviço não é reiniciado.
- **Tema condicional**: o `git pull` do tema só ocorre quando `tema/` existe.
- **Saída fiel**: o log exibido reflete a saída real dos passos, sem erro de concatenação de `None`.

## Error Handling
- `deploy.sh` usa `set -euo pipefail`: aborta no primeiro erro e propaga código de saída.
- `os_run` captura stdout/stderr e, com `halt=True`, levanta `ValidationError` em código != 0; a view trata e exibe o passo que falhou.
- O reinício assíncrono não deve mascarar falhas dos passos anteriores: o restart só é agendado se os passos 1–4 tiverem sucesso.
- A view diferencia sucesso (mensagem + log) de falha (mensagem de erro + saída de erro no log).

## Design Decisions and Trade-offs
- **Script shell versionado vs. lógica in-process**: o script é reutilizável (manual, cron, webhook), testável fora do request e mantém a view magra. Trade-off: introduz um artefato shell a manter, dependente do SO do servidor (aceitável, pois o deploy é local e o alvo é Linux).
- **Reinício assíncrono**: resolve o worker morto no request, ao custo de o resultado do restart não ser capturado no mesmo log (o script retorna antes de o restart concluir). Aceitável: o sucesso dos passos de atualização é o que importa para a resposta.
- **Parametrização por variáveis de ambiente**: evita fixar caminhos de um servidor específico; permite usar o mesmo script em teste e produção.
- **Fabric mantido para outros fins**: `fabfile.py` continua útil para backup e para deploys genuinamente remotos (ex.: `deploy_iesp`); a mudança remove apenas a *necessidade* do Fabric no caminho local do `system_update`.

## Testing Strategy

- **Teste da view**: mockar `os_run` e verificar que `system_update` invoca `deploy.sh` com `cwd=BASE_DIR`, exige staff, e monta o log a partir da saída (sucesso e falha).
- **Teste do gate de DEBUG**: confirmar que o passo de restart não é incluído em `DEBUG`.
- **Teste do script** (fora do Django): rodar `deploy.sh` num checkout de teste com um serviço supervisor fictício, validando `set -e` (aborta no primeiro erro) e o restart desacoplado.
- **Teste de regressão do bug de concatenação**: garantir que a captura da saída dos management commands não lança `TypeError`.
- **Isolamento**: nenhum teste deve executar `git pull`/`migrate`/restart reais; usar mocks e um diretório temporário.
