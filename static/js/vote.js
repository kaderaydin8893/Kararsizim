/**
 * Kararsızım — Oy Verme Etkileşimi (vote.js)
 */

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("poll-container");
    if (!container) return;

    const voteUrl = container.dataset.voteUrl;
    const votingBox = document.getElementById("voting-box");
    const resultsContainer = document.getElementById("results-container");
    const resultsList = document.getElementById("results-list");
    const totalVotesCount = document.getElementById("total-votes-count");
    const voteAlert = document.getElementById("vote-alert");
    const optionButtons = document.querySelectorAll(".vote-option-btn");

    if (!votingBox || optionButtons.length === 0) return;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getCsrfToken() {
        const formToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (formToken && formToken.value) {
            return formToken.value;
        }
        return getCookie("csrftoken");
    }

    function showAlert(message) {
        if (!voteAlert) return;
        voteAlert.textContent = message;
        voteAlert.style.display = "block";
    }

    function hideAlert() {
        if (!voteAlert) return;
        voteAlert.textContent = "";
        voteAlert.style.display = "none";
    }

    function renderResults(data) {
        hideAlert();
        votingBox.style.display = "none";

        if (totalVotesCount) {
            totalVotesCount.textContent = `${data.total_votes} Toplam Oy`;
        }

        if (resultsList) {
            resultsList.innerHTML = "";
            data.options.forEach((opt) => {
                const row = document.createElement("div");
                row.className = `result-row ${opt.is_selected ? "is-selected" : ""}`;

                const pillHtml = opt.is_selected
                    ? '<span class="your-vote-pill">✓ Senin Oyun</span>'
                    : "";

                const fillClass = opt.is_selected ? "fill-selected" : "";

                row.innerHTML = `
                    <div class="result-info">
                        <span class="result-text">
                            ${escapeHtml(opt.text)}
                            ${pillHtml}
                        </span>
                        <span class="result-stats">
                            <strong>%${opt.percentage}</strong>
                            <small class="vote-count-text">(${opt.vote_count} oy)</small>
                        </span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill ${fillClass}" style="width: ${opt.percentage}%;"></div>
                    </div>
                `;
                resultsList.appendChild(row);
            });
        }

        resultsContainer.style.display = "block";
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    optionButtons.forEach((button) => {
        button.addEventListener("click", async () => {
            const optionId = button.dataset.optionId;
            if (!optionId) return;

            hideAlert();

            // Butonları geçici olarak devre dışı bırak
            optionButtons.forEach((btn) => {
                btn.disabled = true;
                btn.classList.add("btn-disabled");
            });
            button.classList.add("btn-loading");

            const csrfToken = getCsrfToken();

            try {
                const response = await fetch(voteUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ option_id: optionId }),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Oy kaydedilirken bir hata oluştu.");
                }

                renderResults(data);
            } catch (err) {
                showAlert(err.message || "Bağlantı hatası oluştu, lütfen tekrar deneyin.");
                optionButtons.forEach((btn) => {
                    btn.disabled = false;
                    btn.classList.remove("btn-disabled");
                });
                button.classList.remove("btn-loading");
            }
        });
    });
});
