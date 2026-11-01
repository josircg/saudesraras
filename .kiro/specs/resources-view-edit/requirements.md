# Requirements Document

_Feature: Visualização e edição de recursos (publicações), com tratamento da imagem de capa_

## Introduction

Esta spec documenta a visualização (listagem `/resources` e detalhe
`/resource/<id>`), a edição (formulário `/editResource/<id>`) e o admin de
recursos do app `resources`, com foco no **tratamento da imagem de capa**
(`Resource.image1`).

A capa de um recurso é, em geral, a capa de um livro, revista ou cartilha, e
por isso segue a **proporção A4 retrato (210:297 ≈ 1:1,414)** em todas as etapas:
recorte no navegador, gravação no servidor, thumbnails e molduras de exibição.

Os itens marcados **[IMPLEMENTADO]** já estão no código; **[PENDENTE]** são
lacunas ou decisões em aberto.

> Convenções em `#django`; estrutura dos apps em `#structure`; princípios de
> produto (conteúdo moderado, multi-idioma pt-br/es/en) em `#product`.

## Glossary

- **Capa / image1**: campo `ImageField` `Resource.image1`, a imagem principal do recurso.
- **Proporção A4**: 210:297 (retrato). Tamanho de referência da capa gravada: **600 x 848 px**.
- **Preset de recorte**: tamanho-alvo usado pelo `modal-crop.js`, escolhido pelo atributo
  `data-image-width-option` do campo: `0` = 600x400, `1` = 1100x400, `2` = 600x848 (A4).
- **Moldura A4**: contêiner com `aspect-ratio: 210 / 297` e a imagem com `object-fit: cover`.
- **Fallback**: ícone `static/site/img/publicacoes.svg`, exibido quando o recurso não tem capa.
- **Imagem legada**: capa gravada antes desta mudança, em 600x400 (paisagem). Não é reprocessada.
- **Training resource**: recurso com `isTrainingResource=True` (proxy `TrainingResource`); usa
  as rotas `/training_resource/<id>` e `/editTrainingResource/<id>`.

## Requirements

### Requirement 1: Listagem de recursos [IMPLEMENTADO]
**User Story:** Como visitante, quero ver os recursos numa lista legível, com título,
descrição e capa, para escolher o que abrir.

#### Acceptance Criteria
1. QUANDO a listagem `/resources` é exibida ENTÃO cada recurso DEVE aparecer num card de
   coluna única larga, com a capa à esquerda e o conteúdo à direita.
2. O card DEVE exibir sempre o título (link para o detalhe) e a descrição resumida
   (`abstract` com `truncate_summary:45`), sem depender de hover.
3. O card DEVE exibir a categoria e os tópicos (`theme`) como tags azuis (`bg-blue3`),
   traduzidos (`translate_instance` / `translated_sorted_by_text`).
4. O card NÃO DEVE exibir o tipo (Resource/Training Resource) nem um botão "Saiba mais";
   o título e a capa são os links para o detalhe.
5. O mesmo card DEVE ser usado nas demais listagens que o incluem (home e página de
   recursos curados).

### Requirement 2: Detalhe do recurso [IMPLEMENTADO]
**User Story:** Como visitante, quero ver a capa e as informações do recurso com a
descrição em destaque e as ações agrupadas.

#### Acceptance Criteria
1. QUANDO o detalhe `/resource/<id>` é exibido ENTÃO a descrição (`abstract`) DEVE aparecer
   logo abaixo do título, antes das datas e metadados.
2. Os botões "Ir para publicação", "Contatar responsável pelo cadastro" e "Editar" DEVEM
   ficar lado a lado no mesmo grupo.
3. "Contatar responsável" DEVE aparecer apenas para staff; "Editar" apenas para o criador,
   staff ou cooperadores.
4. A capa DEVE ocupar uma coluna estreita (`col-md-3`), com o conteúdo em `col-md-9`.

### Requirement 3: Formulário de edição [IMPLEMENTADO]
**User Story:** Como editor, quero editar o recurso com botões de salvar consistentes
com o restante do site.

#### Acceptance Criteria
1. Os botões "Salvar" e "Salvar e continuar editando" DEVEM usar o mesmo estilo do
   formulário de organização (`btn-blue3`), sem alterar os formulários de projeto e
   plataforma, que compartilham o `_save_zone.html`.
2. O formulário DEVE oferecer apenas a categoria raiz; a seleção de subcategoria foi
   removida do site (ver Requisito 8.3).
3. O formulário NÃO DEVE conter campos sem uso (`choices`, `categorySelected` removidos).
4. O `modal-crop.js` DEVE ser carregado uma única vez na página.

### Requirement 4: Recorte da capa no navegador [IMPLEMENTADO]
**User Story:** Como editor, quero recortar a capa já na proporção A4, para que o
resultado não saia achatado.

#### Acceptance Criteria
1. O campo `image1` DEVE usar o preset de recorte `2` (`data-image-width-option=2`).
2. QUANDO o preset `2` está ativo ENTÃO o `modal-crop.js` DEVE usar proporção
   600/848, tamanho mínimo da moldura 600x848 e gerar o preview pós-recorte em 600x848.
3. Os presets `0` (600x400) e `1` (1100x400) DEVEM continuar inalterados para organizações,
   projetos e plataformas.
4. O preview no formulário DEVE manter o id `imageResult1`, para que o recorte atualize a
   imagem exibida.

### Requirement 5: Gravação da capa no servidor [IMPLEMENTADO]
**User Story:** Como mantenedor, quero que a capa gravada siga a proporção do recorte,
para não distorcer a imagem.

#### Acceptance Criteria
1. QUANDO uma nova capa é enviada pelo formulário do site ENTÃO o servidor DEVE recortar
   pela área escolhida (x, y, largura, altura), corrigir a orientação EXIF e redimensionar
   para **600x848** (`RESOURCE_IMAGE_SIZE`).
2. O arquivo DEVE ser gravado em `MEDIA_ROOT/images/<uuid>.<ext>`.
3. QUANDO nenhum arquivo novo é enviado ENTÃO a capa existente DEVE ser mantida.
4. Imagens legadas (600x400) NÃO DEVEM ser reprocessadas.

### Requirement 6: Exibição da capa [IMPLEMENTADO]
**User Story:** Como visitante, quero ver as capas sempre na proporção correta.

#### Acceptance Criteria
1. A listagem DEVE exibir a capa numa moldura A4 de 140px de largura, com thumbnail
   **280x396** (2x, para telas de alta densidade).
2. O detalhe DEVE exibir a capa numa moldura A4, com thumbnail **420x594**.
3. O preview do formulário DEVE exibir a capa numa moldura A4 de até 300px de largura,
   com thumbnail **420x594**.
4. As molduras DEVEM ser definidas no próprio template (estilo inline), sem depender do
   CSS global.
5. QUANDO o recurso não tem capa ENTÃO listagem, detalhe e formulário DEVEM exibir o
   fallback `publicacoes.svg` centralizado na mesma moldura A4.

### Requirement 7: Admin de recursos [IMPLEMENTADO]
**User Story:** Como moderador, quero sair do admin direto para a edição completa ou para
a página pública do recurso.

#### Acceptance Criteria
1. QUANDO um recurso é aberto no admin ENTÃO DEVEM aparecer os power buttons
   "Edição Completa" (`/editResource/<id>`) e "Visualizar no site" (`/resource/<id>`).
2. Para training resources, os botões DEVEM apontar para `/editTrainingResource/<id>` e
   `/training_resource/<id>`.
3. Na tela de inclusão (sem id), os botões NÃO DEVEM aparecer e o campo `safe_url` DEVE
   ficar vazio (antes gerava o link quebrado `/editResource/None`).
4. Os rótulos DEVEM usar msgid em inglês (`Full edit`, `View on site`), traduzidos nos `.po`.
5. SE o usuário do admin não é superuser ENTÃO o campo `image1` DEVE ser somente leitura
   (exibe o arquivo atual, sem campo de upload), em `Resource` e em `TrainingResource`.
   A troca da capa por esses usuários DEVE ser feita pelo formulário do site
   ("Edição Completa"), que aplica o recorte A4.
6. SE um usuário não superuser enviar um arquivo `image1` no POST do admin ENTÃO o
   servidor DEVE ignorá-lo e manter a capa atual, salvando os demais campos.
7. O superuser DEVE continuar podendo enviar a capa pelo admin; nesse caso o arquivo é
   gravado como veio, sem recorte nem redimensionamento.

### Requirement 8: Lacunas e decisões em aberto [PENDENTE]
**User Story:** Como mantenedor, quero que os pontos em aberto fiquem registrados.

#### Acceptance Criteria
1. **[RESOLVIDO]** O CSS global (`eu-citizen_science.css`) tinha 2 blocos sem chave de
   fechamento (`.period-line` e `.btn4:hover`), herdados das branches issue118 e
   issue154, que desativavam os estilos seguintes (ícones da barra de busca, botões de
   sintomas, FAQ). Os `}` foram acrescentados; falta a conferência visual no navegador.
2. **[RESOLVIDO]** Uma capa enviada **pelo admin** é gravada como veio, sem recorte nem
   redimensionamento. Decisão: o campo `image1` fica somente leitura no admin para quem
   não é superuser (ver Requisitos 7.5 a 7.7). A proporção A4 só não é garantida quando
   um superuser envia a capa pelo admin.
3. Subcategorias continuam editáveis só pelo admin. Editar pelo site um recurso que use
   subcategoria troca a categoria pela raiz (hoje nenhum recurso usa subcategoria).
4. Não há como remover a capa pelo formulário do site; só substituir.
5. **[NÃO SE APLICA]** Imagens legadas: o banco de produção não tem imagens de
   recursos. Mantido `object-fit: cover`.
6. **[RESOLVIDO]** A migration `0055_alter_resource_options` (só metadado, sem SQL) foi
   aplicada.

## Out of Scope

- Reprocessar ou converter as imagens legadas para A4.
- Edição de imagens de organizações, projetos e plataformas (seguem os presets 0 e 1).
- Seleção de subcategoria pelo site.

## Data Impact

- Sem mudança de schema. A migration `0055` só altera `verbose_name_plural` do model
  `Resource` (`sqlmigrate` não gera SQL).
- Novas capas passam a ser gravadas em 600x848; as existentes permanecem em 600x400.
