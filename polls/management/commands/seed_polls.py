from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from polls.models import Option, Poll, Vote

User = get_user_model()


class Command(BaseCommand):
    help = "Ana sayfa için renkli ve eğlenceli örnek anketler oluşturur."

    def handle(self, *args, **options):
        self.stdout.write("Örnek kullanıcılar ve eğlenceli anketler hazırlanıyor...")

        # 1. Örnek yazarlar oluştur veya al
        users_data = [
            ("merve_kararsiz", "merve@example.com", "Merve K."),
            ("burak_gurme", "burak@example.com", "Burak Gurme"),
            ("sinema_tutkunu", "sinema@example.com", "Ece Sinemada"),
            ("geveze_panda", "panda@example.com", "Tembel Panda"),
        ]

        created_users = []
        for username, email, _ in users_data:
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password="OrnekParola123!",
                )
            created_users.append(user)

        # 2. Eğlenceli anket havuzu
        sample_polls = [
            {
                "author": created_users[1],
                "question": "Akşam yemeğinde ne söyleyelim? Acil karar lazım! 🍕🍔",
                "description": "Bütün gün çalıştık, yemek yapacak hal kalmadı. Mideler isyanda!",
                "options": [
                    "Çıtır Lahmacun & Bol Köpüklü Ayran 🌯",
                    "Bol Malzemeli İtalyan Pizzası 🍕",
                    "Ev Yapımı Burger & Baharatlı Patates 🍔",
                    "Hafif ve Leziz Sushi Tabağı 🍣",
                ],
                "votes_distribution": [14, 22, 18, 7],
            },
            {
                "author": created_users[0],
                "question": "Güne başlarken senin vazgeçilmezin hangisi? ☕🫖",
                "description": "Pazartesi sabahı enerjisini ne toplar, tarafını seç!",
                "options": [
                    "Sert bir Filtre Kahve / Espresso ☕",
                    "Tavşan kanı demli Türk Çayı & Simit 🫖",
                    "Taze sıkılmış Portakal Suyu 🍊",
                    "Alarmı 5 dakika daha ertelemek 😴",
                ],
                "votes_distribution": [35, 42, 11, 29],
            },
            {
                "author": created_users[2],
                "question": "Bu akşam ne tarz bir film izleyelim? 🍿🎬",
                "description": "Mısırlar patlatıldı, ekran başına geçildi ama 1 saattir film seçemedik...",
                "options": [
                    "Beyin yakan ters köşeli Bilim Kurgu 🤯",
                    "Gülmekten karnımıza ağrı sokacak Komedi 😂",
                    "Kalp atışını ikiye katlayan Gerilim / Gizem 😱",
                    "İçimizi ısıtacak sıcacık bir Animasyon 🎈",
                ],
                "votes_distribution": [19, 15, 24, 12],
            },
            {
                "author": created_users[3],
                "question": "Hangi süper güce sahip olmak isterdin? ✨🦸",
                "description": "Tek bir dilek hakkın olsa hangisini seçerdin?",
                "options": [
                    "İstediğin yere anında ışınlanabilmek 🚀",
                    "Zamanı 1 saat geri alabilmek ⏳",
                    "İnsanların zihnini okuyabilmek 🧠",
                    "Ne yersen ye asla kilo almamak 🍕",
                    "Tamamen görünmez olabilmek 👻",
                ],
                "votes_distribution": [28, 31, 16, 45, 9],
            },
            {
                "author": created_users[0],
                "question": "İdeal bir hafta sonu sabahı senin için nasıldır? 🌿🛌",
                "description": "Haftanın yorgunluğunu atmak için en doğru aktiviteyi oylayalım.",
                "options": [
                    "Öğlene kadar yataktan çıkmamak & Dizi maratonu 📺",
                    "Erkenden kalkıp sahilde yürüyüş & Zengin kahvaltı 🍳",
                    "Doğaya kaçıp kamp veya sessiz piknik 🌲",
                    "Kulaklığı takıp şehri rastgele turlamak 🎧",
                ],
                "votes_distribution": [23, 19, 14, 17],
            },
            {
                "author": created_users[2],
                "question": "Tatile çıkacak olsan ilk tercihin neresi olurdu? ✈️🏝️",
                "description": "Valizler hazır sayılır, peki istikamet neresi?",
                "options": [
                    "Ege ve Akdeniz'in turkuaz koyları 🌊",
                    "Karadeniz'in sisli ve serin yaylaları 🏔️",
                    "Tarih ve kültür kokan Avrupa sokakları 🏰",
                    "Uzak Doğu'nun mistik tapınakları ve egzotik lezzetleri ⛩️",
                ],
                "votes_distribution": [26, 15, 30, 21],
            },
        ]

        created_poll_count = 0
        for data in sample_polls:
            poll, created = Poll.objects.get_or_create(
                question=data["question"],
                defaults={
                    "author": data["author"],
                    "description": data["description"],
                    "is_active": True,
                },
            )

            if created:
                created_poll_count += 1
                for idx, opt_text in enumerate(data["options"]):
                    option = Option.objects.create(
                        poll=poll,
                        text=opt_text,
                        position=idx,
                    )

                    # Gerçekçi oy dağılımı ekle
                    vote_count = data["votes_distribution"][idx] if idx < len(data["votes_distribution"]) else 5
                    for v_idx in range(vote_count):
                        dummy_session = f"seed_{poll.id}_{option.id}_{v_idx}"
                        Vote.objects.create(
                            poll=poll,
                            option=option,
                            session_key=dummy_session,
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Tebrikler! {created_poll_count} yeni renkli anket ve oylar başarıyla oluşturuldu."
            )
        )
