// botón back
document.addEventListener("DOMContentLoaded", ()=>{
    console.log("algo racista");

    const bbtn = document.getElementById("back");
    const url = bbtn.dataset.url;
    bbtn.addEventListener("click", ()=>{
        window.location.href = url;
    });
    
    const dirbtn = document.getElementById("ubi");
    if(dirbtn){
        const dirurl = dirbtn.dataset.url;
        console.log("algo todavía más racista",dirurl);
        dirbtn.addEventListener("click", ()=>{
            window.location.href = dirurl;
        });
    }

    const sibtn = document.getElementById("sibtn");
    if(sibtn){
        const sibtnurl = sibtn.dataset.url;
        console.log("sí existo",sibtnurl);
        sibtn.addEventListener("click", ()=>{
            window.location.href = sibtnurl;
        });
    }

    const mNext = document.getElementById("mNext");
    if(mNext){
        const latInput = document.getElementById("latInput");
        const lngInput = document.getElementById("lngInput");

        const iframe = document.querySelector("iframe");
        if (!iframe) return;
        iframe.addEventListener("load", () => {
            const innerDoc = iframe.contentDocument || iframe.contentWindow.document;
        
            innerDoc.addEventListener("click", (e) => {
                const popup = innerDoc.querySelector(".leaflet-popup-content");
                if (!popup) return;
        
                const match = popup.innerText.match(/Lat:\s*([-\d.]+)\s*Lon:\s*([-\d.]+)/);
                if (match) {
                latInput.value = match[1];
                lngInput.value = match[2];
                console.log("Coordenadas guardadas:", match[1], match[2]);
                }
            });
        });
    } 
});

document.getElementById("close").addEventListener("click", function () {
    window.location.href = this.dataset.url;
});



