import json
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
        with self.assertRaises(IntegrityError):
            Vote.objects.create(poll=self.poll, option=self.option2, user=self.user)

    def test_unique_session_vote_constraint(self):
        session_key = "test_session_xyz123"
        Vote.objects.create(poll=self.poll, option=self.option1, session_key=session_key)
        with self.assertRaises(IntegrityError):
            Vote.objects.create(poll=self.poll, option=self.option2, session_key=session_key)


class PollViewTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email="yazar2@example.com",
            username="filmsever",
            password="Parola123!",
        )
        self.voter = User.objects.create_user(
            email="oyveren@example.com",
            username="oy_kullanan",
            password="Parola123!",
        )
        self.poll = Poll.objects.create(
            author=self.author,
            question="Bu akşam ne yesem?",
            description="Evde yemek mi yoksa pizza mı?",
        )
        self.option1 = Option.objects.create(poll=self.poll, text="Ev Yemeği", position=0)
        self.option2 = Option.objects.create(poll=self.poll, text="Pizza", position=1)

    def test_home_page_displays_polls(self):
        response = self.client.get(reverse("polls:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu akşam ne yesem?")
        self.assertContains(response, "@filmsever")
        self.assertContains(response, "2 Seçenek")
        self.assertNotContains(response, "yazar2@example.com")

    def test_inactive_poll_not_displayed_on_home(self):
        Poll.objects.create(
            author=self.author,
            question="Eski Pasif Soru",
            is_active=False,
        )
        response = self.client.get(reverse("polls:home"))
        self.assertNotContains(response, "Eski Pasif Soru")

    def test_home_page_pagination(self):
        for i in range(12):
            p = Poll.objects.create(
                author=self.author,
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

    def test_poll_detail_view_anonymous_before_vote(self):
        response = self.client.get(reverse("polls:detail", kwargs={"pk": self.poll.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu akşam ne yesem?")
        self.assertContains(response, "Ev Yemeği")
        self.assertContains(response, "Pizza")
        self.assertContains(response, "voting-box")

    def test_poll_detail_404_for_inactive_poll(self):
        inactive_poll = Poll.objects.create(
            author=self.author,
            question="Pasif Detay Sorusu",
            is_active=False,
        )
        response = self.client.get(reverse("polls:detail", kwargs={"pk": inactive_poll.pk}))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_can_vote_json(self):
        url = reverse("polls:vote", kwargs={"pk": self.poll.pk})
        payload = json.dumps({"option_id": self.option1.id})
        response = self.client.post(url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_votes"], 1)
        self.assertEqual(data["selected_option_id"], self.option1.id)
        self.assertEqual(data["options"][0]["vote_count"], 1)
        self.assertEqual(data["options"][0]["percentage"], 100.0)

        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 1)
        vote = Vote.objects.first()
        self.assertIsNone(vote.user)
        self.assertIsNotNone(vote.session_key)

    def test_anonymous_user_cannot_vote_twice(self):
        url = reverse("polls:vote", kwargs={"pk": self.poll.pk})
        payload1 = json.dumps({"option_id": self.option1.id})
        self.client.post(url, data=payload1, content_type="application/json")

        payload2 = json.dumps({"option_id": self.option2.id})
        response2 = self.client.post(url, data=payload2, content_type="application/json")

        self.assertEqual(response2.status_code, 400)
        data = response2.json()
        self.assertIn("daha önce oy kullandınız", data["error"])
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 1)

    def test_authenticated_user_can_vote_and_cannot_vote_twice(self):
        self.client.login(email="oyveren@example.com", password="Parola123!")
        url = reverse("polls:vote", kwargs={"pk": self.poll.pk})

        payload = json.dumps({"option_id": self.option2.id})
        response = self.client.post(url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.filter(poll=self.poll, user=self.voter).first()
        self.assertIsNotNone(vote)
        self.assertEqual(vote.option, self.option2)

        response2 = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response2.status_code, 400)
        self.assertIn("daha önce oy kullandınız", response2.json()["error"])

    def test_vote_invalid_option_fails(self):
        other_poll = Poll.objects.create(author=self.author, question="Başka soru")
        other_option = Option.objects.create(poll=other_poll, text="Başka seçenek", position=0)

        url = reverse("polls:vote", kwargs={"pk": self.poll.pk})
        payload = json.dumps({"option_id": other_option.id})
        response = self.client.post(url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("bu ankete ait değil", response.json()["error"])

    def test_detail_view_shows_results_after_voting(self):
        self.client.login(email="oyveren@example.com", password="Parola123!")
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.voter)

        response = self.client.get(reverse("polls:detail", kwargs={"pk": self.poll.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anket Sonuçları")
        self.assertContains(response, "Senin Oyun")
        self.assertContains(response, "1 Toplam Oy")
        self.assertNotContains(response, "Fikrini belirtmek için bir seçeneğe tıkla")

    # Faz 4 Testleri: Anket Oluşturma ve Kullanıcı Profili
    def test_create_poll_unauthenticated_redirect(self):
        url = reverse("polls:create")
        response = self.client.get(url, follow=True)
        login_url = reverse("accounts:login")
        self.assertRedirects(response, f"{login_url}?next={url}")
        self.assertContains(response, "Anket oluşturabilmek için lütfen giriş yapın veya üye olun.")

    def test_create_poll_authenticated_get(self):
        self.client.login(email="yazar2@example.com", password="Parola123!")
        response = self.client.get(reverse("polls:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yeni Anket Oluştur")
        self.assertContains(response, "Seçenekler (En az 2, en fazla 5)")

    def test_create_poll_success(self):
        self.client.login(email="yazar2@example.com", password="Parola123!")
        post_data = {
            "question": "Bugün sinemaya mı gitsem?",
            "description": "Vizyonda harika filmler var.",
            "options": ["Evet, git", "Hayır, evde kal", "Arkadaşlarınla buluş"],
        }
        response = self.client.post(reverse("polls:create"), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anketiniz başarıyla paylaşıldı!")
        self.assertContains(response, "Bugün sinemaya mı gitsem?")
        self.assertContains(response, "Evet, git")
        self.assertContains(response, "Hayır, evde kal")
        self.assertContains(response, "Arkadaşlarınla buluş")

        new_poll = Poll.objects.get(question="Bugün sinemaya mı gitsem?")
        self.assertEqual(new_poll.author, self.author)
        self.assertEqual(new_poll.options.count(), 3)

    def test_create_poll_insufficient_options(self):
        self.client.login(email="yazar2@example.com", password="Parola123!")
        post_data = {
            "question": "Yetersiz seçenekli soru?",
            "options": ["Tek Seçenek", ""],
        }
        response = self.client.post(reverse("polls:create"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "en az 2 geçerli seçenek bulunmalıdır")
        self.assertFalse(Poll.objects.filter(question="Yetersiz seçenekli soru?").exists())

    def test_create_poll_too_many_options(self):
        self.client.login(email="yazar2@example.com", password="Parola123!")
        post_data = {
            "question": "Çok fazla seçenekli soru?",
            "options": ["Opt 1", "Opt 2", "Opt 3", "Opt 4", "Opt 5", "Opt 6"],
        }
        response = self.client.post(reverse("polls:create"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "en fazla 5 seçenek bulunabilir")

    def test_create_poll_duplicate_options(self):
        self.client.login(email="yazar2@example.com", password="Parola123!")
        post_data = {
            "question": "Mükerrer seçenekli soru?",
            "options": ["Sinema", "sinema"],  # Büyük-küçük harf duyarsız
        }
        response = self.client.post(reverse("polls:create"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "birden fazla kez girdiniz")

    def test_user_polls_view(self):
        # Yazarın anketleri listelenmeli
        url = reverse("polls:user_polls", kwargs={"username": self.author.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"@{self.author.username}")
        self.assertContains(response, "Bu akşam ne yesem?")
        self.assertContains(response, "1 Anket Paylaştı")
        # E-posta ASLA sayfada bulunmamalı!
        self.assertNotContains(response, self.author.email)

    def test_user_polls_404_for_unknown_user(self):
        url = reverse("polls:user_polls", kwargs={"username": "olmayan_biri_123"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
