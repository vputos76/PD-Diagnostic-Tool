// This file controls the functionality of all of the buttons that begin test sequences
    // Connects with Flask main.py file to run tests in backend and process data


// Track if the test is currently running for each button
let isTestRunning = {
    handmotion: false,
    speech: false,
    tremor: false
};

// Assign variables to all buttons
const surveyButton = document.getElementById("start-survey-button");
const handmotionButton = document.getElementById("start-handmotion-button");
const speechButton = document.getElementById("start-speech-button");
const tremorButton = document.getElementById("start-tremor-button");

// Assign variable name to the "confirm-restart-test" modal
let restartTestModal = document.getElementById("confirm-restart-test");
// Assign variable names to "confirm-restart-test" modal yes button, no button, "X" close button
let yesRestart = document.getElementById("confirm-restart-panel-yes");
let noRestart = document.getElementById("confirm-restart-panel-no");
let closeRestart = document.getElementById("close-restart-modal");

surveyButton.addEventListener("click", () => buttonClicked("survey", surveyButton))
handmotionButton.addEventListener("click", () => buttonClicked("handmotion", handmotionButton))
speechButton.addEventListener("click", () => buttonClicked("speech", speechButton))
tremorButton.addEventListener("click", () => buttonClicked("tremor", tremorButton))


// Connect to main.py file and begin test based on what button was clicked
function buttonClicked(button, buttonName) {
    // Assign fetch body type based on what button was clicked
    let bodyVar = ""
    let statusVar = ""  // For staus label that will change colour green and say "complete"
    
    switch(button) {
        case "survey":
            bodyVar = "test_type=survey";
            statusVar = "survey-status"
            break;
        case "handmotion":
            bodyVar = "test_type=handmotion";
            statusVar = "handmotion-status"
            break;
        case "speech":
            bodyVar = "test_type=speech";
            statusVar = "speech-status"
            break;
        case "tremor":
            bodyVar = "test_type=tremor";
            statusVar = "tremor-status"
            break;
    }

    // If the button has not been clicked before, rewrite the "clicked" attribute to reflect that it has been, then run the test
    if (buttonName.getAttribute("clicked") === "false") {
        buttonName.setAttribute("clicked", "true");
        beginTest(button, bodyVar, statusVar)
    }

    // If the button has been clicked before, ask the user if they want to erase previous test data and re-record it
    else {
        restartTestModal.style.display = "block";  // Make the modal visible
        // Create a Promise that resolves when one of the buttons is clicked
        new Promise((resolve) => {
            yesRestart.addEventListener("click", function yesClickHandler() {
                yesHandler(button, bodyVar, statusVar);  // Execute the yes handler
                resolve();  // Resolve to continue the program
            }, { once: true });
    
            noRestart.addEventListener("click", function noClickHandler() {
                noHandler();  // Execute the no handler
                resolve();  // Resolve to continue the program
            }, { once: true });
    
            closeRestart.addEventListener("click", function closeClickHandler() {
                noHandler();  // Execute the no handler (or close handler, if needed)
                resolve();  // Resolve to continue the program
            }, { once: true });
        }).then(() => {
            // The rest of the program will continue after the user clicks a button
        });
    }
}

// Actually send the data to the Python script to begin the test
function beginTest(button, bodyVar, statusVar) {
    if (bodyVar) {
        let formData = new URLSearchParams();
        formData.append("test_type", button);
    
        fetch("/start_test", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded", 
            },
            body: formData.toString()
        })
        isTestRunning[button] = false;

    }

    // Change incomplete staus mark to complete
    statusLabel = document.getElementById(statusVar)
    statusLabel.innerHTML = "Complete"
    statusLabel.style.color = "green"
}

function yesHandler(button, bodyVar, statusVar) {
    restartTestModal.style.display = "none";
       // If the test is not running, start the test
       if (!isTestRunning[button]) {
        isTestRunning[button] = true;
        beginTest(button, bodyVar, statusVar);
  
    }
}

function noHandler() {
    restartTestModal.style.display = "none";
    // Clone the element to reset it and remove existing event listeners
    const newYesRestart = yesRestart.cloneNode(true);
    // Replace the old element with the new one
    yesRestart.parentNode.replaceChild(newYesRestart, yesRestart);
    // Reassign the variable to the new element
    yesRestart = newYesRestart;
}

