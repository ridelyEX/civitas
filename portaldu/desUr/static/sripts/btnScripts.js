// botones
document.addEventListener("DOMContentLoaded", ()=>{
    console.log("algo racista");
    try{
//Botón global para regresar entre pantallas
      const bbtn = document.getElementById("back");
        if (bbtn) {
            const url = bbtn.dataset.url;
            bbtn.addEventListener("click", () => {
                window.location.href = url;
            });
        }
//Botón para entrar al mapa
   /* const dirbtn = document.getElementById("ubi");
    if(dirbtn){
        const dirurl = dirbtn.dataset.url;
        console.log("algo todavía más racista",dirurl);
        dirbtn.addEventListener("click", ()=>{
            window.location.href = dirurl;
        });
    } */

//Boton para entrar a docs
/*
    const docbtn = document.getElementById("docs");
    if(docbtn){
        const docurl = docbtn.dataset.url;
        console.log("fakiu perro",docurl);
        docbtn.addEventListener("click", ()=>{
            window.location.href = docurl;
        });
    }
*/
//Botón para ir home desde el popup
    const sibtn = document.getElementById("sibtn");
    if(sibtn){
        const sibtnurl = sibtn.dataset.url;
        console.log("sí existo",sibtnurl);
        sibtn.addEventListener("click", ()=>{
            window.location.href = sibtnurl;
        });
    }

//Botón para agregar archivos
/*
   const pbtn = document.getElementById("plus");
   if(pbtn){
       const purl = pbtn.dataset.url;
       console.log("vuelvo a existir");
       pbtn.addEventListener("click", ()=>{
        window.location.href = purl;
       });
   }
*/
//botón para cerrar el mapa
/*
    document.getElementById("close").addEventListener("click", function () {
        window.location.href = this.dataset.url;
    });
*/

    console.log("este mugrero está jalando")
}catch(e){
        console.error("no jala este mugrero", e)
    }
});
