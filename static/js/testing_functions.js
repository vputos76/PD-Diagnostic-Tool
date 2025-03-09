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

// Assign variables for speech test instructional modal
const speechTestModal = document.getElementById("speech-test")
const speechStartSymbol = document.getElementById("start-test-symbol")



surveyButton.addEventListener("click", () => buttonClicked("survey", surveyButton))                 // Open up survey
handmotionButton.addEventListener("click", () => buttonClicked("handmotion", handmotionButton))     // Open up handmotion test
speechButton.addEventListener("click", () => buttonClicked("speech", speechButton))                 // Open up speech test
tremorButton.addEventListener("click", () => buttonClicked("tremor", tremorButton))                 // Open up tremor test

// speechButton.addEventListener("click", () => speechModal())                                         // Show modal for speech test instructions

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
        // Run speech test
        if (bodyVar === "test_type=speech"){
            speechModal()
        }

        // Run survey test
        if (bodyVar === "type_test=survey"){
            surveyModal()
        }

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

// Show the modal that has instructions for the speech test
function speechModal() {
    speechTestModal.style.display = "flex"
    // Cause a 6 second delay before the background noise test begins--allows program to load recording function and take ambient noise reading
    setTimeout(function(){
        speechStartSymbol.innerHTML = "Speak"
        speechStartSymbol.style.color = "#27969e"
    },6000)
    // Let the user know that the recording has finished
    setTimeout(function(){
        speechStartSymbol.innerHTML = "Recording Finished"
        speechStartSymbol.style.color = "#780000"
    },10000)
    // 2 seconds after the recording is finished close the window
    setTimeout(function(){
        speechTestModal.style.display = "none"
    },12000)
    // Change instruction back to "Don't Speak" in case the test is run again
    speechStartSymbol.innerHTML = "Don't Speak"

}

// Add survey questions (radiobuttons) to the modal
function surveyModal(){
    // Define where the ssurvey questions will be placed
    const targetDiv = document.getElementById("survey-test-content")
    // Define answer types (agree, don't agree, etc.)
    const answers = ["0-Never", "1-Rarely", "2-Occasionally", "3-Sometimes", "4-Frequently", "5-Always"];
    // Define questions to be asked
    const questions = ["TREMOR - Involuntary movement at rest.",
        "RIGIDITY - Tightness or stiffness of the limbs or torso.",
        "BALANCE / WALKING DIFFICULTIES - Taking small or slow steps; a shuffling gait; decrease in the natural swing of the arms.",
        "MOTOR FLUCTUATIONS / DYSKINESIA - Motor Fluctuations are 'on' and 'off' periods of controlled motor symptoms; Dyskinesia is sudden, uncontrollable movements.",
        "DIZZINESS UPON STANDING - The sensation of light-headednesss, which often leads to a loss of balance, when moving from sitting to standing or lying down to standing.",
        "FALLS - Balance impairment can lead to falls.",
        "FATIGUE / SLEEP DISTURBANCES - Difficulty falling asleep or staying asleep; vivid dreams; daytime sleepiness.",
        "ANXIETY / DEPRESSION / MEMORY - Feeling nervous or irritable; feeling sad, empty and hopeless; loss of pleasure in things you once enjoyed; problems with thinking, word finding, and judgment.",
        "SWALLOWING - Difficulty swallowing; drooling; excessive saliva in the mouth.",
        "GASTROINTESTINAL ISSUES / CONSTIPATION - Nausea; vomiting; diarrhea; infrequent bowel movements.",
        "SEXUAL CONCERNS - Changes in sexual desire or erectile dysfunction.",
        "HALLUCINATIONS - Seeing, hearing or sensing things that are not there.",
        "DELUSIONS - Believing things that are not true, e.g. Everyone is ststaring at me when I walk outside.",
        "URINARY FREQUENCY - The need to urinate often.",
        "URINARY URGENCY - The feeling that one must urinate right away, even if the bladder is not full.",
        "URINARY INCONTINENCE .",];



}