from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from .models import Poll


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
    """Anket detay sayfası (soru, açıklama ve seçenekler)."""
    poll = get_object_or_404(
        Poll.objects.select_related("author").prefetch_related("options"),
        pk=pk,
        is_active=True,
    )
    return render(request, "polls/poll_detail.html", {"poll": poll})
