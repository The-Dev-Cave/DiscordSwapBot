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

function on(title) {
    // console.log(this.event.target.classList.contains('over-div'))

    // console.log("toggle on")
    document.getElementById('page-container').style.overflowY = "hidden";
    document.getElementById('listingBrowser').style.overflowY = "hidden";
    document.getElementById(title).style.display = "block";
    document.body.style.overflowY = "hidden";
}

function off(title) {
    // console.log(this.event.target.classList.contains('over-div'))
    if (this.event.target.classList.contains('over-div')) {
        // console.log("toggle off")
        document.getElementById(title).style.display = "none";
        document.getElementById('page-container').style.overflowY = "auto";
        document.getElementById('listingBrowser').style.overflowY = "auto";
        document.body.style.overflowY = "auto";
    }
}



let slideIndex = {};
// showSlides(slideIndex);

function plusSlides(n, id) {
  showSlides(slideIndex[id] += n, id);
}

function currentSlide(n, title) {
  showSlides(slideIndex[id] = n, id);
}

function showSlides(n, id="") {
    if (!(id in slideIndex)){
        slideIndex[id] = 1
    }

  let i;
  let slides = document.getElementsByClassName(`mySlides-${id}`);
  if (n > slides.length) {slideIndex[id] = 1}
  if (n < 1) {slideIndex[id] = slides.length}
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  slides[slideIndex[id]-1].style.display = "block";
}


function contact_popup(post_id, int_party_id, my_user_id) {
  var popup = document.getElementById(`myPopup-${post_id}`);

  if (int_party_id == my_user_id){
      popup.innerHTML = "Can't Make Channels With Yourself"
  } else {
      popup.innerHTML = "Chat Channel Being Created In Post's Server If Not Already Made<br>You Will Be Pinged When Done"
  }

  popup.classList.toggle("show");

  new Promise((resolve) => {
    setTimeout(() => {
      resolve(popup.classList.toggle("show"));
    }, 5000);
  });

}

function profile_popup(post_id) {
  var popup = document.getElementById(`myPopup-prof-${post_id}`);

  // if (int_party_id == my_user_id){
  //     popup.innerHTML = "Can't Make Channels With Yourself"
  // } else {
  //     popup.innerHTML = "Chat Channel Being Created In Post's Server If Not Already Made<br>You Will Be Pinged When Done"
  // }

  popup.classList.toggle("show");

  new Promise((resolve) => {
    setTimeout(() => {
      resolve(popup.classList.toggle("show"));
    }, 3000);
  });

}


function btnOnClick(posttype, postid, user_id) {
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", `/contact-lister/${posttype}/${postid}/${user_id}`, true);
    xhttp.send();
}

function btnViewProfile(author_id, user_id, guild_id) {
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", `/view-profile/${author_id}/${user_id}/${guild_id}`, true);
    xhttp.send();
}