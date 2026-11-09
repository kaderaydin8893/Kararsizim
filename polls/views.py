import json
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import PollCreateForm
from .models import Option, Poll, Vote

User = get_user_model()


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

    option = poll.options.filter(id=option_id).first()
    if not option:
        return JsonResponse({"error": "Belirtilen seçenek bu ankete ait değil."}, status=400)

    user = request.user if request.user.is_authenticated else None
    session_key = None

    if user:
        if Vote.objects.filter(poll=poll, user=user).exists():
            return JsonResponse({"error": "Bu ankette daha önce oy kullandınız."}, status=400)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        if Vote.objects.filter(poll=poll, session_key=session_key).exists():
            return JsonResponse({"error": "Bu ankette daha önce oy kullandınız."}, status=400)

    vote = Vote.objects.create(
        poll=poll,
        option=option,
        user=user,
        session_key=session_key,
    )

    poll_results = calculate_poll_results(poll, user_vote=vote)

    return JsonResponse({
        "success": True,
        "message": "Oyunuz başarıyla kaydedildi.",
        "selected_option_id": option.id,
        "total_votes": poll_results["total_votes"],
        "options": poll_results["options"],
    })


def create_poll(request):
    """Yeni anket oluşturma (Sadece giriş yapmış kullanıcılar)."""
    if not request.user.is_authenticated:
        messages.info(request, "Anket oluşturabilmek için lütfen giriş yapın veya üye olun.")
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    options_error = None
    options_data = ["", ""]  # Başlangıçta 2 boş seçenek

    if request.method == "POST":
        form = PollCreateForm(request.POST)
        raw_options = request.POST.getlist("options")
        options_data = raw_options if raw_options else ["", ""]

        try:
            cleaned_options = PollCreateForm.clean_options(raw_options)
        except ValidationError as e:
            options_error = e.message
            cleaned_options = None

        if form.is_valid() and not options_error:
            with transaction.atomic():
                poll = form.save(commit=False)
                poll.author = request.user
                poll.save()

                for index, option_text in enumerate(cleaned_options):
                    Option.objects.create(
                        poll=poll,
                        text=option_text,
                        position=index,
                    )

            messages.success(request, "Anketiniz başarıyla paylaşıldı!")
            return redirect("polls:detail", pk=poll.pk)
    else:
        form = PollCreateForm()

    return render(
        request,
        "polls/poll_create.html",
        {
            "form": form,
            "options_data": options_data,
            "options_error": options_error,
        },
    )


def user_polls(request, username):
    """Belirli bir kullanıcının paylaştığı anketlerin listesi (E-posta ASLA gösterilmez)."""
    user_obj = get_object_or_404(User, username=username)

    poll_list = (
        Poll.objects.filter(author=user_obj, is_active=True)
        .prefetch_related("options")
        .order_by("-created_at")
    )

    paginator = Paginator(poll_list, 10)
    page_number = request.GET.get("sayfa")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "polls/user_polls.html",
        {
            "profile_user": user_obj,
            "page_obj": page_obj,
            "total_polls": poll_list.count(),
        },
    )
