document.addEventListener("DOMContentLoaded", () => {
    console.log("aqui hay algo racista");
    try{
        const bbtn = document.getElementById("back");
        const vbtn = document.getElementById("ver-btn");
        const fbtn = document.getElementById("fllw-btn");
        const bback = document.getElementById("bback");

        // Echarle pa atrás en usuarios
        if(bbtn){
            const dirurl = bbtn.dataset.url;
            console.log("le podemos echar pa trás", dirurl);
            bbtn.addEventListener("click", ()=>{
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

    }catch(e){
        console.error("no chambea nadota");
    }
});