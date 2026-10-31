"""Testes do fluxo de permissoes por objeto geridas no admin.

Cobre a Task 5 da spec `pages-permissioned-editing`:

- 5.1 (Requisitos 1.2, 1.3, 1.4): salvar o usuario pelo
  `CustomUserChangeForm` com objetos selecionados atribui as permissoes
  por objeto via guardian (`assign_perm`); remover da selecao revoga
  (`remove_perm`).
- 5.2 (Requisitos 1.1, 1.2): ao abrir um usuario existente, os seletores
  (`allowed_pages`/`allowed_sections`/`allowed_articles`) sao
  pre-carregados com os objetos cujas permissoes o usuario ja possui
  (`get_objects_for_user`).

O foco e testar o FORM diretamente (mais robusto que simular o POST do
admin e sem depender do rendering). Rodar com --keepdb a partir de src/:

    uv run manage.py test accounts --keepdb
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from guardian.shortcuts import assign_perm, get_objects_for_user

from accounts.admin import CustomUserChangeForm
from pages.models import Page, Section, Article

User = get_user_model()


class PermissoesPorObjetoTestBase(TestCase):
    """Base com o usuario alvo e objetos Page/Section/Article minimos."""

    def setUp(self):
        super().setUp()
        # Usuario comum (nao-staff), alvo das permissoes por objeto.
        # name e obrigatorio no form do User (authtools), entao criamos com
        # um valor para o data do form bater com os campos exigidos.
        self.user = User.objects.create_user(
            email="editor@example.com", name="Editor de Conteudo"
        )

        # Objetos minimos. language deve ser um valor valido de
        # settings.TRANSLATED_LANGUAGES (pt-br). Section/Article herdam o
        # idioma do pai no save().
        self.page = Page.objects.create(
            slug="medicos",
            title="Medicos",
            language="pt-br",
        )
        self.section = Section.objects.create(
            page=self.page,
            order=1,
            title="Secao 1",
        )
        self.article = Article.objects.create(
            section=self.section,
            order=1,
            title="Artigo 1",
            content="Conteudo do artigo",
        )

    def _dados_base_do_form(self):
        """data minimo valido para o ModelForm de User (authtools).

        Campos obrigatorios do form: email, name, password, date_joined.
        Os seletores de permissao (allowed_*) nao sao obrigatorios e sao
        adicionados por cada teste conforme o cenario.
        """
        return {
            "email": self.user.email,
            "name": self.user.name or "",
            # password aqui e apenas um campo de texto do ModelForm
            # (fields='__all__'); mantemos o hash atual do usuario.
            "password": self.user.password or "senha-nao-usada",
            "date_joined": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            # is_active precisa vir marcado: e um BooleanField e, ausente do
            # data, seria salvo como False. Um usuario inativo faz o
            # has_perm (ModelBackend/ObjectPermissionBackend) retornar False
            # para QUALQUER permissao, mesmo com a UserObjectPermission gravada
            # (get_objects_for_user nao filtra por is_active). No admin real o
            # checkbox vem marcado para um usuario ativo; refletimos isso aqui.
            "is_active": True,
        }


class SincronizacaoPermissoesTest(PermissoesPorObjetoTestBase):
    """5.1 - assign/remove de permissoes por objeto ao salvar o form."""

    def test_salvar_com_objetos_atribui_permissoes(self):
        """Selecionar page/section/article concede change_* via assign_perm."""
        data = self._dados_base_do_form()
        data["allowed_pages"] = [self.page.pk]
        data["allowed_sections"] = [self.section.pk]
        data["allowed_articles"] = [self.article.pk]

        form = CustomUserChangeForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        form.save()

        self.assertIn(
            self.page,
            get_objects_for_user(self.user, "pages.change_page", klass=Page),
        )
        self.assertIn(
            self.section,
            get_objects_for_user(self.user, "pages.change_section", klass=Section),
        )
        self.assertIn(
            self.article,
            get_objects_for_user(self.user, "pages.change_article", klass=Article),
        )

        # has_perm por objeto tambem deve refletir a concessao. O guardian
        # mantem um cache de permissoes por instancia de user; recarregamos
        # da base para checar o estado real (em producao cada request tem um
        # user novo).
        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.has_perm("pages.change_page", self.page))
        self.assertTrue(user.has_perm("pages.change_section", self.section))
        self.assertTrue(user.has_perm("pages.change_article", self.article))

    def test_salvar_com_lista_vazia_remove_permissoes(self):
        """Desmarcar os objetos revoga change_* via remove_perm."""
        # Primeiro concede as permissoes diretamente.
        assign_perm("change_page", self.user, self.page)
        assign_perm("change_section", self.user, self.section)
        assign_perm("change_article", self.user, self.article)

        # Sanidade: o usuario realmente tem as permissoes antes de remover.
        self.assertTrue(
            User.objects.get(pk=self.user.pk).has_perm("pages.change_page", self.page)
        )

        # Salvar com os seletores vazios deve remover tudo.
        data = self._dados_base_do_form()
        data["allowed_pages"] = []
        data["allowed_sections"] = []
        data["allowed_articles"] = []

        form = CustomUserChangeForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        form.save()

        self.assertNotIn(
            self.page,
            get_objects_for_user(self.user, "pages.change_page", klass=Page),
        )
        self.assertNotIn(
            self.section,
            get_objects_for_user(self.user, "pages.change_section", klass=Section),
        )
        self.assertNotIn(
            self.article,
            get_objects_for_user(self.user, "pages.change_article", klass=Article),
        )

        user = User.objects.get(pk=self.user.pk)
        self.assertFalse(user.has_perm("pages.change_page", self.page))
        self.assertFalse(user.has_perm("pages.change_section", self.section))
        self.assertFalse(user.has_perm("pages.change_article", self.article))

    def test_salvar_remove_apenas_desmarcados(self):
        """Remover um objeto da selecao nao afeta os que permanecem."""
        assign_perm("change_page", self.user, self.page)
        assign_perm("change_section", self.user, self.section)

        # Mantem a page, remove a section (nao envia allowed_sections).
        data = self._dados_base_do_form()
        data["allowed_pages"] = [self.page.pk]
        data["allowed_sections"] = []

        form = CustomUserChangeForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        form.save()

        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.has_perm("pages.change_page", self.page))
        self.assertFalse(user.has_perm("pages.change_section", self.section))


class PreCarregamentoSeletoresTest(PermissoesPorObjetoTestBase):
    """5.2 - os seletores refletem as permissoes existentes do usuario."""

    def test_seletores_pre_carregam_permissoes_existentes(self):
        """initial de cada seletor contem os objetos ja permitidos."""
        assign_perm("change_page", self.user, self.page)
        assign_perm("change_section", self.user, self.section)
        assign_perm("change_article", self.user, self.article)

        form = CustomUserChangeForm(instance=self.user)

        self.assertIn(self.page, form.fields["allowed_pages"].initial)
        self.assertIn(self.section, form.fields["allowed_sections"].initial)
        self.assertIn(self.article, form.fields["allowed_articles"].initial)

    def test_seletores_vazios_sem_permissoes(self):
        """Sem permissoes concedidas, os seletores iniciam vazios."""
        form = CustomUserChangeForm(instance=self.user)

        self.assertEqual(list(form.fields["allowed_pages"].initial), [])
        self.assertEqual(list(form.fields["allowed_sections"].initial), [])
        self.assertEqual(list(form.fields["allowed_articles"].initial), [])
