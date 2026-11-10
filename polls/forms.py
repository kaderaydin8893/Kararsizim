from django import forms
from django.core.exceptions import ValidationError
from .models import Poll


class PollCreateForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ("question", "description")
        widgets = {
            "question": forms.TextInput(
                attrs={
                    "placeholder": "örn. Akşam yemeğinde pizza mı, sushi mi?",
                    "autocomplete": "off",
                    "maxlength": "200",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Kararsızlığın hakkında biraz daha detay vermek ister misin? (İsteğe bağlı)",
                    "rows": 3,
                    "maxlength": "500",
                }
            ),
        }
        labels = {
            "question": "Anket Sorusu",
            "description": "Açıklama",
        }
        help_texts = {
            "question": "En fazla 200 karakter.",
            "description": "İsteğe bağlı, en fazla 500 karakter.",
        }

    def clean_question(self):
        question = self.cleaned_data.get("question", "").strip()
        if len(question) < 5:
            raise ValidationError("Anket sorusu en az 5 karakter olmalıdır.")
        return question

    @staticmethod
    def clean_options(raw_options):
        """
        Dinamik seçenek listesini doğrular ve temizler.
        Kurallar:
        - Boş seçenekleri eler.
        - En az 2, en fazla 5 seçenek olmalıdır.
        - Her seçenek en fazla 100 karakter olmalıdır.
        - Mükerrer seçeneklere izin verilmez (büyük-küçük harf duyarsız).
        """
        cleaned_options = []
        seen_lower = set()

        for opt in raw_options:
            text = opt.strip()
            if not text:
                continue

            if len(text) > 100:
                raise ValidationError(f"'{text[:30]}...' seçeneği çok uzun. En fazla 100 karakter olabilir.")

            lower_text = text.lower()
            if lower_text in seen_lower:
                raise ValidationError(f"'{text}' seçeneğini birden fazla kez girdiniz.")

            seen_lower.add(lower_text)
            cleaned_options.append(text)

        if len(cleaned_options) < 2:
            raise ValidationError("Bir ankette en az 2 geçerli seçenek bulunmalıdır.")

        if len(cleaned_options) > 5:
            raise ValidationError("Bir ankette en fazla 5 seçenek bulunabilir.")

        return cleaned_options
