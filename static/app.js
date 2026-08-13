document.addEventListener("DOMContentLoaded", () => {
    // File upload cards
    document.querySelectorAll(".dropzone").forEach(zone => {
        const input = zone.querySelector("input");
        const fileName = zone.querySelector(".file-name");

        const showFile = () => {
            if (input.files && input.files.length) {
                fileName.textContent = "SELECTED // " + input.files[0].name;
                zone.classList.add("has-file");
            } else {
                fileName.textContent = "";
                zone.classList.remove("has-file");
            }
        };

        input.addEventListener("change", showFile);

        ["dragenter", "dragover"].forEach(event => {
            zone.addEventListener(event, e => {
                e.preventDefault();
                zone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(event => {
            zone.addEventListener(event, e => {
                e.preventDefault();
                zone.classList.remove("dragover");
            });
        });

        zone.addEventListener("drop", e => {
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                showFile();
            }
        });
    });

    // Analysis upload
    const analysisInput = document.querySelector("#analysis-image");
    const analysisFile = document.querySelector(".analysis-file");

    if (analysisInput && analysisFile) {
        analysisInput.addEventListener("change", () => {
            analysisFile.textContent = analysisInput.files.length
                ? "SELECTED // " + analysisInput.files[0].name
                : "";
        });
    }

    // Password reveal
    document.querySelectorAll(".password-toggle").forEach(button => {
        button.addEventListener("click", () => {
            const input = button.parentElement.querySelector("input");
            const visible = input.type === "text";
            input.type = visible ? "password" : "text";
            button.textContent = visible ? "SHOW" : "HIDE";
        });
    });

    // Button loading state on submit
    document.querySelectorAll("form").forEach(form => {
        form.addEventListener("submit", () => {
            const button = form.querySelector(".cyber-btn");
            if (!button) return;

            button.disabled = true;
            const original = button.querySelector("span");
            if (original) original.textContent = "PROCESSING...";
            button.style.opacity = ".7";
        });
    });

    // Subtle pointer glow on cards
    document.querySelectorAll(".cyber-card").forEach(card => {
        card.addEventListener("pointermove", e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.background = `
                radial-gradient(circle at ${x}px ${y}px, rgba(0,229,255,.06), transparent 220px),
                linear-gradient(145deg, rgba(16,22,43,.8), rgba(6,9,19,.85))
            `;
        });

        card.addEventListener("pointerleave", () => {
            card.style.background = "";
        });
    });

    // Tiny boot-style title typing effect
    const terminalLines = document.querySelectorAll(".terminal-line");
    terminalLines.forEach(line => {
        line.style.opacity = "0";
        setTimeout(() => {
            line.style.transition = "opacity .5s";
            line.style.opacity = "1";
        }, 250);
    });
});
