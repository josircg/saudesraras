# Implementation Plan

Correção do HTTP 500 (`RelatedObjectDoesNotExist: Resource has no creator.`) ao
adicionar `Resource`/`TrainingResource` pelo admin. Duas partes: (1) admin
preenche `creator = request.user` na criação; (2) `Resource.save()` defensivo
quanto à ausência de `creator`. Nenhuma mudança de schema (sem migration).

Os testes vivem em `src/resources/tests.py` (arquivo a criar). Rodar a partir de
`src/` com `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development`.

- [x] 1. Escrever teste de exploração da condição do bug (antes do fix)
  - **Property 1: Bug Condition** - Criar Resource pelo admin preenche o autor e não estoura
  - **CRITICAL**: Este teste DEVE FALHAR no código não corrigido - a falha confirma que o bug existe
  - **DO NOT** tentar corrigir o teste ou o código quando ele falhar nesta etapa
  - **NOTE**: Este teste codifica o comportamento esperado - ele validará o fix quando passar após a implementação
  - **GOAL**: Surfacing counterexamples que demonstram o bug (`RelatedObjectDoesNotExist: Resource has no creator.`)
  - **Scoped PBT Approach**: Bug determinístico - escopar para os casos concretos de falha (criar via admin como staff; criar instância nova sem `creator`), conforme `isBugCondition(X) = (X.instance.pk IS NULL) AND (X.instance.creator IS NOT SET)`
  - Criar o arquivo `src/resources/tests.py` (ainda não existe)
  - Caso A — Admin add Resource: autenticar client como usuário staff e fazer `POST /admin/resources/resource/add/` com campos válidos do form (`name`, `url`, `theme`, `category`, `abstract`, `publisher`, `keywords`, `approved`) — sem `creator` (não está no form). Asserir redirect 302, objeto persistido com `creator = usuário logado` e `approved = True`
  - Caso B — Admin add TrainingResource: `POST /admin/resources/trainingresource/add/` como staff. Asserir redirect 302, objeto com `isTrainingResource = True`, `creator = usuário logado` e `approved = True`
  - Caso C — `save()` sem creator: instanciar `Resource(name=..., url=..., ...)` novo (sem `creator`) e chamar `.save()`. Asserir que NÃO lança `RelatedObjectDoesNotExist` e que `approved` não é auto-definido (ausência de `creator` != staff)
  - Rodar os testes no código NÃO corrigido: `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development python manage.py test resources` (a partir de `src/`)
  - **EXPECTED OUTCOME**: Testes FALHAM (correto - prova que o bug existe; os casos A/B devem acusar HTTP 500 / `RelatedObjectDoesNotExist`, e o caso C deve estourar em `self.creator.is_staff`)
  - Documentar os counterexamples encontrados (ex.: "POST /admin/resources/resource/add/ retorna 500 com RelatedObjectDoesNotExist em vez de 302")
  - Marcar a task completa quando o teste estiver escrito, rodado e a falha documentada
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Escrever testes de preservação (antes de implementar o fix)
  - **Property 2: Preservation** - Comportamento fora da condição do bug permanece idêntico
  - **IMPORTANT**: Seguir metodologia observation-first — rodar o código NÃO corrigido para entradas fora da condição do bug (`isBugCondition` retorna false) e travar o comportamento observado
  - Adicionar os testes em `src/resources/tests.py`
  - Observar e travar: criação de `Resource` novo por usuário **não-staff** com `creator` já atribuído ⇒ `approved` NÃO vira `True` (continua não auto-aprovado) — Requirement 3.3
  - Observar e travar: criação de `Resource` novo com `creator` **staff** já atribuído (via `creator = request.user` antes do `save()`, como nas views públicas) ⇒ `approved = True` (auto-aprovação preservada) — Requirement 3.1
  - Observar e travar: edição de `Resource`/`TrainingResource` existente (`self.pk` presente) ⇒ `save()` NÃO altera `approved` — Requirement 3.2
  - Observar e travar: `TrainingResource` novo ⇒ `isTrainingResource = True` — Requirement 3.4
  - Rodar os testes no código NÃO corrigido: `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development python manage.py test resources` (a partir de `src/`)
  - **EXPECTED OUTCOME**: Testes PASSAM (confirma o comportamento-base a ser preservado — essas entradas estão fora da condição do bug)
  - Marcar a task completa quando os testes estiverem escritos, rodados e passando no código não corrigido
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 3. Fix para o HTTP 500 na criação de Resource/TrainingResource pelo admin

  - [ ] 3.1 Preencher `creator` na criação via admin
    - Arquivo: `src/resources/admin.py`, classe `ResourceAdminBase`
    - Sobrescrever `save_model(self, request, obj, form, change)`: quando `not change` (criação) e `not obj.creator_id`, atribuir `obj.creator = request.user` antes de `super().save_model(request, obj, form, change)`
    - Usar `not change` para distinguir criação de edição; checar `obj.creator_id` (não `obj.creator`) para não estourar com relação ausente
    - `ResourceAdmin` e `TrainingResourceAdmin` herdam de `ResourceAdminBase`, então ambos os fluxos (Resource e Training Resource) ficam cobertos por este único ponto
    - _Bug_Condition: isBugCondition(X) = (X.instance.pk IS NULL) AND (X.instance.creator IS NOT SET)_
    - _Expected_Behavior: creator ← request.user; registro persistido sem 500; request.user.is_staff ⇒ approved = TRUE (do design, Property 1 / Fix Checking)_
    - _Preservation: Preservation Requirements do design (views públicas, edição, não-staff, isTrainingResource inalterados)_
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 3.2 Tornar `Resource.save()` defensivo quanto à ausência de `creator`
    - Arquivo: `src/resources/models.py`, método `Resource.save()`
    - Trocar `if not self.pk and self.creator.is_staff:` por uma checagem que verifique `self.creator_id` antes de acessar `self.creator` (ex.: `if not self.pk and self.creator_id and self.creator.is_staff:`)
    - Regra preservada: auto-aprova apenas em criação (`not self.pk`) com `creator` presente e staff. Ausência de `creator` ⇒ não auto-aprova e não estoura na avaliação da condição
    - Não alterar `TrainingResource.save()` (proxy) — delega a `Resource.save()` via `super().save()` e mantém `isTrainingResource = True`
    - _Bug_Condition: isBugCondition(X) = (X.instance.pk IS NULL) AND (X.instance.creator IS NOT SET)_
    - _Expected_Behavior: NOT raises(RelatedObjectDoesNotExist) AND approved não auto-definido quando creator ausente (do design, Property / Requirement 2.4)_
    - _Preservation: regra de auto-aprovação e marcação isTrainingResource idênticas fora da condição do bug_
    - _Requirements: 2.4_

  - [ ] 3.3 Verificar que o teste de exploração da condição do bug agora passa
    - **Property 1: Expected Behavior** - Criar Resource pelo admin preenche o autor e não estoura
    - **IMPORTANT**: Re-rodar o MESMO teste da task 1 - NÃO escrever novo teste
    - O teste da task 1 codifica o comportamento esperado; quando passar, confirma que o comportamento esperado foi satisfeito
    - Rodar: `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development python manage.py test resources` (a partir de `src/`)
    - **EXPECTED OUTCOME**: Teste PASSA (confirma que o bug foi corrigido — 302 no admin, `creator = request.user`, `approved = True`; caso C não estoura)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.4 Verificar que os testes de preservação continuam passando
    - **Property 2: Preservation** - Comportamento fora da condição do bug permanece idêntico
    - **IMPORTANT**: Re-rodar os MESMOS testes da task 2 - NÃO escrever novos testes
    - Rodar: `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development python manage.py test resources` (a partir de `src/`)
    - **EXPECTED OUTCOME**: Testes PASSAM (confirma ausência de regressões — views públicas, edição, não-staff e isTrainingResource inalterados)
    - Confirmar que todos os testes continuam passando após o fix
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Checkpoint - Verificação final de ambiente e testes
  - A partir de `src/`, com `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development`:
    1. `python manage.py check` — valida configuração e apps
    2. `python manage.py makemigrations --check --dry-run` — deve ficar limpo (sem migration; a correção não altera schema)
    3. `python manage.py test resources` — todos os testes (exploração + preservação) devem passar
  - Garantir que todos os testes passam; se surgirem dúvidas, perguntar ao usuário
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_
