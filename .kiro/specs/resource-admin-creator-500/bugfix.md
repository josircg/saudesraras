# Bugfix Requirements Document

## Introduction

Ao adicionar um Resource (publicação) pelo admin do Django, o POST em
`/admin/resources/resource/add/` retorna **HTTP 500 (Internal Server Error)**
com a exceção `RelatedObjectDoesNotExist: Resource has no creator.`

A causa raiz está em `Resource.save()` (`src/resources/models.py`), que, ao
criar um registro novo (`not self.pk`), acessa `self.creator.is_staff` para
decidir a auto-aprovação. No fluxo do admin, o campo `creator` (FK obrigatória
para `AUTH_USER_MODEL`) nunca é preenchido, porque o formulário do
`ResourceAdmin` não inclui `creator` (`fields = ('name', 'url', 'theme',
'category', 'abstract', 'publisher', 'keywords', 'approved', 'safe_url')`).
O acesso ao atributo da relação ausente estoura antes do `INSERT`.

O mesmo defeito atinge o fluxo de **TrainingResource** no admin, pois
`TrainingResource` é um modelo proxy de `Resource` e reutiliza o mesmo `save()`
via `super().save()`.

O bug é específico do admin: nas views públicas (`saveResourceAjax` em
`src/resources/views.py`) o `creator` é preenchido a partir de `request.user`
antes do `save()`, por isso ali não ocorre.

Impacto: moderadores/equipe (staff) não conseguem cadastrar Resources nem
Training Resources pelo admin, bloqueando um caminho legítimo de inclusão de
conteúdo.

## Bug Analysis

### Current Behavior (Defect)

O comportamento abaixo descreve o que acontece hoje (função original `F`).

1.1 WHEN um usuário staff submete o formulário de adição em
`POST /admin/resources/resource/add/` com os campos válidos (sem `creator`,
que não está no form) THEN o sistema lança `RelatedObjectDoesNotExist`
("Resource has no creator.") e retorna HTTP 500, sem persistir o Resource.

1.2 WHEN um usuário staff submete o formulário de adição em
`POST /admin/resources/trainingresource/add/` com os campos válidos THEN o
sistema lança a mesma `RelatedObjectDoesNotExist` e retorna HTTP 500, sem
persistir o Training Resource (TrainingResource é proxy de Resource e herda o
mesmo `save()`).

1.3 WHEN `Resource.save()` é chamado para uma instância nova (`not self.pk`)
cujo `creator` não foi atribuído THEN o sistema estoura ao avaliar
`self.creator.is_staff`, antes de executar o `INSERT`.

**Passos de reprodução:**
1. Autenticar no admin como usuário staff.
2. Acessar `/admin/resources/resource/add/`.
3. Preencher os campos do formulário (name, url, theme, category, abstract,
   publisher, keywords, approved) — o formulário não expõe `creator`.
4. Submeter (POST).
5. Resultado: página de erro HTTP 500 com `RelatedObjectDoesNotExist:
   Resource has no creator.` (idem para `/admin/resources/trainingresource/add/`).

### Expected Behavior (Correct)

O comportamento abaixo descreve o que deve acontecer após a correção
(função corrigida `F'`).

2.1 WHEN um usuário staff submete o formulário de adição em
`POST /admin/resources/resource/add/` com os campos válidos THEN o sistema
SHALL preencher `creator` com o usuário logado (`request.user`), persistir o
Resource e retornar sem erro 500 (redirect normal do admin), sem exigir
`creator` no formulário.

2.2 WHEN um usuário staff submete o formulário de adição em
`POST /admin/resources/trainingresource/add/` com os campos válidos THEN o
sistema SHALL preencher `creator` com o usuário logado, persistir o Training
Resource e retornar sem erro 500.

2.3 WHEN um Resource é criado pelo admin por um usuário staff (`creator`
preenchido com `request.user`, que é `is_staff`) THEN o sistema SHALL manter a
intenção original do `save()` de definir `approved = True` (auto-aprovação para
criador staff).

2.4 WHEN `Resource.save()` é chamado para uma instância nova sem `creator`
atribuído THEN o sistema SHALL ser defensivo e NÃO estourar com
`RelatedObjectDoesNotExist` ao avaliar a condição de auto-aprovação (tratando
a ausência de `creator` como "não é staff", isto é, sem auto-aprovar).

### Unchanged Behavior (Regression Prevention)

3.1 WHEN um Resource é criado pelas views públicas
(`saveResourceAjax`, onde `creator` é setado a partir de `request.user` antes
do `save()`) THEN o sistema SHALL CONTINUAR a persistir o Resource e a aplicar
a regra de auto-aprovação conforme `creator.is_staff`.

3.2 WHEN um Resource ou TrainingResource existente (`self.pk` presente) é salvo
(edição) THEN o sistema SHALL CONTINUAR a não alterar `approved` no `save()`
(o ramo de auto-aprovação só se aplica a registros novos).

3.3 WHEN um Resource é criado por um usuário não-staff com `creator` preenchido
THEN o sistema SHALL CONTINUAR a não auto-aprovar (`approved` permanece no
estado submetido / não moderado).

3.4 WHEN um TrainingResource novo é salvo THEN o sistema SHALL CONTINUAR a
definir `isTrainingResource = True` para registros novos.

3.5 WHEN o pre_save signal `notify_approved_resource` é disparado na aprovação
de um Resource existente THEN o sistema SHALL CONTINUAR com o comportamento
atual (fora do escopo desta correção, que trata apenas o estouro na criação).

---

## Deriving the Bug Condition

**Definições:**
- **F**: `Resource.save()` atual (acessa `self.creator.is_staff` sem checar
  presença de `creator`), somado ao `ResourceAdmin` que não popula `creator`.
- **F'**: fluxo corrigido — admin preenche `creator = request.user` ao adicionar,
  e `save()` passa a ser defensivo quanto à ausência de `creator`.

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type SaveResourceInput  // { instance, via }
  OUTPUT: boolean

  // Estoura ao criar um Resource/TrainingResource novo cujo creator
  // não foi atribuido (caminho do admin de adicao).
  RETURN (X.instance.pk IS NULL) AND (X.instance.creator IS NOT SET)
END FUNCTION
```

### Property Specification (Fix Checking)

```pascal
// Property: Fix Checking - criacao pelo admin nao deve estourar
FOR ALL X WHERE isBugCondition(X) DO
  result ← save'(X)   // via admin: creator = request.user (staff)
  ASSERT no_exception(result)
         AND X.instance.creator = request.user
         AND resource_persisted(X.instance)
         AND (request.user.is_staff IMPLIES X.instance.approved = TRUE)
END FOR
```

```pascal
// Property: Fix Checking - save() defensivo com creator ausente
FOR ALL X WHERE (X.instance.pk IS NULL) AND (X.instance.creator IS NOT SET) DO
  result ← save'(X)
  ASSERT NOT raises(result, RelatedObjectDoesNotExist)
         AND X.instance.approved_not_auto_set   // ausencia de creator != staff
END FOR
```

### Preservation Goal (Preservation Checking)

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Ou seja: criação via views públicas (creator já setado), edição de registros
existentes, auto-aprovação para criador staff, não-aprovação para não-staff e
a marcação `isTrainingResource` devem permanecer idênticos ao comportamento
atual.
