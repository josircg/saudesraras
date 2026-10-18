# Requirements Document

## Introduction

O deploy automático atualiza a aplicação Odorico no próprio servidor onde o Django está rodando, a partir de um disparo pela web (view `system_update`). O fluxo atualiza o código (`git pull` do projeto e do submódulo `tema/`), aplica migrações, coleta arquivos estáticos e reinicia o serviço via supervisor.

Hoje a lógica vive dentro da view `utils/views.py::system_update`, executando comandos in-process via `utils/apps.py::os_run` (subprocess). A rotina funciona parcialmente e tem bugs conhecidos. Esta spec documenta o estado atual e especifica a evolução escolhida (**Opção B**): extrair os passos para um **script shell versionado** (`deploy.sh`) que a view apenas invoca, deixando o reinício do serviço desacoplado do request HTTP e sem dependência de ferramentas externas (o Fabric deixa de ser necessário para o deploy local).

## Glossary
- **Deploy local**: atualização executada no mesmo host em que a aplicação Django está rodando (não há SSH para outro servidor)
- **`os_run`**: helper em `utils/apps.py` que executa um comando de SO via `subprocess.run`, retornando a saída ou levantando `ValidationError`
- **`tema/`**: submódulo/repositório de tema, versionado separadamente, com `git pull` próprio
- **supervisor**: gerenciador de processos que mantém o serviço `odorico`; `supervisorctl restart odorico` reinicia os workers
- **venv**: ambiente virtual Python do projeto (ex.: `odorico310`), cujo `python`/`pip` executam os management commands

## Requirements

### Requirement 1: Disparo autenticado do deploy
**User Story:** Como administrador, quero disparar o deploy pela web de forma protegida, para evitar que terceiros atualizem o sistema.

#### Acceptance Criteria
1. QUANDO a view `system_update` é acessada ENTÃO o sistema DEVE exigir autenticação de staff (`@staff_member_required`), que hoje está desabilitada.
2. QUANDO um usuário sem permissão acessa a URL ENTÃO o sistema DEVE negar o acesso.

### Requirement 2: Atualização do código-fonte
**User Story:** Como administrador, quero que o deploy traga a versão mais recente do código, para publicar as mudanças.

#### Acceptance Criteria
1. QUANDO o deploy executa ENTÃO o sistema DEVE rodar `git pull` na raiz do projeto (`BASE_DIR`).
2. QUANDO existe o submódulo `tema/` ENTÃO o sistema DEVE rodar `git pull` também em `tema/`.
3. QUANDO um `git pull` falha ENTÃO o deploy DEVE parar e reportar o passo que falhou.

### Requirement 3: Migrações e arquivos estáticos
**User Story:** Como administrador, quero que o banco e os estáticos fiquem consistentes com o código novo.

#### Acceptance Criteria
1. QUANDO o código é atualizado ENTÃO o sistema DEVE aplicar `migrate` com o Python do venv do projeto.
2. QUANDO o código é atualizado ENTÃO o sistema DEVE executar `collectstatic --noinput`.
3. QUANDO qualquer um desses passos falha ENTÃO o deploy DEVE parar e reportar o passo que falhou.

### Requirement 4: Reinício desacoplado do serviço
**User Story:** Como administrador, quero que o reinício do serviço não derrube a resposta do próprio deploy, para receber o resultado da operação.

#### Acceptance Criteria
1. QUANDO não está em `DEBUG` ENTÃO o deploy DEVE reiniciar o serviço via supervisor (`supervisorctl restart odorico`).
2. QUANDO o reinício é disparado ENTÃO ele DEVE ocorrer de forma que o worker que atende o request consiga devolver a resposta HTTP antes de ser reiniciado (reinício assíncrono / ao final do script).
3. QUANDO está em `DEBUG` ENTÃO o sistema NÃO DEVE reiniciar o serviço.

### Requirement 5: Script de deploy versionado (Opção B)
**User Story:** Como mantenedor, quero os passos de deploy em um script versionado, para reutilizá-lo manualmente, por cron ou webhook, sem duplicar lógica na view.

#### Acceptance Criteria
1. QUANDO o deploy é executado ENTÃO os passos (git pull do projeto e do tema, migrate, collectstatic, restart) DEVEM estar em um script shell versionado no repositório (`deploy.sh`).
2. QUANDO a view `system_update` roda ENTÃO ela DEVE apenas invocar o script e capturar sua saída, sem reimplementar os passos.
3. QUANDO o script é executado ENTÃO ele DEVE usar o Python do venv do projeto para os management commands.
4. QUANDO um passo do script falha ENTÃO o script DEVE abortar imediatamente (`set -e` ou equivalente) e sinalizar erro via código de saída.
5. QUANDO o script roda ENTÃO caminhos (raiz do projeto, venv, nome do serviço supervisor) DEVEM ser parametrizáveis/derivados, não codificados de forma fixa para um único servidor.

### Requirement 6: Relato do resultado
**User Story:** Como administrador, quero ver o resultado de cada passo, para diagnosticar falhas.

#### Acceptance Criteria
1. QUANDO o deploy conclui com sucesso ENTÃO o sistema DEVE exibir mensagem de sucesso e o log acumulado dos passos.
2. QUANDO um passo falha ENTÃO o sistema DEVE exibir mensagem de erro identificando o passo e incluir a saída de erro no log.
3. QUANDO os management commands rodam ENTÃO sua saída DEVE ser capturada corretamente (sem causar erro de concatenação).

## Gaps e dívidas técnicas conhecidas (estado atual)
- `management.call_command("collectstatic"/"migrate")` **retorna `None`**; o código atual faz `log += None + '<br/>'`, o que lança `TypeError` e interrompe o fluxo — causa provável do "funcionando parcialmente".
- `@staff_member_required` está **comentado** na view: a URL de deploy está exposta sem autenticação.
- `supervisorctl restart odorico` roda **dentro do request**, podendo matar o worker antes de a resposta HTTP ser enviada.
- `os_run` faz `command.split(" ")`, frágil para caminhos/argumentos com espaços.
- O `git pull` depende de credenciais do usuário que roda o processo Django (worker do supervisor), que pode não ter chave SSH/token configurados.
- `execute_deploy_tema` duplica parte do fluxo (git pull do tema + collectstatic) e tem código Fabric comentado; convém consolidar com o `deploy.sh`.
- Não há testes automatizados do fluxo de deploy.
