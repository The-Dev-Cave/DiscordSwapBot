let subMenu = document.getElementById("subMenu");
function toggleMenu(){
    subMenu.classList.toggle("open-menu");
}

function toggleMobileMenu(menu) {
    menu.classList.toggle('open');
}

function detectMob() {
    const toMatch = [
        /Android/i,
        /webOS/i,
        /iPhone/i,
        /iPad/i,
        /iPod/i,
        /BlackBerry/i,
        /Windows Phone/i
    ];
    
    return toMatch.some((toMatchItem) => {
        return navigator.userAgent.match(toMatchItem);
    });
}

// var toConstruction = function (event){
//     if (window.innerWidth < 885){
//         window.location.href = "/construction";
//     }
// };
// window.addEventListener('resize', toConstruction, false);
// window.addEventListener('load', toConstruction, false);