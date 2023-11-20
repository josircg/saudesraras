# Gerenciamento de idiomas do site

Internamente, a CIVIS mantém o fonte com os textos e nome de classes e atributos em Inglês para que fique o mais compatível possível com o sistema original eucitizen-science.

Entretanto, a linguagem padrão do site é pt-BR e caso o usuário queira ver o site em inglês ou espanhol, ele pode selecionar o idioma desejado que o site é reconfigurado automaticamente.

Para alterar a linguagem padrão do sistema, deve-se alterar o parâmetro LANGUAGE_CODE no settings.py para o idioma desejado.

Na CIVIS, os arquivos de tradução são mantidos apenas em Português e Espanhol mas o sistema permite que novos idiomas sejam adicionados. 

Os arquivos de tradução estão localizados nas pastas src/locale/django.po e src/forum/locale/django.po

# Gerenciamento de Idioma dos Emails

Por enquanto, todos os emails são enviados em Português pois o sistema ainda não permite a seleção do idioma desejado pelo usuário.