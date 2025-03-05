// Access CSS constant colours
const rootStyles = getComputedStyle(document.documentElement);
// Access a specific color variable using getPropertyValue
const h1_error = rootStyles.getPropertyValue('--close-patient').trim();
const bg = rootStyles.getPropertyValue('--bg').trim();
const error_bg = rootStyles.getPropertyValue('--error-bg').trim();
const error_accent = rootStyles.getPropertyValue('--close-patient-active').trim();
const button = rootStyles.getPropertyValue('--button').trim();
const button_active = rootStyles.getPropertyValue('--button-active').trim();
const button_accent = rootStyles.getPropertyValue('--button-accent').trim();


// Monitor the "Login" button and enable it when both the username and password inputs have text
const username_input = document.getElementById("username-input");
const password_input = document.getElementById("password-input");
const login_button = document.getElementById("login-button");

// Add event listeners to detect input changes
username_input.addEventListener("input", toggleLogin)
password_input.addEventListener("input", toggleLogin)

// Add "Ctrl + Enter" key binding to try to login
document.addEventListener("keydown", (event) => {
    if(event.key == "Enter" && login_button.disabled == false) {verifyLogin();}
});


// Add event listener for span that toggles password visibility
const togglePassButton = document.getElementById("toggle-visibility-icon")
togglePassButton.addEventListener("click", togglePassVisibility)

// Disable/enable login button based on how many input forms have content
function toggleLogin() {
    if (username_input.value.trim() !== "" && password_input.value.trim() !== "") {
        login_button.disabled = false;}
    else {login_button.disabled = true;}
}

// Collect both the inputted username and password and check against the login_credentials.json file
function verifyLogin() {
    // Get username input
    let username = username_input.value;
    // Get password input
    let password = password_input.value;

    // Fetch the login credentials object and iterate through it to see if there is a match for both the username and password
    fetch("/get_logins")
        .then(response => response.json())  // Convert response to JSON
        .then(data => {
            // Verify that the entered credentials match login credentials from json file
            const isValidLogin = data.some(user => user.Username === username && user.Password === password);

            // If the login credentials match, log the user in and display the home screen
            if (isValidLogin) {
                // Do nothing, since Flask page will redirect
            }
            // Alert user if login credentials fail
            else {
            document.getElementById("login-modal").style.border = "4px solid" + h1_error;           // Change modal border
            document.getElementById("login-modal").style.backgroundColor = error_bg;                // Change modal background colour
            document.getElementById("instruction").innerHTML = "Login failed. Please Try again.";   // Change message
            document.getElementById("instruction").style.color = h1_error;                          // Change message colour
            document.getElementById("login-button").style.background = h1_error;                    // Change login button background
            document.getElementById("login-button").style.border = "2px solid" + error_accent;      // Change login button border          

        }
    })
}

// Toggle the visibility of the password when the span is clicked
function togglePassVisibility() {
    var passToggle = document.getElementById("password-input");
    // If the type is password (text is hidden), switch it so that characters appear
    if (passToggle.type === "password") {
        passToggle.type = "text";
        togglePassButton.innerHTML = "visibility_off"
    }
    // If the type is not password (text is visible), switch it so that characters are hidden
    else {
        passToggle.type = "password";
        togglePassButton.innerHTML = "visibility"
    }
}