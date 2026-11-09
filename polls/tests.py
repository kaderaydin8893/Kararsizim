from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from .models import Option, Poll, Vote

User = get_user_model()


class PollModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="yazar@example.com",
            username="anket_yazari",
            password="Parola123!",
        )
        self.poll = Poll.objects.create(
            author=self.user,
            question="Hangi filmi izlesem?",
            description="Aksiyon mu komedi mi kararsız kaldım.",
        )
        self.option1 = Option.objects.create(poll=self.poll, text="Film A", position=0)
        self.option2 = Option.objects.create(poll=self.poll, text="Film B", position=1)

    def test_model_str_representations(self):
        self.assertEqual(str(self.poll), "Hangi filmi izlesem?")
        self.assertIn("Film A", str(self.option1))

    def test_unique_user_vote_constraint(self):
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.user)
        # İkinci oy UniqueConstraint nedeniyle hata fırlatmalıdır
        with self.assertRaises(IntegrityError):
            Vote.objects.create(poll=self.poll, option=self.option2, user=self.user)

    def test_unique_session_vote_constraint(self):
        session_key = "test_session_xyz123"
        Vote.objects.create(poll=self.poll, option=self.option1, session_key=session_key)
        # Aynı session_key ile ikinci oy engellenmelidir
        with self.assertRaises(IntegrityError):
            Vote.objects.create(poll=self.poll, option=self.option2, session_key=session_key)


class PollViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="yazar2@example.com",
            username="filmsever",
            password="Parola123!",
        )
        self.poll = Poll.objects.create(
            author=self.user,
            question="Bu akşam ne yesem?",
            description="Evde yemek mi yoksa pizza mı?",
        )
        Option.objects.create(poll=self.poll, text="Ev Yemeği", position=0)
        Option.objects.create(poll=self.poll, text="Pizza", position=1)

    def test_home_page_displays_polls(self):
        response = self.client.get(reverse("polls:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu akşam ne yesem?")
        self.assertContains(response, "@filmsever")
        self.assertContains(response, "2 Seçenek")
        # E-posta hiçbir yerde yer almamalı!
        self.assertNotContains(response, "yazar2@example.com")

    def test_inactive_poll_not_displayed_on_home(self):
        inactive_poll = Poll.objects.create(
            author=self.user,
            question="Eski Pasif Soru",
            is_active=False,
        )
        response = self.client.get(reverse("polls:home"))
        self.assertNotContains(response, "Eski Pasif Soru")

    def test_home_page_pagination(self):
        # 10'dan fazla anket oluşturarak sayfalama kontrolü
        for i in range(12):
            p = Poll.objects.create(
                author=self.user,
                question=f"Test Soru {i}",
            )
            Option.objects.create(poll=p, text="A", position=0)
            Option.objects.create(poll=p, text="B", position=1)

        response_page1 = self.client.get(reverse("polls:home"))
        self.assertEqual(response_page1.status_code, 200)
        self.assertContains(response_page1, "Sayfa 1 / 2")

        response_page2 = self.client.get(reverse("polls:home") + "?sayfa=2")
        self.assertEqual(response_page2.status_code, 200)
        self.assertContains(response_page2, "Sayfa 2 / 2")

    def test_poll_detail_view_anonymous(self):
        # Giriş yapmamış kullanıcı anketi görüntüleyebilir
        response = self.client.get(reverse("polls:detail", kwargs={"pk": self.poll.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu akşam ne yesem?")
        self.assertContains(response, "Evde yemek mi yoksa pizza mı?")
        self.assertContains(response, "@filmsever")
        self.assertContains(response, "Ev Yemeği")
        self.assertContains(response, "Pizza")
        self.assertNotContains(response, "yazar2@example.com")

    def test_poll_detail_404_for_inactive_poll(self):
        inactive_poll = Poll.objects.create(
            author=self.user,
            question="Pasif Detay Sorusu",
            is_active=False,
        )
        response = self.client.get(reverse("polls:detail", kwargs={"pk": inactive_poll.pk}))
        self.assertEqual(response.status_code, 404)
