// botón back
document.addEventListener("DOMContentLoaded", ()=>{
    console.log("algo racista");
//Botón global para regresar entre pantallas
    const bbtn = document.getElementById("back");
    const url = bbtn.dataset.url;
    bbtn.addEventListener("click", ()=>{
        window.location.href = url;
    });
//Botón para entrar al mapa
    const dirbtn = document.getElementById("ubi");
    if(dirbtn){
        const dirurl = dirbtn.dataset.url;
        console.log("algo todavía más racista",dirurl);
        dirbtn.addEventListener("click", ()=>{
            window.location.href = dirurl;
        });
    }

//Boton para entrar a docs
    const docbtn = document.getElementById("docs");
    if(docbtn){
        const docurl = docbtn.dataset.url;
        console.log("fakiu perro",docurl);
        docbtn.addEventListener("click", ()=>{
            window.location.href = docurl;
        });
    }

//Botón para añadir documentos
const pbtn = document.getElementById("plus");
    if(pbtn){
        const purl = pbtn.dataset.url;
        console.log("a ver cómo añado más campos",purl);
        pbtn.addEventListener("click", ()=>{
            window.location.href = purl;
        });
    }

//Botón para ir home desde el popup (creo)
    const sibtn = document.getElementById("sibtn");
    if(sibtn){
        const sibtnurl = sibtn.dataset.url;
        console.log("sí existo",sibtnurl);
        sibtn.addEventListener("click", ()=>{
            window.location.href = sibtnurl;
        });
    }
});

//botón para cerrar el popup
document.getElementById("close").addEventListener("click", function () {
    window.location.href = this.dataset.url;
});


