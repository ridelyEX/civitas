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
});

document.getElementById("close").addEventListener("click", function () {
    window.location.href = this.dataset.url;
});


