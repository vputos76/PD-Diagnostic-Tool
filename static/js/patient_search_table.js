// This script controls the loading of patient names/ids to the patient search table so a user can filter patients and load their file
document.addEventListener("DOMContentLoaded", function () {
    loadPatient("0")      // Load default "no patient" on startup
    fetchPatients();    // Load patients when the page loads
    // Attach input event listener to filter patients live
    document.getElementById("patient-search-bar").addEventListener("input", filterPatients);
    document.getElementById("confirm-close-panel-yes").addEventListener("dblclick", closePatient);
});

function fetchPatients() {
    let visibleIndex = 0; // Keeps track of visible row index for striping
    fetch("/get_patients", {
        headers: {'X-Requested-With': 'Flask-App'}
    },)

        .then(response => response.json())
        .then(data => {
            let tableBody = document.getElementById("patient-search-table").getElementsByTagName("tbody")[0];
            tableBody.innerHTML = ""; // Clear existing rows before adding new ones

            data.patient.forEach(patient => {
                let row = document.createElement("tr");
                row.classList.add("clickable-row")      // Add class to make it appear clickable

                // Ensure correct column order: ID -> First Name -> Last Name
                let idCell = document.createElement("td");
                idCell.textContent = patient.ID;
                row.appendChild(idCell);

                let firstNameCell = document.createElement("td");
                firstNameCell.textContent = patient["First Name"];
                row.appendChild(firstNameCell);

                let lastNameCell = document.createElement("td");
                lastNameCell.textContent = patient["Last Name"];
                row.appendChild(lastNameCell);

                tableBody.appendChild(row);
                
                // Make row double clickable to refresh the page for that patient
                row.ondblclick = function() {
                    loadPatient(patient.ID)          // Rewrite the header info for the newly opened patient
                }

                // Apply striping
                if (visibleIndex % 2 === 0) {
                    row.classList.add("even-row");
                } else {
                    row.classList.add("odd-row");
                }
                visibleIndex++; // Increment only for visible rows
            });

            console.log("Patients loaded:", data.patient.length);
        })
        .catch(error => console.error("Error fetching patients:", error));
}

function filterPatients() {
    let input = document.getElementById("patient-search-bar");
    let filter = input.value.toLowerCase().trim();
    console.log("Filtering for:", filter);

    let table = document.getElementById("patient-search-table");
    let tableBody = table.getElementsByTagName("tbody")[0];
    let rows = Array.from(tableBody.getElementsByTagName("tr"));

    if (rows.length === 0) {
        console.warn("No rows found in patient table.");
        return;
    }

    let visibleIndex = 0; // Keeps track of visible row index for striping

    rows.forEach(row => {
        let cells = row.getElementsByTagName("td");
        if (cells.length < 3) return; // Ensure row has required columns

        let patientID = cells[0].textContent.toLowerCase();
        let firstName = cells[1].textContent.toLowerCase();
        let lastName = cells[2].textContent.toLowerCase();

        // Show row if it matches, otherwise hide it
        if (filter === "" || patientID.includes(filter) || firstName.includes(filter) || lastName.includes(filter)) {
            row.style.display = ""; // Show matching rows
            row.classList.remove("even-row", "odd-row"); // Clear existing classes

            // Apply striping
            if (visibleIndex % 2 === 0) {
                row.classList.add("even-row");
            } else {
                row.classList.add("odd-row");
            }
            visibleIndex++; // Increment only for visible rows
        } else {
            row.style.display = "none"; // Hide non-matching rows
        }
    });
}

function closePatient() {
    location.reload() // Reloading the page resets all content (start from scratch)
    // document.getElementById("confirm-close-modal").style.display = "none"
    // loadPatient("0")
}


function loadPatient(patient_ID) {
    fetch(`/get_patients/${patient_ID}`, {
        headers: {'X-Requested-With': 'Flask-App'}
    },)
        .then(response => response.json())
        .then(patient => updatePatientInfo(patient))
        .then(state => buttonPanelState(patient_ID))
}

// Change patient info presented in header
function updatePatientInfo(patient) {
    document.getElementById("header-name").textContent = patient.Info.FirstName + " " + patient.Info.LastName || "No Patient Selected";
    document.getElementById("header-id").textContent = "Patient ID: " + patient.Info.ID || "N/A";
    document.getElementById("header-dob").textContent = "Date of Birth: " + patient.Info.Birthday || "N/A";
    document.getElementById("header-age").textContent = "Age: " + patient.Age || "N/A";
    document.getElementById("header-sex").textContent = "Sex: " + patient.Info.Sex || "N/A";
    document.getElementById("header-doc").textContent = "Attending Physician: " + patient.Info.Doctor || "N/A";
    document.getElementById("profile-photo").src = `../static/patient_data/${patient.Photo}`;
    // Close patient search modal
    document.getElementById("open-patient-modal").style.display = "none";
    ;
}

// Enable buttons is a patient is selected, or disable when the patient is de-selected
function buttonPanelState(patient_ID) {
    let buttonsToChange = document.getElementsByClassName("control-buttons")
    // If the "No Patient" patient is selected, disable all of the buttons
    if (patient_ID === "0") {
        Array.from(buttonsToChange).forEach(button => button.disabled = true)
    }
    // When the patient is not the "No Patient" condition, enable all of the buttons
    else {
        Array.from(buttonsToChange).forEach(button => button.disabled = false)
    }
}