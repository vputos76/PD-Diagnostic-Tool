// Assign variables to each input element to check if it is empty or not
const inputs = [
    document.getElementById("fname"),
    document.getElementById("lname"),
    document.getElementById("dob"),
    document.getElementById("sex"),
    document.getElementById("attending"),
]
// Assign variable name to photo upload input to check if file has been uploaded
const photoInput = document.getElementById("photo-upload")
// Boolean to flag when a file has been uploaded
let fileUploaded = false

// Assign variabel to "Update" button to enable/disable it
const updateButton = document.getElementById("update-patient-info")


// Assign event listener to each of the items in "inputs"
inputs.forEach(input => {if(input) {input.addEventListener("input", toggleUpdate);}})

// Raise flag when photo has been uploaded
photoInput.addEventListener("change", function() {
    if (photoInput.files.length > 0) {
       fileUploaded = true
       toggleUpdate() 
    }
    else {
        fileUploaded = false
        toggleUpdate() 
    }
}
)


function toggleUpdate() {
    // Create an array that checks if every input field has been filled out
    let booleanArray = inputs.map(input => input.value.trim() !== "")
    // If every input field is filled out, enable the button, else disable it
    if (booleanArray.every(value => value === true) && fileUploaded === true){
        updateButton.disabled = false;}
    else {updateButton.disabled = true;}
}