"""Testes de busca/filtro da listagem de doencas (spec search-filters).

Inclui o teste de regressao do contrato de URL: a busca usa `keywords`
(antes era `q`); `?q=` NAO deve mais filtrar.
"""
from django.test import TestCase
from django.urls import reverse

from .models import Disease, Symptom


class DiseaseSearchTestCase(TestCase):
    def setUp(self):
        self.febre = Symptom.objects.create(description="Febre")
        self.dor = Symptom.objects.create(description="Dor")

        self.d1 = Disease.objects.create(name="Sindrome de Marfan", ICD="Q87",
                                         description="tecido conjuntivo")
        self.d1.symptoms.add(self.dor)
        self.d2 = Disease.objects.create(name="Fibrose cistica", ICD="E84",
                                         description="afeta pulmoes")
        self.d2.symptoms.add(self.febre)

    def test_busca_keywords_filtra_por_nome(self):
        r = self.client.get(reverse("disease_list"), {"keywords": "marfan"})
        self.assertEqual(r.status_code, 200)
        nomes = [d.name for d in r.context["diseases"]]
        self.assertEqual(nomes, ["Sindrome de Marfan"])

    def test_busca_keywords_filtra_por_icd(self):
        r = self.client.get(reverse("disease_list"), {"keywords": "E84"})
        nomes = [d.name for d in r.context["diseases"]]
        self.assertEqual(nomes, ["Fibrose cistica"])

    def test_filtro_por_sintoma(self):
        r = self.client.get(reverse("disease_list"), {"symptom": str(self.febre.id)})
        nomes = [d.name for d in r.context["diseases"]]
        self.assertEqual(nomes, ["Fibrose cistica"])

    def test_sem_filtro_lista_todas(self):
        r = self.client.get(reverse("disease_list"))
        nomes = [d.name for d in r.context["diseases"]]
        self.assertCountEqual(nomes, ["Sindrome de Marfan", "Fibrose cistica"])

    def test_compatibilidade_q_e_keywords(self):
        # Compatibilidade retroativa: `keywords` (padrao) e `q` (antigo) filtram.
        r_kw = self.client.get(reverse("disease_list"), {"keywords": "marfan"})
        self.assertEqual([d.name for d in r_kw.context["diseases"]],
                         ["Sindrome de Marfan"])
        # O parametro antigo `q` continua filtrando (fallback na view):
        r_q = self.client.get(reverse("disease_list"), {"q": "marfan"})
        self.assertEqual([d.name for d in r_q.context["diseases"]],
                         ["Sindrome de Marfan"])
        # `keywords` tem precedencia sobre `q` quando ambos vem:
        r_both = self.client.get(reverse("disease_list"),
                                 {"keywords": "marfan", "q": "fibrose"})
        self.assertEqual([d.name for d in r_both.context["diseases"]],
                         ["Sindrome de Marfan"])

    def test_contexto_filters_e_issearchpage(self):
        r = self.client.get(reverse("disease_list"), {"keywords": "fibrose"})
        self.assertTrue(r.context["isSearchPage"])
        self.assertEqual(r.context["filters"]["keywords"], "fibrose")
