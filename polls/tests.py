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

        # Veritabanında oy oluştu mu
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 1)
        vote = Vote.objects.first()
        self.assertIsNone(vote.user)
        self.assertIsNotNone(vote.session_key)

    def test_anonymous_user_cannot_vote_twice(self):
        url = reverse("polls:vote", kwargs={"pk": self.poll.pk})
        payload1 = json.dumps({"option_id": self.option1.id})
        self.client.post(url, data=payload1, content_type="application/json")

        # İkinci oy denemesi
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

        # İkinci oy denemesi
        response2 = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response2.status_code, 400)
        self.assertIn("daha önce oy kullandınız", response2.json()["error"])

    def test_vote_invalid_option_fails(self):
        # Başka bir anketin seçeneği
        other_poll = Poll.objects.create(author=self.author, question="Başka soru")
        other_option = Option.objects.create(poll=other_poll, text="Başka seçenek", position=0)

        url = reverse("polls:vote", kwargs={"pk": self.poll.pk})
        payload = json.dumps({"option_id": other_option.id})
        response = self.client.post(url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("bu ankete ait değil", response.json()["error"])

    def test_detail_view_shows_results_after_voting(self):
        # Kullanıcı oy kullandıktan sonra detay sayfasını yenilediğinde sonuçları görmelidir
        self.client.login(email="oyveren@example.com", password="Parola123!")
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.voter)

        response = self.client.get(reverse("polls:detail", kwargs={"pk": self.poll.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anket Sonuçları")
        self.assertContains(response, "Senin Oyun")
        self.assertContains(response, "1 Toplam Oy")
        self.assertNotContains(response, "Fikrini belirtmek için bir seçeneğe tıkla")
