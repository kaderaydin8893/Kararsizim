from django.conf import settings
from django.db import models
from django.db.models import Q


class Poll(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="polls",
        verbose_name="Yazar",
    )
    question = models.CharField(
        max_length=200,
        verbose_name="Soru",
        help_text="En fazla 200 karakter.",
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Açıklama",
        help_text="İsteğe bağlı, en fazla 500 karakter.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif mi?",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma Tarihi",
    )

    class Meta:
        verbose_name = "Anket"
        verbose_name_plural = "Anketler"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question


class Option(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Anket",
    )
    text = models.CharField(
        max_length=100,
        verbose_name="Seçenek Metni",
    )
    position = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Sıralama",
    )

    class Meta:
        verbose_name = "Seçenek"
        verbose_name_plural = "Seçenekler"
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.poll.question} - {self.text}"


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Anket",
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Seçenek",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="votes",
        verbose_name="Kullanıcı",
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name="Oturum Anahtarı",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oy Tarihi",
    )

    class Meta:
        verbose_name = "Oy"
        verbose_name_plural = "Oylar"
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "user"],
                condition=Q(user__isnull=False),
                name="unique_poll_user_vote",
            ),
            models.UniqueConstraint(
                fields=["poll", "session_key"],
                condition=Q(session_key__isnull=False),
                name="unique_poll_session_vote",
            ),
        ]

    def __str__(self):
        voter = self.user.username if self.user else f"Anonim ({self.session_key})"
        return f"{voter} -> {self.option.text}"
