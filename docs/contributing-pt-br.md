# Diretrizes de contribuição

Obrigado por seu interesse em contribuir com o projeto CIVIS! Agradecemos seus esforços e esperamos poder colaborar com você. Para garantir um processo de contribuição tranquilo e eficiente, leia e siga as diretrizes descritas abaixo.

## Sumário
1. [Código de Conduta](#code-of-conduct)
2. [Como começar](#getting-started)
3. [Relatando erros e solicitando novas funcionalidades](#reporting-bugs-and-feature-requests)
4. [Envie suas mudanças](#submitting-changes)
5. [Padronização do Código](#code-quality-and-standards)
6. [Testes e Integração Contínua](#testing-and-continuous-integration)
7. [Documentação](#documentation)

## Código de Conduta
Todos os colaboradores devem aderir ao nosso [Código de Conduta](CODE_OF_CONDUCT.md), que promove um ambiente respeitoso, profissional e construtivo. Assédio, discriminação ou outros comportamentos inadequados não serão tolerados.

## Como começar
1. Faça um fork do [Repositório da Civis](https://git.redemoara.ibict.br/ibict/cgti/civis).
2. Clone o repositório para a sua máquina pessoal.
3. Configure o ambiente de desenvolvimento seguindo as instruções descritas [aqui](install-dev.md).

## Relatando erros e solicitando novas funcionalidades
1. Verifique na seção de [Solicitações](https://git.redemoara.ibict.br/ibict/cgti/civis/issues) para verificar se o erro ou a solicitação de melhorias já não foi reportada para outra pessoa.
2. Se o problema não existir, crie um novo problema usando o modelo apropriado (relatório de bug ou solicitação de recurso).
3. Descreva a sua solicitação com o maior detalhamento possível, incluindo as etapas para reproduzir o bug, o comportamento esperado e quaisquer mensagens de erro ou capturas de tela relevantes.

## Envie suas mudanças
1. Antes de fazer qualquer alteração, certifique-se de que está trabalhando com a versão mais recente do ramo `master`.
2. Crie um novo 'branch' para suas alterações usando uma convenção de nomenclatura descritiva (exemplo: `feature/username-description` ou `bugfix/username-description`).
3. Faça suas alterações no novo 'branch', seguindo o [Padronização do Código](#Padronização do Código).
4. Teste suas alterações minuciosamente e certifique-se de que todos os testes sejam aprovados.
5. Confirme suas alterações usando mensagens de confirmação concisas e claras que seguem um formato padrão.
6. Execute um 'Push' para o seu repositório.
7. Crie um 'pull request' (PR) para o repositório da Civis, fornecendo um título e uma descrição claros de suas alterações, incluindo quaisquer números de problemas relevantes.
8. Responda a todos os comentários do processo de revisão de código e faça as alterações necessárias.

## Padronização do Código
1. Todo o código Python deve seguir o PEP 8, o guia de estilo do Python, e ser verificado com o Pylint.
2. O HTML e o CSS devem seguir os padrões do W3C.
3. O código JavaScript deve seguir o Guia de estilo JavaScript do Airbnb.
4. As práticas recomendadas do Django devem ser seguidas, incluindo o uso de exibições baseadas em classes, o princípio DRY e o design adequado de aplicativos e modelos.

## Testes e Integração Contínua
1. Todo o código deve ser testado antes do envio de um PR, e os testes devem ser incluídos no PR ao adicionar ou modificar a funcionalidade.
2. O Travis CI pode ser utilizado para integração contínua, e o arquivo de configuração `.travis.yml` deve ser configurado corretamente para executar testes, processos de compilação e quaisquer verificações necessárias.
3. PRs devem passar por todos os testes de integração contínua do Travis antes de serem aprovados e integrados ao código principal (merged).

## Documentação
1. Todo o código deve ser bem documentado, com comentários claros e nomes significativos de variáveis/funções.
2. A documentação do projeto deve ser mantida, incluindo arquivos README, documentação da API e quaisquer outros guias necessários.

**Ao seguir essas diretrizes, você ajudará a promover um ambiente de desenvolvimento produtivo, organizado e colaborativo, garantindo um código da mais alta qualidade e um progresso eficiente no projeto da Plataforma EU-CS. Estamos ansiosos para trabalharmos juntos e causar um impacto positivo!**