/**
 * Kararsızım — Dinamik Anket Seçenek Formu (poll_form.js)
 */

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("options-container");
    const addBtn = document.getElementById("btn-add-option");
    const form = document.getElementById("poll-create-form");

    if (!container || !addBtn || !form) return;

    const MIN_OPTIONS = 2;
    const MAX_OPTIONS = 5;

    function getOptionRows() {
        return container.querySelectorAll(".option-row");
    }

    function updateControls() {
        const rows = getOptionRows();
        const count = rows.length;

        // "Seçenek Ekle" butonu kontrolü
        if (count >= MAX_OPTIONS) {
            addBtn.disabled = true;
            addBtn.classList.add("btn-disabled");
            addBtn.textContent = `En Fazla ${MAX_OPTIONS} Seçenek Eklenebilir`;
        } else {
            addBtn.disabled = false;
            addBtn.classList.remove("btn-disabled");
            addBtn.textContent = "+ Seçenek Ekle";
        }

        // "Kaldır" butonları kontrolü (en az 2 seçenek)
        rows.forEach((row, index) => {
            const removeBtn = row.querySelector(".btn-remove-option");
            const label = row.querySelector(".option-row-number");
            if (label) {
                label.textContent = `${index + 1}. Seçenek`;
            }

            if (removeBtn) {
                if (count <= MIN_OPTIONS) {
                    removeBtn.disabled = true;
                    removeBtn.style.visibility = "hidden";
                } else {
                    removeBtn.disabled = false;
                    removeBtn.style.visibility = "visible";
                }
            }
        });
    }

    function createOptionRow(value = "") {
        const rows = getOptionRows();
        if (rows.length >= MAX_OPTIONS) return;

        const row = document.createElement("div");
        row.className = "option-row";

        row.innerHTML = `
            <div class="option-row-header">
                <span class="option-row-number">Seçenek</span>
                <button type="button" class="btn-remove-option" title="Bu seçeneği kaldır">Kaldır ✕</button>
            </div>
            <input type="text" 
                   name="options" 
                   class="form-control option-input" 
                   placeholder="Seçenek metnini yazın..." 
                   maxlength="100" 
                   value="${escapeHtml(value)}" 
                   required>
        `;

        const removeBtn = row.querySelector(".btn-remove-option");
        removeBtn.addEventListener("click", () => {
            if (getOptionRows().length > MIN_OPTIONS) {
                row.remove();
                updateControls();
            }
        });

        container.appendChild(row);
        updateControls();

        const input = row.querySelector("input");
        if (input && !value) {
            input.focus();
        }
    }

    function escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // Mevcut satırlara kaldır olayı bağla
    container.querySelectorAll(".option-row").forEach((row) => {
        const removeBtn = row.querySelector(".btn-remove-option");
        if (removeBtn) {
            removeBtn.addEventListener("click", () => {
                if (getOptionRows().length > MIN_OPTIONS) {
                    row.remove();
                    updateControls();
                }
            });
        }
    });

    addBtn.addEventListener("click", () => {
        createOptionRow();
    });

    // İlk durumu senkronize et
    updateControls();
});
