import json
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from .models import Option, Poll, Vote


def get_user_vote(poll, request):
    """Mevcut kullanıcının (üye veya anonim) bu anketteki oyunu döndürür."""
    if request.user.is_authenticated:
        return Vote.objects.filter(poll=poll, user=request.user).first()
    elif request.session.session_key:
        return Vote.objects.filter(poll=poll, session_key=request.session.session_key).first()
    return None


def calculate_poll_results(poll, user_vote=None):
    """Anket seçeneklerinin oy sayılarını, yüzdelerini ve kullanıcının seçimini hesaplar."""
    options = poll.options.annotate(vote_count=Count("votes")).order_by("position", "id")
    total_votes = sum(option.vote_count for option in options)

    results = []
    for option in options:
        percentage = round((option.vote_count / total_votes * 100), 1) if total_votes > 0 else 0
        is_selected = bool(user_vote and user_vote.option_id == option.id)
        results.append({
            "id": option.id,
            "text": option.text,
            "vote_count": option.vote_count,
            "percentage": percentage,
            "is_selected": is_selected,
        })

    return {
        "options": results,
        "total_votes": total_votes,
        "user_voted": user_vote is not None,
    }


def home(request):
    """Ana sayfa - aktif anket akışı (sayfalama ile)."""
    poll_list = (
        Poll.objects.filter(is_active=True)
        .select_related("author")
        .prefetch_related("options")
    )
    paginator = Paginator(poll_list, 10)
    page_number = request.GET.get("sayfa")
    page_obj = paginator.get_page(page_number)

    return render(request, "polls/home.html", {"page_obj": page_obj})


def poll_detail(request, pk):
    """Anket detay sayfası: oy verilmişse sonuçlar, verilmemişse oy seçenekleri."""
    poll = get_object_or_404(
        Poll.objects.select_related("author").prefetch_related("options"),
        pk=pk,
        is_active=True,
    )

    user_vote = get_user_vote(poll, request)
    poll_results = calculate_poll_results(poll, user_vote=user_vote)

    return render(
        request,
        "polls/poll_detail.html",
        {
            "poll": poll,
            "user_vote": user_vote,
            "poll_results": poll_results,
        },
    )


@require_POST
def vote_poll(request, pk):
    """Oy verme JSON endpoint'i (üye veya anonim)."""
    poll = get_object_or_404(Poll, pk=pk, is_active=True)

    # İstek gövdesinden option_id'yi al (JSON veya POST formu)
    option_id = None
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
            option_id = data.get("option_id")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Geçersiz istek formatı."}, status=400)
    else:
        option_id = request.POST.get("option_id")

    if not option_id:
        return JsonResponse({"error": "Lütfen bir seçenek seçin."}, status=400)

    try:
        option_id = int(option_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Geçersiz seçenek kimliği."}, status=400)

    # Seçeneğin bu ankete ait olup olmadığını kontrol et
    option = poll.options.filter(id=option_id).first()
    if not option:
        return JsonResponse({"error": "Belirtilen seçenek bu ankete ait değil."}, status=400)

    # Oturum ve kullanıcı belirleme
    user = request.user if request.user.is_authenticated else None
    session_key = None

    if user:
        if Vote.objects.filter(poll=poll, user=user).exists():
            return JsonResponse({"error": "Bu ankette daha önce oy kullandınız."}, status=400)
    else:
        # Anonim oy: oturum yoksa oluştur
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        if Vote.objects.filter(poll=poll, session_key=session_key).exists():
            return JsonResponse({"error": "Bu ankette daha önce oy kullandınız."}, status=400)

    # Oy kaydı
    vote = Vote.objects.create(
        poll=poll,
        option=option,
        user=user,
        session_key=session_key,
    )

    # Güncel anket sonuçlarını hesapla ve JSON döndür
    poll_results = calculate_poll_results(poll, user_vote=vote)

    return JsonResponse({
        "success": True,
        "message": "Oyunuz başarıyla kaydedildi.",
        "selected_option_id": option.id,
        "total_votes": poll_results["total_votes"],
        "options": poll_results["options"],
    })
