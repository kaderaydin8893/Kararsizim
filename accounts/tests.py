from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="mevcut@example.com",
            username="mevcut_kullanici",
            password="Parola1234!",
        )

    def test_register_page_get(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aramıza Katıl")
        self.assertContains(response, "Kullanıcı Adı")
        self.assertContains(response, "E-posta")

    def test_register_success(self):
        data = {
            "username": "yeni_uye",
            "email": "yeni@example.com",
            "password": "GucluParola123!",
            "password_confirm": "GucluParola123!",
        }
        response = self.client.post(reverse("accounts:register"), data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Yeni kullanıcı oluşmuş olmalı
        self.assertTrue(User.objects.filter(username="yeni_uye").exists())
        # Oturum açılmış ve menüde kullanıcı adı görünüyor olmalı
        self.assertContains(response, "@yeni_uye")
        # E-posta kesinlikle HTML içinde yer almamalı!
        self.assertNotContains(response, "yeni@example.com")

    def test_register_duplicate_email(self):
        data = {
            "username": "farkli_kullanici",
            "email": "mevcut@example.com",
            "password": "Parola1234!",
            "password_confirm": "Parola1234!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu e-posta adresi ile zaten kayıtlı bir hesap var.")

    def test_register_duplicate_username(self):
        data = {
            "username": "MEVCUT_kullanici",
            "email": "baskasi@example.com",
            "password": "Parola1234!",
            "password_confirm": "Parola1234!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu kullanıcı adı zaten alınmış.")

    def test_register_password_mismatch(self):
        data = {
            "username": "uyumsuz_biri",
            "email": "uyumsuz@example.com",
            "password": "Parola1234!",
            "password_confirm": "FarkliParola123!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Girdiğiniz parolalar birbiriyle eşleşmiyor.")

    def test_register_invalid_username_characters(self):
        data = {
            "username": "kullanici adı!",  # Boşluk ve ünlem yasak
            "email": "gecersiz@example.com",
            "password": "Parola1234!",
            "password_confirm": "Parola1234!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "harf, rakam ve alt çizgi")

    def test_login_page_get(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Giriş Yap")

    def test_login_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "mevcut@example.com", "password": "Parola1234!"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@mevcut_kullanici")
        self.assertNotContains(response, "mevcut@example.com")

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "mevcut@example.com", "password": "YanlisParola!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-posta adresi veya parola hatalı.")

    def test_logout_post(self):
        self.client.login(email="mevcut@example.com", password="Parola1234!")
        response = self.client.post(reverse("accounts:logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Başarıyla çıkış yaptınız.")
        self.assertNotContains(response, "@mevcut_kullanici")

    def test_logout_get_method_not_allowed(self):
        self.client.login(email="mevcut@example.com", password="Parola1234!")
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_authenticated_user_redirect_from_login_and_register(self):
        self.client.login(email="mevcut@example.com", password="Parola1234!")
        login_resp = self.client.get(reverse("accounts:login"))
        self.assertRedirects(login_resp, reverse("polls:home"))
        reg_resp = self.client.get(reverse("accounts:register"))
        self.assertRedirects(reg_resp, reverse("polls:home"))
