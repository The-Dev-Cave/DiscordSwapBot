var editBtn = document.getElementById("editBtn")
if (editBtn){
    editBtn.onclick = function(){
    
        var inputs = document.getElementsByTagName("input");
        var imgBox = document.getElementById("imgBox")
        var hoverBox = document.getElementById("hoverBox")
        
        for (var i = 0; i < inputs.length; i++) {
            if(inputs[i].disabled){
                inputs[i].disabled = false;
                imgBox.classList.toggle('disabled')
                hoverBox.classList.toggle('disabled')
            } else {
                inputs[i].disabled = true;
                imgBox.classList.toggle('disabled')
                hoverBox.classList.toggle('disabled')
            }
        }
    }
}


window.onload = function () {
    var fileupload = document.getElementById("FileUpload1");
    var image = document.getElementById("imgFileUpload");
    image.onclick = function () {
        fileupload.click();
    };
    fileupload.onchange = function () {
        document.getElementById('pfpForm').submit()
    }
};