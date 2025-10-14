 //enviar mapa
  function enviar(){
    const text = document.getElementById('dirr').value;
    document.getElementById('dir').value = text;
    modals('close', 'modal');
  }

//función global de modals
function modals(action, modalId) {
    const modal = document.getElementById(modalId);

    if (action === 'open') {
        modal.classList.remove('hidden');
        modal.style.display = 'block';

        // Si es el modal del mapa, inicializar después de mostrar
        if (modalId === 'modal') {
            setTimeout(() => {
                console.log('🗺️ Inicializando mapa desde modal...');
                if (typeof window.openm === 'function') {
                    // Ya no llamar openm, solo inicializar el mapa
                    initializeMap();
                }
            }, 100);
        }
    } else if (action === 'close') {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }
}

  //mostrar mapa
 function openm(){
    document.getElementById('modal').classList.remove('hidden');
    document.getElementById('modal').style.display = 'block';
}

window.onclick = function(event){
    var modal = document.getElementById('modalDoc');
    if (event.target === modal){
        modal.style.display = "none";
    }
}

//boton para añadir los archivos
document.body.addEventListener("click", function(e){
    if (e.target.matches("#search")){
        console.log("puede jalar pa?")
        const fileInput = document.getElementById("file");
        if (fileInput){
            console.log("está jalando pa")
            fileInput.click()
        }
    }
});

//cerrar modal exclusivo
function closem(){
    const modal = document.getElementById('modalDoc2');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('hidden');
    }
}

function validateFileSize(input) {
    if (input.files && input.files[0]) {
        const archivo = input.files[0];
        const limitSize = 5 * 1024 * 1024; //5mb

        if (archivo.size > limitSize) {
            alert('archivo demasiado grande. Máximo 5 MB);
            input.value = '';
            return false;
        }
    }
    return true;
}


/*
document.getElementById('modalDoc2').addEventListener('click', function(e){
    if (e.target == this){
        this.classList.add('hidden');
        this.style.display = 'none';
    }
});
*/