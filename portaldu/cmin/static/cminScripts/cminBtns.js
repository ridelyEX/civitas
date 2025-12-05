document.addEventListener("DOMContentLoaded", () => {
    console.log("aqui hay algo racista");
    try{
        const bbtn = document.getElementById("back");
        const vbtn = document.getElementById("ver-btn");
        const fbtn = document.getElementById("fllw-btn");
        const bback = document.getElementById("bback");
        const busers = document.getElementById("bbtn");
        const bencuestas = document.getElementById("encuesta-btn");
        const bexcel = document.getElementById("reporteria-btn");

        // Echarle pa atrás en usuarios
        if(bbtn){
            const dirurl = bbtn.dataset.url;
            console.log("le podemos echar pa trás", dirurl);
            bbtn.addEventListener("click", ()=>{
                window.location.href = dirurl;
            });
        }

        // Crear usuarios
        if (busers) {
            const dirurl = busers.dataset.url;
            console.log("hay usuarios cerca", dirurl);
            bbtn.addEventListener("click", () => {
                window.location.href = dirurl;
            });
        }

        if (vbtn){
            const vurl = vbtn.dataset.url;
            console.log("hay negros cerca", vbtn);
            vbtn.addEventListener("click", ()=>{
                window.location.href = vurl;
            });
        }

        if (fbtn){
            const furl = fbtn.dataset.url;
            console.log("Hay gente no deseada cerca", fbtn);
            fbtn.addEventListener("click", ()=>{
                window.location.href = furl;
            });
        }

        // Echarle pa atrás en tablas

        if(bback){
            const back = bback.dataset.url;
            console.log("le podemos echar pa trás");
            bback.addEventListener("click", ()=>{
                window.location.href = back;
            });
        }

        if (bencuestas) {
            const encuestas = bencuestas.dataset.url;
            console.log("Sí jala pa encuestas");
            bencuestas.addEventListener("click", ()=> {
                window.location.href = encuestas;
            });
        }

        if (bexcel) {
            const reportes = bexcel.dataset.url;
            console.log("Sí jala pa reportes");
            bexcel.addEventListener("click", () => {
                window.location.href = reportes;
            });
        }

    }catch(e){
        console.error("no chambea nadota");
    }
});