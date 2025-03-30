// Make header shrink, but still remain visible, when scrolling up
window.onscroll = function() {scrollHide()};

// Array of objects to hide when scrolling
let objectsToHide = [document.getElementById("testing-button"),
    document.getElementById("review-data-button"),// document.getElementById("progression-button"),
    document.getElementById("new-patient-button"),document.getElementById("open-patient-button"),
    document.getElementById("close-patient-button"), document.getElementById("header-id"),
    document.getElementById("header-dob"), document.getElementById("header-age"),
    document.getElementById("header-sex"), document.getElementById("header-doc"), document.getElementById("user-login"),
    document.getElementById("company-logo")
]

let photo = document.getElementById("profile-photo")
let header = document.getElementById("base-header-div")
let patientInfoPanel = document.getElementById("patient-info-panel")
let controlButtonsPanel = document.getElementById("control-buttons-panel")
const scrollParam = 50

function scrollHide() {
    // Modify display styles to make header tab smaller
    if (document.body.scrollTop > scrollParam || document.documentElement.scrollTop > scrollParam) {
        objectsToHide.forEach(item => item.style.display = "none")
        photo.style.width = "8vh";
        photo.style.height = "8vh";
        header.style.paddingBottom = "37vh"
        patientInfoPanel.style.padding = "0.5vh"
        controlButtonsPanel.style.padding = "0"

    } else {
        // Revert back to original display styles
        objectsToHide.forEach(item => item.style.display = "flex")
        photo.style.width = "20vh";
        photo.style.height = "20vh";
        header.style.paddingBottom = "44vh"
        patientInfoPanel.style.padding = "3vh"
        controlButtonsPanel.style.padding = "2vh"
    }
} 



