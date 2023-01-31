document.getElementById("editBtn").onclick = function(){
    
    var inputs = document.getElementsByTagName("input");
    for (var i = 0; i < inputs.length; i++) {
        if(inputs[i].disabled){
            inputs[i].disabled = false;
        } else {
            inputs[i].disabled = true;
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