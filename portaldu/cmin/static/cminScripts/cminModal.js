function showSendForm(){
    document.getElementById('modal-sender').style.display = 'block';
}

function closeModal(){
    document.getElementById('modal-sender').style.display = 'none';
}

window.onclick = function(event){
    const modal = document.getElementById('modal-sender');
    if (event.target == modal){
        modal.style.display = 'none';
    }
}

document.getElementById('usuario').addEventListener('change', function(){
    const selectedOption = this.options[this.selectedIndex];

    console.log('aqui andamos');
    if (this.value) {
        const email = selectedOption.getAttribute('data-email');
        document.getElementById('correo').value = email;
        console.log('si se printeo', email);
    } else {
        document.getElementById('correo').value = '';
        console.log('no se printeo');
    }
});

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