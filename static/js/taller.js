"use strict";

document.querySelectorAll("nav a, .subnav a").forEach(enlace => {
    const esFichaCliente = location.pathname.startsWith("/clientes/") &&
        enlace.pathname === "/cuaderno/clientes/";

    if (
        esFichaCliente ||
        enlace.pathname === location.pathname ||
        (enlace.pathname !== "/" &&
            location.pathname.startsWith(enlace.pathname))
    )
        enlace.setAttribute("aria-current", "page");
});

document.querySelectorAll("[data-imprimir]").forEach(boton =>
    boton.addEventListener("click", () => window.print())
);

document.querySelectorAll("[data-medida]").forEach(punto =>
    punto.addEventListener("click", evento => {
        evento.preventDefault();

        const campo = document.getElementById(`id_${punto.dataset.medida}`);

        campo?.focus();
        campo?.scrollIntoView({
            block: "center",
            behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
                ? "instant"
                : "smooth"
        });
    })
);

document.querySelectorAll("form[data-proteger-envio]").forEach(form =>
    form.addEventListener("submit", () => {
        if (form.dataset.enviando) return;

        form.dataset.enviando = "1";
        form.querySelectorAll(
            'button[type="submit"], button:not([type])'
        ).forEach(b => {
            b.disabled = true;
            b.textContent = "Guardando…";
        });
    })
);

window.addEventListener("pageshow", evento => {
    if (evento.persisted) location.reload();
});

let etiqueta = null;

document.querySelectorAll(".etiqueta[draggable]").forEach(tarjeta => {
    tarjeta.addEventListener("dragstart", evento => {
        etiqueta = tarjeta;
        evento.dataTransfer.setData("text/plain", tarjeta.dataset.url);
        tarjeta.classList.add("arrastrando");
    });

    tarjeta.addEventListener("dragend", () => {
        tarjeta.classList.remove("arrastrando");
        etiqueta = null;
        document.querySelectorAll(".destino").forEach(e =>
            e.classList.remove("destino")
        );
    });
});

document.querySelectorAll("[data-etapa]").forEach(columna => {
    columna.addEventListener("dragover", evento => {
        if (etiqueta) {
            evento.preventDefault();
            columna.classList.add("destino");
        }
    });

    columna.addEventListener("dragleave", evento => {
        if (!columna.contains(evento.relatedTarget))
            columna.classList.remove("destino");
    });

    columna.addEventListener("drop", async evento => {
        evento.preventDefault();
        columna.classList.remove("destino");

        if (!etiqueta || etiqueta.dataset.estado === columna.dataset.etapa)
            return;

        const tarjeta = etiqueta;
        tarjeta.draggable = false;

        const aviso = document.getElementById("notificacion");

        try {
            const respuesta = await fetch(tarjeta.dataset.url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "#csrf-tablero input"
                    ).value,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: new URLSearchParams({
                    estado: columna.dataset.etapa
                })
            });
            const datos = await respuesta.json();

            if (!respuesta.ok)
                throw new Error(
                    datos.error ||
                    "No tienes permiso para mover este encargo."
                );

            location.reload();
        } catch (error) {
            aviso.textContent = error instanceof SyntaxError
                ? "Tu sesión cambió. Recarga la página e inténtalo de nuevo."
                : error.message;
            aviso.hidden = false;
            tarjeta.draggable = true;

            setTimeout(() => {
                aviso.hidden = true;
            }, 7000);
        }
    });
});
