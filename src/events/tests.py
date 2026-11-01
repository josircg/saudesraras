"""Testes de busca e filtros da listagem de eventos (spec search-filters)."""
from datetime import datetime, timedelta

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Event

User = get_user_model()


def _now():
    return datetime.now(tz=pytz.UTC)


class EventsSearchTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@x.com", name="User")
        agora = _now()

        # upcoming (futuro), aprovado
        self.futuro = Event.objects.create(
            creator=self.user, title="Congresso raras", description="sobre doencas",
            start_date=agora + timedelta(days=10), end_date=agora + timedelta(days=11),
            approved=True)
        # past (passado), aprovado
        self.passado = Event.objects.create(
            creator=self.user, title="Encontro antigo", description="apoio",
            start_date=agora - timedelta(days=20), end_date=agora - timedelta(days=19),
            approved=True)
        # upcoming NAO aprovado (nao deve aparecer para nao-staff)
        self.nao_aprovado = Event.objects.create(
            creator=self.user, title="Evento pendente raras", description="x",
            start_date=agora + timedelta(days=5), end_date=agora + timedelta(days=6),
            approved=False)

    def _titulos(self, resp):
        ctx = resp.context
        out = []
        for chave in ("upcoming_events", "ongoing_events", "past_events"):
            page = ctx.get(chave)
            if page:
                out += [e.title for e in page]
        return out

    def test_nao_staff_nao_ve_nao_aprovado(self):
        r = self.client.get(reverse("events"))
        self.assertEqual(r.status_code, 200)
        titulos = self._titulos(r)
        self.assertIn("Congresso raras", titulos)
        self.assertNotIn("Evento pendente raras", titulos)  # approved=False

    def test_busca_keywords(self):
        r = self.client.get(reverse("events"), {"keywords": "congresso"})
        titulos = self._titulos(r)
        self.assertIn("Congresso raras", titulos)
        self.assertNotIn("Encontro antigo", titulos)

    def test_filtro_status_upcoming(self):
        r = self.client.get(reverse("events"), {"status": "upcoming"})
        titulos = self._titulos(r)
        self.assertIn("Congresso raras", titulos)
        self.assertNotIn("Encontro antigo", titulos)  # past zerado

    def test_filtro_status_past(self):
        r = self.client.get(reverse("events"), {"status": "past"})
        titulos = self._titulos(r)
        self.assertIn("Encontro antigo", titulos)
        self.assertNotIn("Congresso raras", titulos)

    def test_staff_ve_nao_aprovado(self):
        staff = User.objects.create_superuser(email="s@x.com", name="Staff", password="x")
        self.client.force_login(staff)
        r = self.client.get(reverse("events"))
        titulos = self._titulos(r)
        self.assertIn("Evento pendente raras", titulos)
