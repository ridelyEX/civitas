function hideLoader() {
    const loader = document.getElementById("loader");
    if (loader) {
        loader.classList.add("loader2");
        // Forzar la eliminación después de la transición
        setTimeout(() => {
            loader.style.display = "none";
            loader.style.zIndex = "-1";
        }, 1000);
    }
}

// Ejecutar en múltiples eventos para asegurar que funcione
window.addEventListener("load", function(){
    setTimeout(hideLoader, 500);
});

document.addEventListener("DOMContentLoaded", function(){
    setTimeout(hideLoader, 500);
});

// Respaldo: si después de 2 segundos aún existe, forzar eliminación
setTimeout(function() {
    const loader = document.getElementById("loader");
    if (loader) {
        loader.style.display = "none";
        loader.style.zIndex = "-1";
    }
}, 2000);