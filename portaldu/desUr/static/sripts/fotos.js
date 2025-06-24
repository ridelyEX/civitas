  (function (){
            var streaming = false,
            video = document.querySelector("#video"),
            canvas = document.querySelector("#canvas"),
            foto = document.querySelector("#foto"),
            start = document.querySelector("#start"),
            width = 320,
            height = 0;

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true, audio: false })
                .then(function (stream) {
                    video.srcObject = stream;
                    video.play();
                })
                .catch(function (err) {
                    console.log("Camera error: " + err);
                });
        } else {
            alert("getUserMedia not supported in this browser.");
        }

        video.addEventListener("canplay", function () {
            if (!streaming) {
                height = video.videoHeight / (video.videoWidth / width);
                video.setAttribute("width", width);
                video.setAttribute("height", height);
                canvas.setAttribute("width", width);
                canvas.setAttribute("height", height);
                streaming = true;
            }
        }, false);

        function takepicture() {
            canvas.width = width;
            canvas.height = height;
            canvas.getContext("2d").drawImage(video, 0, 0, width, height);
            var data = canvas.toDataURL("image/png");
            foto.setAttribute("src", data);
        }

        start.addEventListener("click", function (ev) {
            takepicture();
            ev.preventDefault();
        }, false);
        })();