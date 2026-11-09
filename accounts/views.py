from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .forms import UserLoginForm, UserRegistrationForm


def register_view(request):
    """Yeni kullanıcı kaydı."""
    if request.user.is_authenticated:
        return redirect("polls:home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Aramıza hoş geldin, @{user.username}!")
            return redirect("polls:home")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """Kullanıcı girişi (e-posta + parola)."""
    if request.user.is_authenticated:
        return redirect("polls:home")

    redirect_to = request.POST.get("next") or request.GET.get("next") or "polls:home"

    if request.method == "POST":
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Tekrar hoş geldin, @{user.username}!")
            return redirect(redirect_to)
    else:
        form = UserLoginForm(request=request)

    return render(request, "accounts/login.html", {"form": form, "next": redirect_to})


@require_POST
def logout_view(request):
    """Kullanıcı çıkışı (yalnızca POST isteklerine izin verilir)."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Başarıyla çıkış yaptınız. Görüşmek üzere!")
    return redirect("polls:home")
