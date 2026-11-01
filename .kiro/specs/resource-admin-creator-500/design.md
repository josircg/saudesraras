# Resource Admin Creator 500 Bugfix Design

## Overview

Adicionar um `Resource` (ou `TrainingResource`) pelo admin do Django estoura
com `RelatedObjectDoesNotExist: Resource has no creator.` e retorna HTTP 500.
O formulário do admin (`ResourceAdmin.fields`) não expõe o campo `creator` —
que é uma FK obrigatória (`NOT NULL`) para `AUTH_USER_MODEL` — então a instância
chega em `Resource.save()` sem `creator`. Lá, no ramo de criação (`not self.pk`),
o código acessa `self.creator.is_staff` para decidir a auto-aprovação e estoura
antes do `INSERT`.

A estratégia de correção tem duas partes, ambas sem alteração de schema:

1. **Correção primária (admin preenche o autor):** sobrescrever
   `save_model` em `ResourceAdminBase` para, na criação, atribuir
   `obj.creator = request.user`. Como `ResourceAdmin` e `TrainingResourceAdmin`
   herdam de `ResourceAdminBase`, ambos os fluxos são corrigidos de uma vez.
   Isso garante que a FK obrigatória seja satisfeita com o autor real (o staff
   logado), sem expor o campo no formulário.

2. **Defesa em profundidade (`save()` defensivo):** tornar
   `Resource.save()` resiliente à ausência de `creator`, para não trocar um 500
   explícito por outro erro em chamadores que não sejam o admin, e para que a
   regra de auto-aprovação dependa de um `creator` presente e staff. Sem
   `creator`, não auto-aprova (e não estoura na avaliação da condição).

A parte (1) é a correção real do bug observado (garante `creator`); a parte (2)
protege outros caminhos de código e mantém a semântica da auto-aprovação
explícita e segura. Como `creator` é `NOT NULL`, salvar de fato sem `creator`
ainda resultaria em `IntegrityError` no `INSERT` — o ponto da defesa é a
avaliação da condição, não contornar a constraint do banco.

## Glossary

- **Bug_Condition (C)**: criar uma instância nova de `Resource`/`TrainingResource`
  (`self.pk` é `None`) cujo `creator` não foi atribuído — o que faz `save()`
  estourar ao avaliar `self.creator.is_staff`.
- **Property (P)**: ao adicionar via admin, o sistema preenche `creator` com o
  usuário logado, persiste o registro sem erro 500 e aplica a auto-aprovação
  quando o criador é staff.
- **Preservation**: comportamento das views públicas, da edição de registros
  existentes, da regra de auto-aprovação e da marcação `isTrainingResource`
  permanecem idênticos.
- **`Resource.save()`**: método em `src/resources/models.py` que, na criação
  (`not self.pk`), define `approved = True` se o criador for staff, e então
  chama `super().save()`.
- **`TrainingResource`**: modelo **proxy** de `Resource` em
  `src/resources/models.py`; seu `save()` define `isTrainingResource = True` em
  registros novos e delega a `Resource.save()` via `super().save()`.
- **`ResourceAdminBase`**: classe-base de admin em `src/resources/admin.py` da
  qual `ResourceAdmin` e `TrainingResourceAdmin` herdam.
- **`creator`**: `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)` em
  `Resource`, obrigatória (`NOT NULL` no banco), não exposta no formulário do
  admin.

## Bug Details

### Bug Condition

O bug se manifesta quando um `Resource` (ou `TrainingResource`) novo é salvo
sem que `creator` tenha sido atribuído. No fluxo do admin de adição, o
formulário de `ResourceAdmin`/`TrainingResourceAdmin` não inclui `creator`, e
nada preenche esse campo antes de `save()`. Em `Resource.save()`, para
instância nova (`not self.pk`), o acesso `self.creator.is_staff` dispara
`RelatedObjectDoesNotExist` antes do `INSERT`.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X of type SaveResourceInput  // { instance, via }
  OUTPUT: boolean

  RETURN (X.instance.pk IS NULL)
         AND (X.instance.creator IS NOT SET)
END FUNCTION
```

### Examples

- Staff faz `POST /admin/resources/resource/add/` com campos válidos (sem
  `creator`, que não está no form). Esperado: redirect 302 e Resource criado
  com `creator = request.user`. Atual: HTTP 500 com
  `RelatedObjectDoesNotExist: Resource has no creator.`
- Staff faz `POST /admin/resources/trainingresource/add/` com campos válidos.
  Esperado: redirect 302 e TrainingResource criado (`isTrainingResource=True`)
  com `creator = request.user`. Atual: mesmo HTTP 500 (proxy herda `save()`).
- `Resource(name=..., url=...).save()` numa instância nova sem `creator`.
  Esperado (defensivo): não estourar na avaliação da auto-aprovação (sem
  auto-aprovar). Atual: `RelatedObjectDoesNotExist`.
- Edge case — criação via view pública (`saveResourceAjax`), que seta
  `creator = request.user` antes do `save()`: não é bug (fora de C), deve
  continuar funcionando sem mudança.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Criação pelas views públicas (`saveResourceAjax`, onde `creator` já é setado a
  partir de `request.user`) continua persistindo e aplicando a auto-aprovação
  conforme `creator.is_staff`.
- Edição de `Resource`/`TrainingResource` existente (`self.pk` presente) não
  altera `approved` em `save()` (o ramo de auto-aprovação só vale para novos).
- Criação por usuário não-staff com `creator` preenchido continua não
  auto-aprovando (`approved` fica no estado submetido / não moderado).
- `TrainingResource` novo continua marcando `isTrainingResource = True`.
- O signal `notify_approved_resource` não muda; continua assumindo `creator`
  presente — agora garantido na criação via admin.

**Scope:**
Todas as entradas que NÃO caem na condição do bug devem ficar completamente
inalteradas por esta correção. Isso inclui:
- Criação via views públicas (creator já atribuído).
- Edição de registros existentes (`self.pk` presente).
- Qualquer `save()` em que `creator` já esteja atribuído (staff ou não).

A expectativa de comportamento correto para as entradas da condição do bug está
definida na seção Correctness Properties (Property 1).

## Hypothesized Root Cause

Com base na análise do bug e no código real (`src/resources/models.py` e
`src/resources/admin.py`):

1. **Campo `creator` ausente no formulário do admin**: `ResourceAdmin.fields`
   lista `('name', 'url', 'theme', 'category', 'abstract', 'publisher',
   'keywords', 'approved', 'safe_url')`, sem `creator`.
   `TrainingResourceAdmin` herda de `ResourceAdminBase` e usa a mesma base de
   campos. Nada atribui `creator` antes do `save()`.

2. **Acesso não defensivo em `Resource.save()`**: no ramo de criação
   (`not self.pk`), `self.creator.is_staff` acessa uma relação não atribuída,
   disparando `RelatedObjectDoesNotExist` antes do `INSERT`.

3. **Herança via proxy propaga o defeito**: `TrainingResource.save()` chama
   `super().save()`, então o mesmo caminho estoura para Training Resources.

4. **FK obrigatória**: `creator` é `NOT NULL`; mesmo com `save()` defensivo, um
   `INSERT` sem `creator` falharia com `IntegrityError`. Daí a necessidade de a
   parte (1) garantir o `creator` na criação pelo admin.

## Correctness Properties

Property 1: Bug Condition - Criar Resource pelo admin preenche o autor e não estoura

_For any_ input onde a condição do bug vale (`isBugCondition` retorna true) e a
criação ocorre pelo admin com um usuário staff logado, o fluxo corrigido SHALL
atribuir `creator = request.user`, persistir o registro sem erro 500 (redirect
302 do admin) e, por ser o criador staff, definir `approved = True`
(auto-aprovação). Para `TrainingResource`, SHALL também manter
`isTrainingResource = True`.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Comportamento fora da condição do bug permanece idêntico

_For any_ input onde a condição do bug NÃO vale (`isBugCondition` retorna false)
— criação via views públicas com `creator` já atribuído, edição de registros
existentes, criação por não-staff, marcação de `isTrainingResource` — o fluxo
corrigido SHALL produzir exatamente o mesmo resultado do fluxo original,
preservando a regra de auto-aprovação (`creator.is_staff` em instâncias novas),
a não alteração de `approved` na edição e o comportamento do signal
`notify_approved_resource`.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

Além disso, como defesa em profundidade: _para qualquer_ instância nova sem
`creator` atribuído, a avaliação da condição de auto-aprovação em
`Resource.save()` SHALL não lançar `RelatedObjectDoesNotExist` e SHALL tratar a
ausência de `creator` como "não é staff" (sem auto-aprovar). **Validates:
Requirement 2.4**

## Fix Implementation

### Changes Required

Assumindo que a análise da causa raiz está correta. Nenhuma mudança de schema,
nenhum campo novo/alterado — portanto **nenhuma migration** (confirmar com
`makemigrations --check --dry-run`).

**File**: `src/resources/admin.py`

**Class**: `ResourceAdminBase`

1. **Preencher `creator` na criação via admin**: sobrescrever
   `save_model(self, request, obj, form, change)` para, quando `not change`
   (criação) e `obj.creator_id` estiver vazio, atribuir
   `obj.creator = request.user` antes de chamar `super().save_model(...)`.
   - Usar `not change` para distinguir criação de edição.
   - Checar `obj.creator_id` (e não `obj.creator`) para não estourar se, por
     algum caminho, `creator` ainda não estiver atribuído.
   - Como `ResourceAdmin` e `TrainingResourceAdmin` herdam de
     `ResourceAdminBase`, ambos os fluxos (Resource e Training Resource) ficam
     cobertos por este único ponto.

   Esboço:
   ```python
   def save_model(self, request, obj, form, change):
       if not change and not obj.creator_id:
           obj.creator = request.user
       super().save_model(request, obj, form, change)
   ```

**File**: `src/resources/models.py`

**Method**: `Resource.save()`

2. **Tornar a checagem de auto-aprovação defensiva**: trocar o acesso direto
   `self.creator.is_staff` por uma checagem que verifique a presença do
   `creator` via `self.creator_id` antes de acessar `self.creator`. A regra
   permanece: auto-aprova apenas se for criação (`not self.pk`) E houver
   `creator` E `creator.is_staff`. Ausência de `creator` ⇒ não auto-aprova
   (e não estoura).

   Esboço:
   ```python
   def save(self, *args, **kwargs):
       # approved pode ser null (nao moderado); so auto-aprova em criacao
       # com creator presente e staff. Ausencia de creator nao estoura aqui.
       if not self.pk and self.creator_id and self.creator.is_staff:
           self.approved = True

       super().save(*args, **kwargs)
   ```

### Decisões de design

- **Setar `creator` no admin vs. tornar o campo editável no form**: optamos por
  atribuir `creator = request.user` no `save_model`, em vez de expor `creator`
  no formulário. Isso registra a autoria real (quem está logado) e evita que o
  staff escolha outro autor manualmente, mantendo consistência com as views
  públicas, que também derivam o criador de `request.user`.
- **Interação com a auto-aprovação**: como o criador via admin é staff, a regra
  original (`creator.is_staff ⇒ approved = True`) resulta em auto-aprovação,
  consistente com a intenção do código existente.
- **`TrainingResource` (proxy)**: coberto pela herança de
  `ResourceAdminBase.save_model` e pelo mesmo `Resource.save()`; nenhuma mudança
  específica no proxy é necessária.
- **Sem schema/migration**: nenhum campo é adicionado ou alterado;
  `makemigrations --check --dry-run` deve seguir limpo.
- **Signals**: `notify_approved_resource` não muda. Ele continua assumindo
  `creator` presente (usa `instance.creator.email` no ramo de aprovação de
  registros existentes) — presença agora garantida na criação via admin.

## Testing Strategy

### Validation Approach

A estratégia segue duas fases: primeiro, demonstrar o bug no código não
corrigido (contra-exemplos), depois verificar que o fix funciona e preserva o
comportamento existente. Os testes vivem no app `resources` e usam o runner
padrão do Django (`python manage.py test resources`), com
`DJANGO_SETTINGS_MODULE=eucs_platform.settings.development`.

### Exploratory Bug Condition Checking

**Goal**: Surfacing counterexamples que demonstrem o bug ANTES do fix. Confirmar
ou refutar a análise de causa raiz. Se refutar, re-hipotetizar.

**Test Plan**: Com um client autenticado como staff, fazer `POST` nos endpoints
de adição do admin e observar o HTTP 500 / `RelatedObjectDoesNotExist` no código
não corrigido. Adicionalmente, instanciar um `Resource` novo sem `creator` e
chamar `save()` para observar o estouro.

**Test Cases**:
1. **Admin add Resource**: `POST /admin/resources/resource/add/` como staff com
   campos válidos (sem `creator`) — falha no código não corrigido (500).
2. **Admin add TrainingResource**: `POST
   /admin/resources/trainingresource/add/` como staff — falha no código não
   corrigido (500).
3. **save() sem creator**: `Resource(name=..., url=...).save()` numa instância
   nova — lança `RelatedObjectDoesNotExist` no código não corrigido.

**Expected Counterexamples**:
- `RelatedObjectDoesNotExist: Resource has no creator.` ao avaliar
  `self.creator.is_staff` em `save()`.
- Causas prováveis: `creator` ausente no form do admin; acesso não defensivo em
  `save()`.

### Fix Checking

**Goal**: Verificar que, para toda entrada da condição do bug, o fluxo corrigido
produz o comportamento esperado.

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result := save'(X)   // via admin: creator = request.user (staff)
  ASSERT no_exception(result)
         AND X.instance.creator = request.user
         AND resource_persisted(X.instance)
         AND (request.user.is_staff IMPLIES X.instance.approved = TRUE)
END FOR
```

### Preservation Checking

**Goal**: Verificar que, para toda entrada fora da condição do bug, o fluxo
corrigido produz o mesmo resultado do original.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

**Testing Approach**: Testes baseados em exemplos cobrem bem os ramos desta
correção (criação staff/não-staff, edição, proxy). A preservação é verificada
observando o comportamento no código não corrigido para entradas fora de C e
garantindo que ele se mantém após o fix.

**Test Plan**: Observar o comportamento no código não corrigido para criação com
`creator` já setado (staff e não-staff) e edição de registros existentes, e
escrever testes que travem esse comportamento após o fix.

**Test Cases**:
1. **Criação por não-staff não auto-aprova**: `Resource` novo com `creator`
   não-staff ⇒ `approved` não vira `True`.
2. **Edição não altera approved**: salvar um `Resource` existente não mexe em
   `approved` no `save()`.
3. **View pública permanece**: criação com `creator = request.user` já atribuído
   continua persistindo e aplicando a auto-aprovação conforme `is_staff`.

### Unit Tests

- `Resource.save()` em instância nova sem `creator` não lança
  `RelatedObjectDoesNotExist` e não auto-aprova (defensivo — Requirement 2.4).
- `Resource.save()` em instância nova com `creator` staff define `approved=True`;
  com `creator` não-staff mantém `approved` não auto-aprovado.
- `Resource.save()` em edição (`self.pk` presente) não altera `approved`.

### Property-Based Tests

- Não previstos nesta correção. Os ramos são discretos e pequenos (criação vs.
  edição; staff vs. não-staff vs. ausente), bem cobertos por testes de exemplo.
  Caso desejado, uma PBT de preservação poderia gerar instâncias com `creator`
  atribuído aleatório (staff/não-staff) e asserir que `F(X) = F'(X)` fora da
  condição do bug.

### Integration Tests

- **Admin add Resource (staff)**: client staff faz `POST
  /admin/resources/resource/add/` com payload válido ⇒ resposta 302 (sucesso),
  objeto criado com `creator = usuário logado` e `approved = True`.
- **Admin add TrainingResource (staff)**: client staff faz `POST
  /admin/resources/trainingresource/add/` ⇒ 302, objeto com
  `isTrainingResource = True`, `creator = usuário logado` e `approved = True`.
- **Verificação de ambiente** (após as mudanças, a partir de `src/`, com
  `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development`):
  1. `python manage.py check`
  2. `python manage.py makemigrations --check --dry-run` (deve seguir limpo)
  3. `python manage.py test resources`
