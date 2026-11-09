from django.shortcuts import render


def home(request):
    """Ana sayfa - anket akışı."""
    return render(request, "polls/home.html")
