(function (){

    //display camera
    var width = 320;
    var height = 0;

    var streaming = false;

    // Get the video, canvas, and foto elements
    var video = null;
    var canvas =null;
    var photo = null;
    var start = null;

    function startup(){
        video = document.getElementById('video');
        canvas = document.getElementById('canvas');
        photo = document.getElementById('photo');
        start = document.getElementById('start');

        navigator.mediaDevices.getUserMedia({video: true, audio: false})
        .then(function(stream){
            video.srcObject = stream;
            video.play();
        })
        .catch(function(err){
            console.log("Ocurrió un error: " + err);
        });

        video.addEventListener('canplay', function(ev){
            if(!streaming){
                height = video.videoHeight / (video.videoWidth/width);

                if (isNaN(height)){
                    height = width / (4/3);
                }
                video.setAttribute('width', width);
                video.setAttribute('height', height);
                canvas.setAttribute('width', width);
                canvas.setAttribute('height', height);
                streaming = true;
            }
        }, false);

        start.addEventListener('click', function(ev){
            takepicture();
            ev.preventDefault();
        }, false);
        clearphoto();
    }

    function clearphoto(){
        var context = canvas.getContext('2d');
        context.fillStyle = "#AAA";
        context.fillRect(0, 0, canvas.width, canvas.height);

        var data = canvas.toDataURL('image/png');
        photo.setAttribute('src', data);
    }

        function takepicture() {
            var context = canvas.getContext('2d');
            if (width && height){
                canvas.width = width;
                canvas.height = height;
                context.drawImage(video, 0, 0, width, height);

                var data = canvas.toDataURL('image/png');
                photo.setAttribute('src', data);
                document.getElementById('webimg').value = data;

                // También guardar en el campo foto_base64
                const fotoBase64Input = document.getElementById('foto_base64');
                if (fotoBase64Input) {
                    fotoBase64Input.value = data;
                }

                console.log('Foto tomada y guardada');
            }else{
                clearphoto();
            }
        }
        window.addEventListener('load', startup, false);

        document.addEventListener('DOMContentLoaded', function(){
            var saveBtn = document.getElementById('save');
            if (saveBtn){
                saveBtn.addEventListener('click', function(event){
                    event.preventDefault();

                    // Obtener la foto en base64
                    const fotoBase64 = document.getElementById('webimg').value;

                    if (fotoBase64 && fotoBase64 !== '') {
                        // Convertir base64 a archivo
                        const base64Data = fotoBase64.split(',')[1]; // Remover el prefijo data:image/png;base64,
                        const byteCharacters = atob(base64Data);
                        const byteNumbers = new Array(byteCharacters.length);

                        for (let i = 0; i < byteCharacters.length; i++) {
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }

                        const byteArray = new Uint8Array(byteNumbers);
                        const file = new File([byteArray], `foto_camara_${Date.now()}.png`, {type: 'image/png'});

                        // Agregar el archivo al formulario principal
                        const mainForm = document.getElementById('mainForm');
                        if (mainForm) {
                            // Remover input anterior si existe
                            const existingInput = mainForm.querySelector('input[name="foto"][data-camera="true"]');
                            if (existingInput) {
                                existingInput.remove();
                            }

                            // Crear nuevo input file
                            const hiddenInput = document.createElement('input');
                            hiddenInput.type = 'file';
                            hiddenInput.name = 'foto';
                            hiddenInput.style.display = 'none';
                            hiddenInput.setAttribute('data-camera', 'true');

                            // Asignar el archivo usando DataTransfer
                            const dt = new DataTransfer();
                            dt.items.add(file);
                            hiddenInput.files = dt.files;

                            mainForm.appendChild(hiddenInput);

                            console.log('Foto de cámara agregada al formulario:', file.name);

                            // Mostrar confirmación visual
                            const confirmMsg = document.createElement('div');
                            confirmMsg.innerHTML = '✅ Foto guardada correctamente';
                            confirmMsg.style.cssText = `
                                position: fixed; top: 20px; right: 20px;
                                background: #4CAF50; color: white;
                                padding: 10px 15px; border-radius: 5px;
                                z-index: 10000; font-size: 14px;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                            `;
                            document.body.appendChild(confirmMsg);
                            setTimeout(() => confirmMsg.remove(), 3000);
                        }
                    } else {
                        alert('Primero debe tomar una foto');
                        return;
                    }

                    // Cerrar el modal
                    modals('close', 'camaraD');
                });
            }
        });

        })();