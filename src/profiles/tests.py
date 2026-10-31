from __future__ import unicode_literals
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class PageOpenTestCase(TestCase):
    def test_home_page_exists(self):
        url = reverse("home")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_about_page_exists(self):
        url = reverse("about")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)


User = get_user_model()


class ProfileTestCase(TestCase):
    def test_profiles_created(self):
        u = User.objects.create_user(email="dummy@example.com")
        self.assertIsNotNone(u.profile)


# ---------------------------------------------------------------------------
# Testes da view /about (spec about-page-team, Task 4)
# A view monta a pagina "Sobre" a partir de Profile: equipe (team < 99) e
# colaboradores agrupados por periodo (AAAA.S extraido do title).
# ---------------------------------------------------------------------------
from django.utils import translation
from profiles.models import InterestArea


class AboutViewTestCase(TestCase):
    """Cobre selecao de equipe, agrupamento por periodo, exclusao da area
    'Equipe', fallback de foto e renderizacao nos tres idiomas."""

    def _novo_profile(self, email, name, team=None, title=None, bio="", picture=None):
        # O signal post_save cria o Profile automaticamente; ajustamos ele.
        user = User.objects.create_user(email=email, name=name)
        p = user.profile
        p.team = team
        p.title = title
        p.bio = bio
        if picture is not None:
            p.picture = picture
        p.save()
        return p

    def test_equipe_apenas_team_menor_que_99_ordenada(self):
        self._novo_profile("a@x.com", "Ana", team=2)
        self._novo_profile("b@x.com", "Bruno", team=1)
        self._novo_profile("c@x.com", "Carla", team=99)   # ex-integrante
        self._novo_profile("d@x.com", "Diego", team=None)  # nao e equipe

        r = self.client.get(reverse("about"))
        self.assertEqual(r.status_code, 200)
        equipe = list(r.context["equipe"])
        nomes = [p.user.name for p in equipe]
        # Só team < 99, ordenado por team (Bruno=1 antes de Ana=2)
        self.assertEqual(nomes, ["Bruno", "Ana"])

    def test_colaboradores_agrupados_por_periodo(self):
        self._novo_profile("e@x.com", "Eva", title="Bolsista 2024.1")
        self._novo_profile("f@x.com", "Davi", title="Estagio 2023/2")  # barra
        self._novo_profile("g@x.com", "Gina", title="Bolsista 2024.1 e 2022.2")
        self._novo_profile("h@x.com", "Hugo", title="Colaborador sem periodo")

        r = self.client.get(reverse("about"))
        epp = r.context["equipe_por_periodo"]
        chaves = list(epp.keys())

        # Chaves esperadas e ordem decrescente (mais recente -> antigo)
        self.assertEqual(chaves, ["2024.1", "2023.2", "2022.2"])
        # Gina (dois periodos) aparece em 2024.1 e 2022.2, sem duplicar
        nomes_2024 = [p.user.name for p in epp["2024.1"]]
        self.assertIn("Eva", nomes_2024)
        self.assertIn("Gina", nomes_2024)
        self.assertEqual(nomes_2024.count("Gina"), 1)
        self.assertIn("Gina", [p.user.name for p in epp["2022.2"]])
        # Hugo (sem periodo) nao cria chave
        todos = [p.user.name for lst in epp.values() for p in lst]
        self.assertNotIn("Hugo", todos)

    def test_area_equipe_excluida_do_prefetch(self):
        p = self._novo_profile("i@x.com", "Iris", team=1)
        design = InterestArea.objects.create(interestArea="Design")
        equipe_area = InterestArea.objects.create(interestArea="Equipe")
        p.interestAreas.add(design, equipe_area)

        r = self.client.get(reverse("about"))
        html = r.content.decode("utf-8", "ignore")
        # A area "Design" aparece; a area "Equipe" e excluida do prefetch exibido
        self.assertIn("Design", html)
        # O badge de area nao deve conter "Equipe" (a view exclui via iexact)
        equipe_ctx = list(r.context["equipe"])[0]
        areas = [a.interestArea for a in equipe_ctx.interestAreas.all()]
        self.assertIn("Design", areas)
        self.assertNotIn("Equipe", areas)

    def test_fallback_foto_default(self):
        # Sem picture: usa o default via MEDIA_URL (que resolve para /media/).
        self._novo_profile("j@x.com", "Joana", team=1)
        r = self.client.get(reverse("about"))
        html = r.content.decode("utf-8", "ignore")
        self.assertIn("default_profile.png", html)

    def test_templates_nao_tem_media_hardcoded(self):
        # O caminho nao deve estar hardcoded no TEMPLATE-FONTE; deve vir de
        # picture.url / MEDIA_URL. (No HTML renderizado o MEDIA_URL resolve
        # legitimamente para /media/, por isso checamos o fonte, nao o render.)
        import os
        from django.conf import settings
        base = os.path.join(settings.BASE_DIR, "templates", "pages")
        for lang in ("pt-br", "es", "en"):
            caminho = os.path.join(base, lang, "about.html")
            with open(caminho, encoding="utf-8") as fh:
                fonte = fh.read()
            self.assertNotIn('src="/media/', fonte,
                             msg="caminho de midia hardcoded em %s" % lang)

    def test_about_renderiza_nos_tres_idiomas(self):
        self._novo_profile("k@x.com", "Keila", team=1, title="Bolsista 2024.1")
        for lang in ["pt-br", "es", "en"]:
            with translation.override(lang):
                r = self.client.get(reverse("about"))
                self.assertEqual(r.status_code, 200, msg="idioma %s" % lang)
                html = r.content.decode("utf-8", "ignore")
                dinamico = ("timeline-period-block" in html) or ("team-horizontal" in html)
                self.assertTrue(dinamico, msg="template dinamico ausente em %s" % lang)
