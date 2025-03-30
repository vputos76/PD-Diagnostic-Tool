// This script collects all of the recorded data (taken using testing_fnuctions.js)
    //  Either feeds it into the machine learning algorithm (handmotion, speech, tremor) or display radar chart of results (survey)

getSessionDates()
const combobox = document.getElementById("test-date-combobox")

// For each of the elements in the patient's info.JSON file (session dates), add an option with "visit# - date" to the select combobox
async function getSessionDates(){
    let response = await fetch("/view_test_dates")
    let data = await response.json()
    
    // Identify the combobox by element ID
    combobox.addEventListener("change", chooseDate)     // Update displayed info when an option is selected
    combobox.innerHTML = ""                             // Erase all combobox information so that it is not duplicated when the window reloads

    // Write new options to it for each of the dates--values are the session number
    for (let key in data){
        let date = document.createElement("option")
        date.innerHTML = key + " - " + data[key]        // Text that is displayed
        date.value = key                                // Value associated with each option
        combobox.appendChild(date)
    }
    combobox.value = ""                                 // Start as a blank option so data can be selected
}

// Set up figures and results for chosen date
async function chooseDate(){
    // Fetch all of the file data associated with the chosen date/session
    let sessionNum = combobox.value;
    let response = await fetch(`/session_data/${sessionNum}`);
    let data = await response.json();
    // Separate different data results
    let radarData = data.radarData;
    let fullSurvey = data.fullData;
    let predictions = data.predictions;

    plotRadarChart(radarData, fullSurvey)
    displayPredictions(predictions)
}


// Plotting radar chart from survey results ("radarData" is averaged survey results, "fullSurvey" is full results)
async function plotRadarChart(radardata, fullsurvey){
    // Convert radardata and fullsurvey from array of objects to object
    let radarData = Object.fromEntries(
        radardata.map(item => [item.Question, item.Response])
    );
    console.log(radarData)
    
    let fullSurvey = Object.fromEntries(
        fullsurvey.map(item => [item.Question, item.Response])
    );
    console.log(fullSurvey)
    
    // Get canvas where chart will be placed
    let chartCanvas = document.getElementById("radar-canvas").getContext("2d");
    
    // Create data object that builds radar chart
    const data = {
        labels: Object.keys(radarData),     // Categories for radar chart are the object keys
        datasets: [{
            label: `Session ${combobox.value}`,
            data: Object.values(radarData), // Categories for radar chart are the object values
            backgroundColor: "rgba(39, 150, 158, 0.5)", // Semi-transparent fill
            borderColor: "rgba(1, 61, 63, 1)", // Outline color
            borderWidth: 2,
            pointBackgroundColor: "rgba(1, 61, 63, 1)"

        }]
    };
    
    // Destroy any existing radar charts
    if (window.radarChart){
        window.radarChart.destroy();
    }
    
    // Remove the full survey resutls if they exists
    let existingResultsDiv = document.getElementById("full-survey-div");
    if (existingResultsDiv) {
        existingResultsDiv.remove();  // Removes the element from the DOM
    }

    // Create radar chart
    window.radarChart = new Chart(chartCanvas, {
        type: "radar",
        data: data,
        options: {
            responsiveness: true,
            maintainAspectRatio: false, // Allow dynamic resizing
            scales: {
                r: { // 'r' is for radial scale
                    beginAtZero: true,
                    suggestedMin: 0,
                    suggestedMax: 5,
                    ticks:{
                        z:1,        // Place above grid lines
                        stepSize: 1, // Ensure scale increments in whole numbers
                        font: {
                            size: 14, // Increase font size of scale numbers
                            weight: "bold" // Make scale numbers bold
                        },
                        color: "#27969e", // Scale number color (black)
                    },
                    pointLabels: {
                        font: {
                            size: 14, // Increase font size for labels
                            weight: "bold" // Make category labels bold
                        },
                        color: "#013d3f" // Category label color
    }}}}})

    // Place full survey results next to radar chart for better data comprehension
    let resultsDiv = document.createElement("div")
    resultsDiv.id = "full-survey-div"
    
    // Place title in div
    let title = document.createElement("h2")
    title.innerHTML = "Full Survey Results"
    title.id = "full-survey-label"
    resultsDiv.appendChild(title)
    
    // For each of the full survey answers, show the response
    let fullSurveyList = document.createElement("ol")
    fullSurveyList.id = "survey-list"
    
    // Map of numerical answers to survey responses (i.e. 0=Never)
    const answers = ["Never", "Rarely", "Occasionally", "Sometimes", "Frequently", "Always"];

    // For each key, map the value to answers, and display that with the key in a list item
    Object.entries(fullSurvey).forEach(([topic, value]) => {
        let listItem = document.createElement("li");
        listItem.innerHTML = `<b>${topic}:</b> ${answers[value]}`;
        fullSurveyList.appendChild(listItem);
    });
    // Append list to radar chart div
    resultsDiv.appendChild(fullSurveyList)

    // Add survey items div items to the full chart div
    document.getElementById("radar-chart-div").appendChild(resultsDiv)
}

// Display the predictions of the ML model in a table
function displayPredictions(predictions){
    console.log(predictions)

    // Collect the table and make it visible
    let results = document.getElementById("predictions-table")
    results.style.display = ""

    // Fill in each of the cell blocks using the predicitions object
    document.getElementById("hm-pred").innerHTML = predictions["pred_HM"]
    document.getElementById("hm-rate").innerHTML = predictions["conf_HM"]
    document.getElementById("speech-pred").innerHTML = predictions["pred_v"]
    document.getElementById("speech-rate").innerHTML = predictions["conf_v"]
    document.getElementById("rt-pred").innerHTML = predictions["pred_RT"]
    document.getElementById("rt-rate").innerHTML = predictions["conf_RT"]
    document.getElementById("weighted-rate-row").innerHTML = predictions["weighted_vote"]
    document.getElementById("prediction-row").innerHTML = predictions["final_class"]
}