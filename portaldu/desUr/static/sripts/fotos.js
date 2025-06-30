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
            }else{
                clearphoto();
            }
        }
        window.addEventListener('load', startup, false);

        document.addEventListener('DOMContentLoaded', function(){
            var saveBtn = document.getElementById('save');
            if (saveBtn){
                saveBtn.addEventListener('click', function(){
                    var form = saveBtn.closest('form');
                    if (form){
                        form.submit();
                    }else{
                        console.error('No se encontró el formulario para enviar la foto.');
                    }
                });
            }
        });

        })();