// 🌐 Script básico para interacción
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Sistema de Control de Extintores listo.");

    // Ejemplo: mostrar alerta si hay extintores vencidos
    const vencidos = document.querySelectorAll(".estado.vencido");
    if (vencidos.length > 0) {
        alert(`⚠️ Atención: Hay ${vencidos.length} extintor(es) vencido(s).`);
    }
});

