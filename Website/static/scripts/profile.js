function submitProfile(){
    let fName = document.getElementById("fname").value;
    let lName = document.getElementById("lname").value;
    let pNouns = document.getElementById("pnouns").value;
    let email = document.getElementById("email").value;

    const info = fName + ' ' + lName + ' | ' + pNouns + ' | ' + email;
    console.log(info)

    const request = XMLHttpRequest()
    request.open('POST', '/submitInfo/${JSON.stringify(fName)}')
    request.send();
}