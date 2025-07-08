document.addEventListener('DOMContentLoaded', function() {
    var startBtn = document.getElementById('searchPhoto');
    var cameraInput = document.getElementById('cameraInput');
    if (startBtn && cameraInput) {
        startBtn.addEventListener('click', function() {
            cameraInput.click();
        });
    }
});