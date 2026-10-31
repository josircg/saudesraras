"""
Testes do modelo de autorizacao em cascata das views de edicao front-end
do app `pages` (spec pages-permissioned-editing, Task 6).

Cada view de edicao usa @login_required(login_url='/login') e, apos autenticar,
avalia uma cascata de permissoes (global -> objeto na pagina mae -> objeto na
secao -> objeto no artigo). Negacao => HTTP 403 com `pages/no_permission.html`.

Exercitamos a autorizacao apenas com GET (200 = permitido, 403 = negado); nao e
necessario submeter POST valido para testar a checagem de permissao.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from guardian.shortcuts import assign_perm

from .models import Page, Section, Article

User = get_user_model()

# Idioma usado nos objetos; precisa bater com get_language() nas views
# (as views fazem get_object_or_404(Page, ..., language=get_language())).
# LANGUAGE_CODE = "pt-br" no settings.
LANG = "pt-br"


class PagesAuthorizationBaseTest(TestCase):
    """Base com objetos (Page/Section/Article) e helpers de permissao."""

    def setUp(self):
        # Garante que get_language() devolva o idioma dos objetos criados.
        translation.activate(LANG)
        self.addCleanup(translation.deactivate)

        # --- Hierarquia principal ---
        self.page = Page.objects.create(slug="medicos", title="Medicos", language=LANG)
        self.section = Section.objects.create(
            page=self.page, order=1, title="Secao A", visible=True
        )
        self.article = Article.objects.create(
            section=self.section, order=1, title="Artigo A", content="conteudo A"
        )

        # --- Hierarquia alternativa (sem permissao concedida) ---
        self.other_page = Page.objects.create(
            slug="justica", title="Justica", language=LANG
        )
        self.other_section = Section.objects.create(
            page=self.other_page, order=1, title="Secao B", visible=True
        )
        self.other_article = Article.objects.create(
            section=self.other_section, order=1, title="Artigo B", content="conteudo B"
        )

        # ContentTypes para permissoes globais
        self.ct_page = ContentType.objects.get_for_model(Page)
        self.ct_section = ContentType.objects.get_for_model(Section)
        self.ct_article = ContentType.objects.get_for_model(Article)

    # ---- Helpers de usuario / permissao ----

    def _criar_usuario(self, email, superuser=False):
        if superuser:
            return User.objects.create_superuser(
                email=email, name="Super", password="x"
            )
        return User.objects.create_user(email=email, name="User", password="x")

    def _add_perm_global(self, user, codename, content_type):
        perm = Permission.objects.get(codename=codename, content_type=content_type)
        user.user_permissions.add(perm)
        # Recarrega para limpar cache de permissoes
        return User.objects.get(pk=user.pk)

    # ---- Helpers de URL ----

    def url_edit_page(self, page=None):
        page = page or self.page
        return reverse("edit_page_generic", kwargs={"page_slug": page.slug})

    def url_new_section(self, page=None):
        page = page or self.page
        return reverse("new_section_generic", kwargs={"page_slug": page.slug})

    def url_edit_section(self, page=None, section=None):
        page = page or self.page
        section = section or self.section
        return reverse(
            "edit_section_generic",
            kwargs={"page_slug": page.slug, "section_id": section.id},
        )

    def url_new_article(self, page=None, section=None):
        page = page or self.page
        section = section or self.section
        return reverse(
            "new_article_generic",
            kwargs={"page_slug": page.slug, "section_id": section.id},
        )

    def url_edit_article(self, page=None, section=None, article=None):
        page = page or self.page
        section = section or self.section
        article = article or self.article
        return reverse(
            "edit_article_generic",
            kwargs={
                "page_slug": page.slug,
                "section_id": section.id,
                "article_id": article.id,
            },
        )

    def todas_rotas_edicao(self):
        """Todas as rotas de edicao da hierarquia principal."""
        return [
            self.url_edit_page(),
            self.url_new_section(),
            self.url_edit_section(),
            self.url_new_article(),
            self.url_edit_article(),
        ]


class SuperuserEGlobalTest(PagesAuthorizationBaseTest):
    """6.1 - Superuser e permissao global (Req 3.1, 3.2)."""

    def test_superuser_recebe_200_em_todas_as_rotas(self):
        user = self._criar_usuario("super@example.com", superuser=True)
        self.client.force_login(user)
        for url in self.todas_rotas_edicao():
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200, msg=url)

    def test_change_page_global_permite_todas_as_rotas(self):
        # change_page global cobre TODAS as views (e a primeira da cascata).
        user = self._criar_usuario("gp@example.com")
        user = self._add_perm_global(user, "change_page", self.ct_page)
        self.client.force_login(user)
        for url in self.todas_rotas_edicao():
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200, msg=url)

    def test_change_section_global_permite_rotas_de_secao_e_artigo(self):
        # change_section global permite: new_section, edit_section,
        # new_article e edit_article (NAO edit_page).
        user = self._criar_usuario("gs@example.com")
        user = self._add_perm_global(user, "change_section", self.ct_section)
        self.client.force_login(user)

        permitido = [
            self.url_new_section(),
            self.url_edit_section(),
            self.url_new_article(),
            self.url_edit_article(),
        ]
        for url in permitido:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200, msg=url)

        # edit_page NAO esta coberto por change_section
        self.assertEqual(self.client.get(self.url_edit_page()).status_code, 403)

    def test_change_article_global_permite_rotas_de_artigo(self):
        # change_article global permite new_article e edit_article.
        user = self._criar_usuario("ga@example.com")
        user = self._add_perm_global(user, "change_article", self.ct_article)
        self.client.force_login(user)

        self.assertEqual(self.client.get(self.url_new_article()).status_code, 200)
        self.assertEqual(self.client.get(self.url_edit_article()).status_code, 200)

        # NAO cobre edit_page, new_section nem edit_section
        self.assertEqual(self.client.get(self.url_edit_page()).status_code, 403)
        self.assertEqual(self.client.get(self.url_new_section()).status_code, 403)
        self.assertEqual(self.client.get(self.url_edit_section()).status_code, 403)


class PermissaoPorObjetoPaginaTest(PagesAuthorizationBaseTest):
    """6.2 - change_page por objeto na pagina (Req 3.3)."""

    def setUp(self):
        super().setUp()
        self.user = self._criar_usuario("owner_page@example.com")
        assign_perm("change_page", self.user, self.page)
        self.client.force_login(self.user)

    def test_permite_editar_pagina_criar_secao_e_criar_editar_artigo(self):
        rotas_permitidas = [
            self.url_edit_page(),
            self.url_new_section(),
            self.url_edit_section(),
            self.url_new_article(),
            self.url_edit_article(),
        ]
        for url in rotas_permitidas:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200, msg=url)

    def test_nao_permite_em_outra_pagina_sem_permissao(self):
        rotas_negadas = [
            self.url_edit_page(page=self.other_page),
            self.url_new_section(page=self.other_page),
            self.url_edit_section(page=self.other_page, section=self.other_section),
            self.url_new_article(page=self.other_page, section=self.other_section),
            self.url_edit_article(
                page=self.other_page,
                section=self.other_section,
                article=self.other_article,
            ),
        ]
        for url in rotas_negadas:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403, msg=url)


class PermissaoPorObjetoSecaoEArtigoTest(PagesAuthorizationBaseTest):
    """6.3 - change_section e change_article por objeto (Req 3.4, 3.5, 3.6)."""

    def test_change_section_objeto_permite_secao_e_artigos_mas_nao_pagina(self):
        user = self._criar_usuario("owner_section@example.com")
        assign_perm("change_section", user, self.section)
        self.client.force_login(user)

        # Pode editar a secao e criar/editar seus artigos
        self.assertEqual(self.client.get(self.url_edit_section()).status_code, 200)
        self.assertEqual(self.client.get(self.url_new_article()).status_code, 200)
        self.assertEqual(self.client.get(self.url_edit_article()).status_code, 200)

        # NAO pode editar a pagina (edit_page nao considera change_section)
        self.assertEqual(self.client.get(self.url_edit_page()).status_code, 403)

        # E nao pode mexer em outra secao
        self.assertEqual(
            self.client.get(
                self.url_edit_section(page=self.other_page, section=self.other_section)
            ).status_code,
            403,
        )

    def test_change_article_objeto_permite_so_aquele_artigo(self):
        user = self._criar_usuario("owner_article@example.com")
        assign_perm("change_article", user, self.article)
        self.client.force_login(user)

        # Pode editar aquele artigo especifico
        self.assertEqual(self.client.get(self.url_edit_article()).status_code, 200)

        # NAO pode editar outro artigo (mesmo criar na mesma secao exige
        # permissao na secao/pagina, que ele nao tem)
        self.assertEqual(
            self.client.get(
                self.url_edit_article(
                    page=self.other_page,
                    section=self.other_section,
                    article=self.other_article,
                )
            ).status_code,
            403,
        )

        # change_article no objeto nao sobe a cascata: nao edita secao nem pagina
        self.assertEqual(self.client.get(self.url_edit_section()).status_code, 403)
        self.assertEqual(self.client.get(self.url_edit_page()).status_code, 403)


class NegacaoEAcessoNaoAutenticadoTest(PagesAuthorizationBaseTest):
    """6.4 - Negacao amigavel e redirecionamento de login (Req 2.1, 4.1, 4.2)."""

    def test_autenticado_sem_permissao_recebe_403_e_template_no_permission(self):
        user = self._criar_usuario("semperm@example.com")
        self.client.force_login(user)
        for url in self.todas_rotas_edicao():
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 403, msg=url)
                self.assertTemplateUsed(resp, "pages/no_permission.html")
                # Link mailto de solicitacao de acesso presente no conteudo
                self.assertIn(b"mailto:", resp.content)

    def test_nao_autenticado_e_redirecionado_para_login(self):
        for url in self.todas_rotas_edicao():
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 302, msg=url)
                self.assertTrue(
                    resp.url.startswith("/login"),
                    msg=f"{url} -> {resp.url}",
                )


# ---------------------------------------------------------------------------
# Task 7 - Testes de navegacao publica e paginas institucionais.
#
# Views publicas (GET, sem login): section_detail, article_detail,
# PageDetailView (busca ?q=) e as rotas institucionais medicos/diagnostico/
# justica (SafePageView com fallback "em construcao").
#
# Todas usam get_object_or_404(..., language=get_language()); por isso o setUp
# ativa pt-br e cria os objetos com language='pt-br'.
# ---------------------------------------------------------------------------


class NavegacaoPublicaBaseTest(TestCase):
    """Base para as views publicas: ativa pt-br e expoe helpers de URL."""

    def setUp(self):
        translation.activate(LANG)
        self.addCleanup(translation.deactivate)

    def url_section_detail(self, page_slug, section_id):
        return reverse(
            "section_detail",
            kwargs={"page_slug": page_slug, "section_id": section_id},
        )

    def url_article_detail(self, page_slug, section_id, article_id):
        return reverse(
            "article_detail",
            kwargs={
                "page_slug": page_slug,
                "section_id": section_id,
                "article_id": article_id,
            },
        )


class SectionEArticleDetailTest(NavegacaoPublicaBaseTest):
    """7.1 - section_detail (paginacao 15/pagina, visible) e article_detail
    (Req 5.1, 5.2)."""

    def setUp(self):
        super().setUp()
        self.page = Page.objects.create(
            slug="medicos", title="Medicos", language=LANG
        )
        # Secao visivel com 20 artigos (15 na pagina 1, 5 na pagina 2).
        self.section = Section.objects.create(
            page=self.page, order=1, title="Secao Visivel", visible=True
        )
        for i in range(1, 21):
            Article.objects.create(
                section=self.section,
                order=i,
                title=f"Artigo {i:02d}",
                content=f"conteudo {i}",
            )

        # Secao invisivel (deve dar 404 no detalhe) com 1 artigo.
        self.section_oculta = Section.objects.create(
            page=self.page, order=2, title="Secao Oculta", visible=False
        )
        self.artigo_oculto = Article.objects.create(
            section=self.section_oculta, order=1, title="Oculto", content="x"
        )

    def test_section_detail_pagina_1_tem_15_artigos(self):
        url = self.url_section_detail(self.page.slug, self.section.id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("articles_paginated", resp.context)
        articles_paginated = resp.context["articles_paginated"]
        self.assertEqual(len(articles_paginated.object_list), 15)
        self.assertEqual(articles_paginated.number, 1)
        # Ordenacao por ('order', 'id'): comeca no artigo 01.
        self.assertEqual(articles_paginated.object_list[0].title, "Artigo 01")

    def test_section_detail_pagina_2_tem_5_artigos_restantes(self):
        url = self.url_section_detail(self.page.slug, self.section.id)
        resp = self.client.get(url, {"page": 2})
        self.assertEqual(resp.status_code, 200)
        articles_paginated = resp.context["articles_paginated"]
        self.assertEqual(len(articles_paginated.object_list), 5)
        self.assertEqual(articles_paginated.number, 2)
        self.assertEqual(articles_paginated.object_list[0].title, "Artigo 16")

    def test_section_detail_de_secao_invisivel_retorna_404(self):
        url = self.url_section_detail(self.page.slug, self.section_oculta.id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_article_detail_retorna_200_e_artigo_correto(self):
        artigo = self.section.articles.order_by("order", "id").first()
        url = self.url_article_detail(self.page.slug, self.section.id, artigo.id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["article"].id, artigo.id)
        self.assertEqual(resp.context["section"].id, self.section.id)
        self.assertEqual(resp.context["page_mae"].id, self.page.id)

    def test_article_detail_de_secao_invisivel_retorna_404(self):
        url = self.url_article_detail(
            self.page.slug, self.section_oculta.id, self.artigo_oculto.id
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class BuscaPageDetailViewTest(NavegacaoPublicaBaseTest):
    """7.2 - Busca ?q= em PageDetailView filtra secoes/artigos por
    title/header/content sem duplicar secoes (Req 5.3)."""

    def setUp(self):
        super().setUp()
        self.page = Page.objects.create(slug="faq", title="FAQ", language=LANG)

        # Secao 1: casa pelo TITULO da propria secao ("girassol").
        self.sec_titulo = Section.objects.create(
            page=self.page,
            order=1,
            title="Secao girassol",
            content="texto neutro",
            visible=True,
        )
        # Artigo irrelevante para a busca por girassol.
        Article.objects.create(
            section=self.sec_titulo, order=1, title="A", content="nada aqui"
        )

        # Secao 2: NAO casa no proprio campo, mas um artigo dela casa
        # ("petunia") -> deve aparecer mesmo assim.
        self.sec_por_artigo = Section.objects.create(
            page=self.page,
            order=2,
            title="Secao comum",
            content="texto neutro",
            visible=True,
        )
        Article.objects.create(
            section=self.sec_por_artigo,
            order=1,
            title="Artigo com petunia",
            content="fala de petunia",
        )
        # Secao 3: nada a ver com os termos de busca.
        self.sec_irrelevante = Section.objects.create(
            page=self.page,
            order=3,
            title="Secao sem relacao",
            content="laranja",
            visible=True,
        )

    def test_sem_busca_retorna_todas_as_secoes_visiveis(self):
        resp = self.client.get(reverse("page_detail", kwargs={"slug": "faq"}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["item_count"], 3)
        self.assertEqual(len(resp.context["sections"]), 3)
        self.assertEqual(resp.context["filters"]["q"], "")

    def test_busca_por_titulo_de_secao_filtra(self):
        resp = self.client.get(
            reverse("page_detail", kwargs={"slug": "faq"}), {"q": "girassol"}
        )
        self.assertEqual(resp.status_code, 200)
        ids = [s.id for s in resp.context["sections"]]
        self.assertEqual(ids, [self.sec_titulo.id])
        self.assertEqual(resp.context["item_count"], 1)
        self.assertEqual(resp.context["filters"]["q"], "girassol")

    def test_busca_que_casa_so_em_artigo_ainda_traz_a_secao(self):
        resp = self.client.get(
            reverse("page_detail", kwargs={"slug": "faq"}), {"q": "petunia"}
        )
        self.assertEqual(resp.status_code, 200)
        ids = [s.id for s in resp.context["sections"]]
        self.assertEqual(ids, [self.sec_por_artigo.id])
        self.assertEqual(resp.context["item_count"], 1)

    def test_busca_nao_duplica_secao_quando_casa_em_varios_campos(self):
        # Secao cujo titulo E cujo artigo casam com o mesmo termo: a join com
        # articles poderia duplicar a secao sem o .distinct().
        sec = Section.objects.create(
            page=self.page,
            order=4,
            title="margarida no titulo",
            content="margarida no conteudo",
            visible=True,
        )
        Article.objects.create(
            section=sec, order=1, title="margarida 1", content="margarida"
        )
        Article.objects.create(
            section=sec, order=2, title="margarida 2", content="margarida"
        )

        resp = self.client.get(
            reverse("page_detail", kwargs={"slug": "faq"}), {"q": "margarida"}
        )
        self.assertEqual(resp.status_code, 200)
        ids = [s.id for s in resp.context["sections"]]
        self.assertEqual(ids.count(sec.id), 1, "secao duplicada na busca")
        self.assertEqual(resp.context["item_count"], 1)


class PaginasInstitucionaisTest(NavegacaoPublicaBaseTest):
    """7.3 - Rotas medicos/diagnostico/justica: renderizam Page do banco e
    caem no fallback 'em construcao' sem 500 quando a Page nao existe
    (Req 6.1, 6.2)."""

    def test_medicos_com_page_existente_retorna_200_e_template_de_page(self):
        Page.objects.create(slug="medicos", title="Medicos", language=LANG)
        resp = self.client.get(reverse("medicos"))
        self.assertEqual(resp.status_code, 200)
        # get_template_names da PageDetailView: pages/<slug>.html ou pages/page.html
        templates = [t.name for t in resp.templates if t.name]
        self.assertTrue(
            any(t in ("pages/medicos.html", "pages/page.html") for t in templates),
            msg=f"templates usados: {templates}",
        )

    def test_diagnostico_sem_page_cai_no_fallback_sem_500(self):
        # NAO criar Page 'diagnostico': SafePageView deve capturar o Http404.
        resp = self.client.get(reverse("diagnostico"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pag_em_construcao.html")

    def test_justica_sem_page_cai_no_fallback_sem_500(self):
        resp = self.client.get(reverse("justica"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pag_em_construcao.html")

    def test_justica_com_page_existente_retorna_200_e_template_de_page(self):
        Page.objects.create(slug="justica", title="Justica", language=LANG)
        resp = self.client.get(reverse("justica"))
        self.assertEqual(resp.status_code, 200)
        templates = [t.name for t in resp.templates if t.name]
        self.assertTrue(
            any(t in ("pages/justica.html", "pages/page.html") for t in templates),
            msg=f"templates usados: {templates}",
        )
