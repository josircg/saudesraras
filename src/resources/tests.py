"""Testes dos power buttons do admin de resources.

'Edicao Completa' -> pagina de edicao do site; 'Visualizar no site' -> detalhe.
Training resources usam as rotas proprias (editTrainingResource / training_resource).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Category, Keyword, Resource, Theme

User = get_user_model()


class ResourceAdminButtonsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="adm@x.com", name="Adm", password="x")
        self.client.force_login(self.admin)
        self.category = Category.objects.create(text="Cat")

    def _resource(self, training=False):
        r = Resource.objects.create(
            creator=self.admin, name="Rec", url="https://example.com", abstract="a",
            category=self.category, isTrainingResource=training)
        r.keywords.add(Keyword.objects.create(keyword="k"))
        r.theme.add(Theme.objects.create(theme="t"))
        return r

    def test_resource_mostra_edicao_completa_e_visualizar(self):
        r = self._resource()
        html = self.client.get(f"/admin/resources/resource/{r.id}/change/").content.decode()
        self.assertIn(f'href="/editResource/{r.id}"', html)
        self.assertIn(f'href="/resource/{r.id}"', html)

    def test_training_resource_usa_rotas_de_treinamento(self):
        r = self._resource(training=True)
        resp = self.client.get(f"/admin/resources/trainingresource/{r.id}/change/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn(f'href="/editTrainingResource/{r.id}"', html)
        self.assertIn(f'href="/training_resource/{r.id}"', html)
        self.assertNotIn(f'href="/editResource/{r.id}"', html)

    def test_add_nao_mostra_botoes(self):
        # Na tela de inclusao ainda nao ha id: os botoes nao devem aparecer.
        # (Checa pelo rotulo: o campo readonly safe_url tem link proprio.)
        html = self.client.get("/admin/resources/resource/add/").content.decode()
        for label in ("Edição Completa", "Full edit", "Visualizar no site"):
            self.assertNotIn(label, html)
        # safe_url vazio sem id (antes gerava /editResource/None)
        self.assertNotIn('/editResource/None', html)


# ---------------------------------------------------------------------------
# Recorte da capa (image1) em proporcao A4 retrato
# ---------------------------------------------------------------------------
import io
import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from .forms import ResourceForm
from .views import RESOURCE_IMAGE_SIZE, saveImage


class _FakeRequest:
    def __init__(self, files):
        self.FILES = files


class _FakeForm:
    def __init__(self, data):
        self.cleaned_data = data


class ResourceImageA4Test(TestCase):
    def _upload(self, size):
        buf = io.BytesIO()
        Image.new("RGB", size, "white").save(buf, format="PNG")
        return SimpleUploadedFile("capa.png", buf.getvalue(), content_type="image/png")

    def test_saveimage_grava_capa_600x848(self):
        with tempfile.TemporaryDirectory() as media:
            os.makedirs(os.path.join(media, "images"))
            with override_settings(MEDIA_ROOT=media):
                upload = self._upload((1000, 1414))
                form = _FakeForm({"x1": 0, "y1": 0, "width1": 1000, "height1": 1414,
                                  "withImage1": True})
                path = saveImage(_FakeRequest({"image1": upload}), form, "image1", "1")
                with Image.open(os.path.join(media, path)) as saved:
                    self.assertEqual(saved.size, (600, 848))
        self.assertEqual(RESOURCE_IMAGE_SIZE, (600, 848))

    def test_campo_image1_usa_preset_a4_do_crop(self):
        widget = ResourceForm().fields["image1"].widget
        self.assertEqual(widget.attrs.get("data-image-width-option"), 2)


class ResourceListCardA4Test(TestCase):
    """O card da listagem mostra a capa numa moldura A4 com thumbnail retrato."""

    def test_card_com_imagem_gera_thumbnail_retrato(self):
        import re
        with tempfile.TemporaryDirectory() as media:
            os.makedirs(os.path.join(media, "images"))
            Image.new("RGB", (600, 848), "white").save(os.path.join(media, "images", "capa.png"))
            with override_settings(MEDIA_ROOT=media):
                user = User.objects.create_user(email="c@x.com", name="C")
                r = Resource.objects.create(
                    creator=user, name="Com capa", url="https://example.com", abstract="a",
                    category=Category.objects.create(text="Cat"), approved=True,
                    image1="images/capa.png")
                html = self.client.get("/resources").content.decode()
                self.assertIn("aspect-ratio: 210 / 297", html)
                m = re.search(r'data-src="/media/([^"]*capa[^"]*)"', html)
                self.assertIsNotNone(m, "thumbnail da capa nao encontrado no card")
                with Image.open(os.path.join(media, m.group(1))) as thumb:
                    w, h = thumb.size
                self.assertLess(w, h, "thumbnail deveria ser retrato (A4)")
                self.assertEqual((w, h), (280, 396))


class ResourceAdminImageReadonlyTest(TestCase):
    """No admin, so superuser pode trocar a capa (image1); para os demais staff o
    campo e somente leitura, porque o admin nao aplica o recorte A4 do site."""

    def setUp(self):
        from django.contrib.auth.models import Permission
        self.category = Category.objects.create(text="Cat")
        self.superuser = User.objects.create_superuser(email="su@x.com", name="Su", password="x")
        self.staff = User.objects.create_user(email="st@x.com", name="Staff", password="x")
        self.staff.is_staff = True
        self.staff.save()
        self.staff.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="resources",
            codename__in=["change_resource", "view_resource", "change_trainingresource",
                          "view_trainingresource"]))
        self.theme = Theme.objects.create(theme="t")
        self.keyword = Keyword.objects.create(keyword="k")

    def _resource(self, training=False):
        r = Resource.objects.create(
            creator=self.superuser, name="Rec", url="https://example.com", abstract="a",
            category=self.category, isTrainingResource=training, image1="images/antiga.png")
        r.theme.add(self.theme)
        r.keywords.add(self.keyword)
        return r

    def test_superuser_ve_campo_de_upload(self):
        r = self._resource()
        self.client.force_login(self.superuser)
        html = self.client.get(f"/admin/resources/resource/{r.id}/change/").content.decode()
        self.assertIn('name="image1"', html)

    def test_staff_ve_image1_somente_leitura(self):
        r = self._resource()
        self.client.force_login(self.staff)
        resp = self.client.get(f"/admin/resources/resource/{r.id}/change/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn('name="image1"', html)
        self.assertIn("antiga.png", html)  # o valor atual continua visivel

    def test_staff_ve_image1_somente_leitura_em_training(self):
        r = self._resource(training=True)
        self.client.force_login(self.staff)
        resp = self.client.get(f"/admin/resources/trainingresource/{r.id}/change/")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('name="image1"', resp.content.decode())

    def test_staff_nao_consegue_trocar_a_capa_pelo_post(self):
        r = self._resource()
        self.client.force_login(self.staff)
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), "white").save(buf, format="PNG")
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                resp = self.client.post(f"/admin/resources/resource/{r.id}/change/", {
                    "name": "Rec editado", "url": "https://example.com", "abstract": "a",
                    "theme": [self.theme.id], "category": self.category.id,
                    "keywords": [self.keyword.id], "approved": "true", "publisher": "",
                    "image1": SimpleUploadedFile("nova.png", buf.getvalue(),
                                                 content_type="image/png"),
                })
        self.assertEqual(resp.status_code, 302, "o salvamento deveria ter sido aceito")
        r.refresh_from_db()
        self.assertEqual(r.name, "Rec editado")          # os demais campos salvam
        self.assertEqual(r.image1.name, "images/antiga.png")  # a capa nao muda
