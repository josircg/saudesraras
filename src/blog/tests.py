"""Testes de busca e filtros da listagem do blog (spec search-filters)."""
from datetime import datetime

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Post

User = get_user_model()


def _dt(y, m, d):
    return datetime(y, m, d, 12, 0, 0, tzinfo=pytz.UTC)


class BlogSearchTestCase(TestCase):
    def setUp(self):
        self.autor1 = User.objects.create_user(email="a1@x.com", name="Autor Um")
        self.autor2 = User.objects.create_user(email="a2@x.com", name="Autor Dois")

        # status=1 (publicado); status=0 (rascunho, nao deve aparecer)
        self.p1 = Post.objects.create(
            title="Doencas raras no Brasil", slug="p1", author=self.autor1,
            content="texto sobre o SUS", excerpt="resumo um", image="x.png",
            created_on=_dt(2024, 1, 10), status=1, sticky=0)
        self.p2 = Post.objects.create(
            title="Eventos de apoio", slug="p2", author=self.autor2,
            content="conteudo raras aqui", excerpt="resumo dois", image="x.png",
            created_on=_dt(2024, 6, 20), status=1, sticky=1)  # sticky
        self.rascunho = Post.objects.create(
            title="Rascunho raras", slug="p3", author=self.autor1,
            content="nao publicado", excerpt="x", image="x.png",
            created_on=_dt(2024, 3, 1), status=0)

    def test_sem_filtro_lista_apenas_publicados(self):
        r = self.client.get(reverse("blog"))
        self.assertEqual(r.status_code, 200)
        titulos = [p.title for p in r.context["object_list"]]
        self.assertIn("Doencas raras no Brasil", titulos)
        self.assertIn("Eventos de apoio", titulos)
        self.assertNotIn("Rascunho raras", titulos)  # status=0 excluido

    def test_busca_keywords_no_titulo_e_conteudo(self):
        r = self.client.get(reverse("blog"), {"keywords": "raras"})
        titulos = [p.title for p in r.context["object_list"]]
        # p1 casa no titulo, p2 casa no content; rascunho e status=0
        self.assertCountEqual(
            titulos, ["Doencas raras no Brasil", "Eventos de apoio"])

    def test_filtro_por_autor(self):
        r = self.client.get(reverse("blog"), {"author": self.autor2.id})
        titulos = [p.title for p in r.context["object_list"]]
        self.assertEqual(titulos, ["Eventos de apoio"])

    def test_filtro_por_intervalo_de_data(self):
        r = self.client.get(reverse("blog"),
                            {"start_date": "2024-05-01", "end_date": "2024-12-31"})
        titulos = [p.title for p in r.context["object_list"]]
        self.assertEqual(titulos, ["Eventos de apoio"])  # so o de junho

    def test_ordenacao_respeita_sticky_primeiro(self):
        # orderby=title asc, mas sticky (p2) deve vir primeiro
        r = self.client.get(reverse("blog"), {"orderby": "title"})
        titulos = [p.title for p in r.context["object_list"]]
        self.assertEqual(titulos[0], "Eventos de apoio")  # sticky=1 primeiro

    def test_contexto_filters_e_all_authors(self):
        r = self.client.get(reverse("blog"), {"keywords": "raras"})
        self.assertTrue(r.context["isSearchPage"])
        self.assertEqual(r.context["filters"]["keywords"], "raras")
        # all_authors so inclui autores com post publicado (ambos tem)
        nomes = [u.name for u in r.context["all_authors"]]
        self.assertCountEqual(nomes, ["Autor Um", "Autor Dois"])

    def test_query_params_nao_contem_page(self):
        r = self.client.get(reverse("blog"), {"keywords": "raras", "page": "1"})
        self.assertNotIn("page", r.context["query_params"])
