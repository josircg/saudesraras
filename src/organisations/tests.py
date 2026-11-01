"""Testes da pagina de detalhe da organizacao (issue 137): doencas e sintomas
associados, link de sintoma que filtra a busca, marcador do mapa e titulo traduzido."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from diseases.models import Disease, Symptom

from .models import Organisation, OrganisationType

User = get_user_model()


class OrganisationDetailDiseasesTest(TestCase):
    def setUp(self):
        translation.activate("pt-br")
        self.addCleanup(translation.deactivate)
        user = User.objects.create_user(email="o@x.com", name="Org Owner")
        self.febre = Symptom.objects.create(description="Febre alta")
        self.disease = Disease.objects.create(name="Doenca Teste", description="descricao")
        self.disease.symptoms.add(self.febre)
        self.org = Organisation.objects.create(
            name="Org", url="https://example.com", description="d",
            orgType=OrganisationType.objects.create(type="Associacao"),
            creator=user, latitude=-22.9, longitude=-43.2, approved=True)
        self.org.diseases.add(self.disease)

    def _html(self, lang="pt-br"):
        self.client.cookies["django_language"] = lang
        resp = self.client.get(reverse("organisation", args=[self.org.id]))
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_lista_doencas_e_sintomas(self):
        html = self._html()
        self.assertIn("Doenca Teste", html)
        self.assertIn("Febre alta", html)
        self.assertIn(reverse("disease_detail", args=[self.disease.id]), html)

    def test_link_do_sintoma_usa_q_symptom_e_filtra(self):
        html = self._html()
        self.assertIn("?q_symptom=Febre%20alta", html)
        self.assertNotIn("?q=Febre", html)
        # a busca de sintomas realmente filtra por esse parametro
        Symptom.objects.create(description="Dor de cabeca")
        resp = self.client.get(reverse("symptoms"), {"q_symptom": "Febre alta"})
        descricoes = [s.description for s in resp.context["symptoms_page"]]
        self.assertEqual(descricoes, ["Febre alta"])

    def test_marcador_usa_icone_do_leaflet(self):
        html = self._html()
        self.assertIn("/static/leaflet/images/marker-icon.png", html)
        self.assertNotIn("/static/images/marker-icon.png", html)

    def test_titulo_das_doencas_traduzido(self):
        esperado = {
            "pt-br": "Doenças sobre as quais esta organização disponibiliza informação",
            "es": "Enfermedades sobre las que esta organización ofrece información",
            "en": "Diseases this organisation provides information about",
        }
        for lang, texto in esperado.items():
            with self.subTest(lang=lang):
                self.assertIn(texto, self._html(lang))

    def test_sem_doencas_nao_mostra_secao(self):
        self.org.diseases.clear()
        html = self._html()
        self.assertNotIn("disponibiliza informação", html)

    def test_sem_aspa_solta_apos_modal(self):
        # O include do modal de exclusao tinha um ' solto que aparecia na pagina
        self.assertNotIn("</div>\n\n\n'\n", self._html())
