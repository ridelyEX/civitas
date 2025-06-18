function showSendForm(){
    document.getElementById('modal-sender').style.display = 'block';
}

function closeModal(){
    document.getElementById('modal-sender').style.display = 'none';
}

window.onclick = function(event){
    const modal = document.getElementById('modal-sender');
    if (event.targt == modal){
        modal.style.display = 'none';
    }
}