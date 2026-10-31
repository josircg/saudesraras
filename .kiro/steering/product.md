# Produto — Saúdes Raras

Contexto de produto e domínio: o *porquê* do sistema. Para *onde* o código
está, ver `#structure`; para stack e ambiente, ver `#django`.

## O que é

Plataforma web para registro e divulgação de informações sobre **Doenças Raras
no Brasil**. Reúne, num único lugar, as organizações, projetos, plataformas,
recursos, eventos e notícias ligados ao tema, para dar visibilidade a quem atua
na área e ajudar pacientes, familiares e pesquisadores a encontrar informação e
apoio.

É **software livre**, com repositório público, e uma **versão especializada da
Plataforma Civis** (IBICT) — portanto herda conceitos de uma plataforma de
ciência cidadã / mobilização social, adaptados ao domínio de doenças raras.

Site em produção (em desenvolvimento): https://saudesraras.pro.br

## Origem e governança

- Idealizada pela Profa. Patricia Saldanha (PPG Mídia e Cotidiano, **UFF**).
- Desenvolvida por estudantes de Ciência da Computação da UFF, com apoio de
  pesquisadores do **IBICT**.
- Contexto acadêmico/sem fins lucrativos: decisões devem favorecer acesso
  aberto à informação, baixo custo operacional e sustentabilidade do projeto.

## Público-alvo

- **Pacientes e familiares** de doenças raras buscando informação, organizações
  de apoio e recursos.
- **Organizações** (associações, ONGs, grupos de pacientes) que querem se
  cadastrar e divulgar sua atuação.
- **Pesquisadores e projetos** de ciência cidadã / iniciativas ligadas ao tema.
- **Equipe/moderadores** da plataforma, que revisam e aprovam o conteúdo
  submetido pela comunidade.

## Conceitos de domínio

- **Doença rara / sintoma** (`diseases`): o núcleo do catálogo. Doenças têm CID
  (ICD), nomes alternativos e sintomas associados; a busca por sintoma é um
  caminho de entrada importante para quem ainda não tem diagnóstico.
- **Organização** (`organisations`): entidade que atua em doenças raras,
  georreferenciada (mapa) e associada às doenças que atende.
- **Projeto / Plataforma** (`projects`, `platforms`): iniciativas de ciência
  cidadã / pesquisa, com localização geográfica, organizações responsáveis e
  conteúdo traduzível.
- **Recurso / Recurso de treinamento** (`resources`): publicações e materiais,
  categorizados, podendo ser vinculados a projetos, organizações e autores.
- **Conteúdo editorial** (`blog`, `pages`, `events`, `digest`): notícias,
  páginas institucionais, depoimentos, FAQ, eventos e boletins periódicos.

## Princípios de produto (guiam decisões de implementação)

- **Conteúdo é submetido pela comunidade e moderado.** A maioria dos tipos de
  conteúdo (organizações, projetos, plataformas, recursos, eventos) passa por
  aprovação antes de aparecer publicamente. Flags `approved`/`hidden`/`featured`
  são centrais. Ao criar features de listagem, por padrão **só** mostre conteúdo
  aprovado e não oculto (há managers `approved_*` para isso).
- **Multi-idioma de verdade.** Idioma padrão **pt-br**, com **es** e **en**.
  Textos de conteúdo de domínio são traduzíveis via o framework de tradução
  genérica (`utilities.AbstractTranslatedModel`/`Translation`), não só i18n de
  template. Ao adicionar conteúdo visível ao usuário, considere os três idiomas.
- **Foco no Brasil.** Fuso `America/Sao_Paulo`, idioma primário pt-br, domínio
  `.pro.br`. Decisões de UX e dados assumem contexto brasileiro (ex.: CID,
  nomenclatura em português), ainda que o sistema seja multilíngue.
- **Acesso aberto.** Projeto livre e público; evite acoplar a serviços pagos ou
  proprietários quando houver alternativa aberta equivalente.
- **Sensibilidade do público.** O público inclui pacientes e familiares em
  situação vulnerável. Linguagem, mensagens de erro e fluxos devem ser
  acolhedores e cuidadosos; nunca tratar doença rara de forma banal ou alarmista.

## O que NÃO é

- Não é um sistema de diagnóstico nem de aconselhamento médico. A busca por
  sintomas é um índice de informação, **não** uma ferramenta clínica — não
  introduza lógica que sugira diagnósticos ou condutas médicas.
- Não é uma rede social; o foco é catálogo de informação curada + conteúdo
  editorial, não interação social aberta entre usuários.
