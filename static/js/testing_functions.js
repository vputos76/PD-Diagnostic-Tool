// This file controls the functionality of all of the buttons that begin test sequences
    // Connects with Flask main.py file to run tests in backend and process data


// Reset isTestRunning if it already exists, otherwise create it
if (typeof window.isTestRunning !== "undefined") {
    window.isTestRunning = { handmotion: false, speech: false, tremor: false };
} else {
    window.isTestRunning = { handmotion: false, speech: false, tremor: false };
}

// Function to safely get or recreate an element
function getElement(id) {
    let elem = document.getElementById(id);
    if (!elem) {
        console.warn(`Element with ID "${id}" not found.`);
    }
    return elem;
}

// Buttons
window.surveyButton = getElement("start-survey-button");
window.handmotionButton = getElement("start-handmotion-button");
window.speechButton = getElement("start-speech-button");
window.tremorButton = getElement("start-tremor-button");

// Modals
window.restartTestModal = getElement("confirm-restart-test");
window.speechTestModal = getElement("speech-test");

// Restart modal buttons
window.yesRestart = getElement("confirm-restart-panel-yes");
window.noRestart = getElement("confirm-restart-panel-no");
window.closeRestart = getElement("close-restart-modal");

// Speech test UI elements
window.speechStartSymbol = getElement("start-test-symbol");

// Function to assign event listeners safely
function assignEventListener(element, event, callback) {
    if (element && !element.dataset.listenerAdded) {
        element.addEventListener(event, callback);
        element.dataset.listenerAdded = "true"; // Mark that an event listener was added
    }
}

// Assign event listeners once
assignEventListener(window.surveyButton, "click", () => buttonClicked("survey", window.surveyButton));
assignEventListener(window.handmotionButton, "click", () => buttonClicked("handmotion", window.handmotionButton));
assignEventListener(window.speechButton, "click", () => buttonClicked("speech", window.speechButton));
assignEventListener(window.tremorButton, "click", () => buttonClicked("tremor", window.tremorButton));

// Check to see if the button needs to be enabled every second using polling
// let polling = setInterval(checkEnableSubmitButton, 1000)

// Assign event listener to process results when "Analyze Test Results" button is clicked
document.getElementById("run-algorithm-button").addEventListener("click", processResults)


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
    
        // Run survey test
        if (bodyVar === "test_type=survey"){
            openSurveyModal()
            document.getElementById("survey-form").addEventListener("submit", function(event) {
                event.preventDefault(); // Prevent default form submission
            
            // Send data to Python for conversion to CSV
            let surveyData  = new FormData(this)   // Collect form data
            surveyData.append("test_type", button);
            fetch("/start_test", {
                method: "POST",
                body: surveyData,
            })
            .then(response => response.json())

            // Close the modal after the form has been submitted
            document.getElementById("survey-test").style.display = "none"
            // If the submit survey button has been clicked, change the complete label to green
            changeCompleteState(window.surveyButton, statusVar)
            }, { once: true })
        }
        
        // Run tremor test
        if (bodyVar === "test_type=handmotion"){
            fetch("/start_test", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded", 
                },
                body: formData.toString()
            })
            // After a few seconds (presumably the patient will have started writing by this point, change the "Complete" label colour to green)
            setTimeout(function(){
                changeCompleteState(window.handmotionButton, statusVar)
            },5000)
        }

        // Run speech test
        if (bodyVar === "test_type=speech"){
            fetch("/start_test", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded", 
                },
                body: formData.toString()
            })
            openSpeechModal(statusVar)  // Pass statusVar in to change complete label in function after enough time has passed
        }

        // Run tremor test
        if (bodyVar === "test_type=tremor"){
            fetch("/start_test", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded", 
                },
                body: formData.toString()
            })
            // After 15 seconds (presumably the patient will have started testing by this point, change the "Complete" label colour to green)
            setTimeout(function(){
                changeCompleteState(window.tremorButton, statusVar)
            },15000)
        }
        isTestRunning[button] = false;
    }
}

// Change incomplete staus mark to complete
function changeCompleteState(buttonName, statusVar){
    // Note that the button has been clicked (at this point the data will have been saved, but if the test is exited prematurely no data will be saved, so the confirm restart modal will open unnecessarily)
    buttonName.setAttribute("clicked", "true");
    // Change label
    statusLabel = document.getElementById(statusVar)
    statusLabel.innerHTML = "Complete"
    statusLabel.style.color = "green"
}

// Check to see if the submit button can be enabled or not
async function checkEnableSubmitButton(){
    let response = await fetch("/session_variables");        // Wait for fetch to finish loading
    let sessions = await response.json();
    if (sessions.all_complete){
        document.getElementById("run-algorithm-button").disabled = false
        clearInterval(polling) // Clear the polling interval to stop the program from checking every second
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

function yesHandler(button, bodyVar, statusVar) {
    restartTestModal.style.display = "none";
       // If the test is not running, start the test
       if (!isTestRunning[button]) {
        isTestRunning[button] = true;
        beginTest(button, bodyVar, statusVar);
  
    }
}

// Show the modal that has instructions for the speech test
function openSpeechModal(statusVar) {
    speechTestModal.style.display = "flex"
    // Cause a 4 second delay before the background noise test begins--allows program to load recording function and take ambient noise reading
    setTimeout(function(){speechStartSymbol.innerHTML = "Do Not Speak&nbsp;&nbsp;&nbsp;3"},1000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Do Not Speak&nbsp;&nbsp;&nbsp;2"},2000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Do Not Speak&nbsp;&nbsp;&nbsp;1"},3000)
    // Tell the patient to speak
    setTimeout(function(){
        speechStartSymbol.style.color = "#27969e";
        speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;10";
    },4000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;9"},5000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;8"},6000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;7"},7000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;6"},8000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;5"},9000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;4"},10000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;3"},11000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;2"},12000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Speak&nbsp;&nbsp;&nbsp;1"},13000)
    // The user should not speak for the final 2 seconds of the test
    setTimeout(function(){
        speechStartSymbol.style.color = "#780000";
        speechStartSymbol.innerHTML = "Do Not Speak&nbsp;&nbsp;&nbsp;2";
    },14000)
    setTimeout(function(){speechStartSymbol.innerHTML = "Do Not Speak&nbsp;&nbsp;&nbsp;1"},15000)
    
    // Let the user know that the recording has finished
    setTimeout(function(){
        speechStartSymbol.style.color = "#024308";
        speechStartSymbol.innerHTML = "Recording Finished"
    },16000)
    // 2 seconds after the recording is finished close the window
    setTimeout(function(){
        speechTestModal.style.display = "none"
        changeCompleteState(window.speechButton, statusVar)
    },18000)
    // Change instruction back to "Don't Speak" in case the test is run again
    speechStartSymbol.style.color = "#780000";
    speechStartSymbol.innerHTML = "Do Not Speak&nbsp;&nbsp;&nbsp;4"


}

// Add survey questions (radiobuttons) to the modal
function openSurveyModal(){
    // Define the modal which becomes visible when the button is clicked
    let surveyModal = document.getElementById("survey-test")
    // Assign event listener to "X" button that closes modal
    document.getElementById("close-survey-modal").addEventListener("click", function(){surveyModal.style.display = "none"})

    // Define survey hmtl form and submit button
    const form = document.getElementById("survey-form")
    form.innerHTML = "" // Erase all content to prevent duplicating questions when reopening the modal

    // Define answer types (agree, don't agree, etc.)
    const answers = ["Never", "Rarely", "Occasionally", "Sometimes", "Frequently", "Always"];

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
        "URINARY INCONTINENCE - The loss of bladder control, resulting in leakage of urine.",];
    
    // Short number of questions for prototyping
    // const questions = ["TREMOR - Involuntary movement at rest.", "RIGIDITY - Tightness or stiffness of the limbs or torso.",]
    
    // Make the modal visible
    surveyModal.style.display = "flex"
    
    // For each of the questions (from "questions"), create a div that holds all answer options (from "answers")
    questions.forEach((question, index) => {
        // Create a div that will hold the questions
        let questionContainer = document.createElement("div");
        questionContainer.innerHTML = `<p>${index + 1}. ${question}</p>`;
        
        // For each of the questions, create 6 radiobuttons for each option in "answers"
        answers.forEach(choice => {
            // Set input radiobutton parameters
            let radio = document.createElement("input")
            radio.type = "radio";
            radio.name = `question${index + 1}`; // i.e. "name=question1"
            radio.value = choice;
            radio.required = true;

            // Create label to go alongside that radiobutton
            let label = document.createElement("label");
            label.appendChild(radio);
            label.appendChild(document.createTextNode(" " + choice));

            // Append each label to the div container that holds all options
            questionContainer.appendChild(label);
            questionContainer.appendChild(document.createElement("br"))
        })
        // Add newly formed divs to survey container
        form.appendChild(questionContainer)
        questionContainer.appendChild(document.createElement("br"))
    })
    // Add in button to submit the form after all questions have been placed
    let submitSurvey = document.createElement("input")
    submitSurvey.type = "submit"
    submitSurvey.id = "submit-form-button"
    submitSurvey.value = "Finish Survey"
    submitSurvey.disabled = true
    
    let breakLine = document.createElement("br")
    breakLine.id = "survey-break"

    form.appendChild(breakLine)
    form.appendChild(breakLine)
    form.appendChild(submitSurvey)

    // Event listener for each radiobutton to check if all buttons are clicked, which enables the submit survey button
    document.querySelectorAll("#survey-form input[type='radio']").forEach((radio) => {
        radio.addEventListener("change", function(){
            // Define array of questions
            const radioQuestions = document.querySelectorAll("#survey-form div");
            let allSelected = Array.from(radioQuestions).every(fieldset => 
                fieldset.querySelector("input[type='radio']:checked")
            )       
            submitSurvey.disabled = !allSelected    // Enable if all are answered
        });
    });
}

// Triggers the machine learning algorithm to start, loads up the process_data.js script
function processResults() {
    // Automatically switch to the review_data page
    fetch(`/content_pages/review.html`)
    .then(response => response.text())
    .then(html => {
        document.getElementById("base-content-div").innerHTML = html;
        // Load the script associated with each content page
        const script = document.createElement("script");
        script.src = "../static/js/process_data.js";
        document.body.appendChild(script);
    })
}