 //enviar mapa
  function enviar(){
    const text = document.getElementById('dirr').value;
    document.getElementById('dir').value = text;
    closem();
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