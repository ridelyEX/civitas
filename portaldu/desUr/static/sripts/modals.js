 //enviar mapa
  function enviar(){
    const text = document.getElementById('dirr').value;
    document.getElementById('dir').value = text;
    modals('close', 'modal');
  }

//función global de modals
function modals(action, id){
    const modal = document.getElementById(id);
    if (action === 'open'){
    console.log("este mugrero sí está chambeando");
        modal.classList.remove('hidden');
        modal.style.display = 'block';
    } else {
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

//procesar formulario con AJAX

document.getElementById("upDocs").addEventListener('submit', async function(e){
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    const documentElement = document.getElementById('document');

    const fileInput = document.getElementById('file');

    if (!fileInput.files.length){
        documentElement.innerText = "seleccione un archivo";
        documentElement.style.color = "red";
        return;
    }

    try {
        documentElement.innerText = "Subiendo documento...";
        documentElement.style.color = "blue";

        formData.append('action', 'savedocs');
    
        const response = await fetch('/desUr/soliData/',{
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData

        });
        const result = await response.json();

        if (result.success){
            documentElement.innerText = "Documento subido";
            documentElement.style.color = "green";

            setTimeout(()=>{
                form.reset();
                documentElement.innerText = "";
            }, 1500);
        }else{
            documentElement.innerText = "Error: " + (result.error || "error desconocido");
            documentElement.style.color = "red";
        }
        if (result.success) {
            document.getElementById('document').innerText = "Se subió el documento";
            closem();
        }else{
            document.getElementById('document').innerText = "Error: " +result.error;
        }
    } catch (error){
        console.error('Error:', error);
        documentElement.innerText = "Error de conexión";
        documentElement.style.color = "red";
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

document.getElementById('modalDoc2').addEventListener('click', function(e){
    if (e.target == this){
        this.classList.add('hidden');
        this.style.display = 'none';
    }
});