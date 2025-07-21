function updateProgressBar(percentage){
    const updateProgressBar = document.querySelector('.progress-bar');
    const messageDiv = document.getElementById('upload-message');

    updateProgressBar.setAttribute('aria-valuenow', percentage);

    if (percentage === 100){
        messageDiv.textContent = 'Archivo subido exitosamente';
    }
}

function showError(message){
    const messageDiv = document.getElementById('upload-message');

    messageDiv.textContent = `Error: ${message}`;
}