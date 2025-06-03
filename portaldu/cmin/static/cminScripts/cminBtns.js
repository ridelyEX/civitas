document.addEventListener("DOMContentLoaded", () => {
    console.log("aqui hay algo racista");
    try{
        const bbtn = document.getElementById("back");
        if(bbtn){
            const dirurl = bbtn.dataset.url;
            console.log("le podemos echar pa trás", dirurl);
            bbtn.addEventListener("click", ()=>{
                window.location.href = dirurl;
            });
        }
    }catch(e){
        console.error("no chambea nadota");
    }
});