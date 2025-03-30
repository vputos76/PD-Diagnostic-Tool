# To render website and load HTML templates
from csv import writer                          # Write survey data to .csv format
from datetime import datetime                   # Work out patient age from birthday
from flask import Flask, render_template, jsonify, redirect, request, url_for, session, send_from_directory
from json import load, dumps, dump              # To read JSON-stored patient data
from pandas import read_csv                     # Used to read survey data to create radar charts in JS
from pprint import pprint                       # Display prediction results in a readable format
from psutil import process_iter                 # Used to get hold of running application windows
from pygetwindow import getWindowsWithTitle     # Used to open and close PressureTest.exe window to ensure functionality
from random import randint                      # Used to generate random patient ID
from shutil import copy, move                   # Used to copy profile photos from images to patient directory
from time import sleep                          # Sleep when switching between incorrect/correct login page
import os                                       # Determine which user is using the program
from utils.sound_recording import record_audio  # Used to record microphone samples
from prediction import run_prediction           # Run prediction on handmotion and voice samples

app = Flask(__name__)
app.secret_key = "capstone_25"


######################################################################################################
###------------------------------------------Flask Routes------------------------------------------###
######################################################################################################

# Catch route for when Flask looks for the .ico file
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images', 'test_logo.ico', mimetype='image/vnd.microsoft.icon')

# Redirect the first page to a login screen
@app.route("/")
def redirect_to_login():
    return redirect("/login")

# Login screen
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username-input")  # Capture username
        password = request.form.get("password-input")  # Capture password
        # Load in login data to compare against captured username and password
        with open("static/login_credentials/login.json") as file:
            logins = load(file)
        # Check if posted username and password are within the login database
        for users in logins:
            if username == users["Username"] and password == users["Password"]:
                session["user"] = users["User"]  # Store in Flask session
                return redirect(url_for("homescreen"))  # Redirect only if correct
        # Delay for 1.75s for JS changes to appear, then refresh
        sleep(1.75)
    return render_template("lock_screen.html")
    
# Return JSON object of all logins
@app.route('/get_logins')
def search_logins():
    with open("static/login_credentials/login.json") as file:
        login_data = load(file)
        return jsonify(login_data)
    
# Return JSON object of all patients
@app.route('/get_patients')
def search_patients():
    with open("static/patient_data/patient_database.json") as file:
        master_json_data = load(file)
        return jsonify(master_json_data) 

# Return JSON object of single patient from master patient list
@app.route('/get_patients/<patient_id>')
def get_patient(patient_id):
    # If the patient ID == 0, it is the "no patient" default case
    if patient_id == "0":
        file_name = "static/patient_data/no_patient/no_patient.json"
    else:
        with open("static/patient_data/patient_database.json") as file:
            master_json_data = load(file)

        # Find the sought patient through their ID
        target_patient = next((p for p in master_json_data["patient"] if p["ID"] == patient_id), None)
        if not target_patient:
            file_name = "static/patient_data/no_patient/no_patient.json"
        else:
            file_name = f"static/patient_data/{patient_id}/{patient_id}.json"
    
    # Now that *a patient (real or 'no patient')* has been selected, process the .json info
    with open(file_name) as file: patient_header_info = load(file)
    # Determine patient profile photo file location based on directory name
    patient_photo_file = f"{os.path.basename(file_name)[:-5]}/{os.path.basename(file_name)[:-5]}.png"

    # Subtract the birth year from the current year, and subtract 1 if the person's birth month and day has not passed yet (i.e. inequality True == 1)
    try: age = datetime.today().year - int(patient_header_info["Birthday"][0:4]) - ((int(patient_header_info["Birthday"][5:7]), int(patient_header_info["Birthday"][8:10])) > (datetime.today().month, datetime.today().day))
    # Catch exception for when "No Patient" birthday causes ValueError
    except ValueError: age = "N/A"
    
    # Combine all data into single patient data dictionary to minimize render_template inputs
    patient_data = {"User" : session["user"],
                    "Info" : patient_header_info,
                    "Age" : age,
                    "Photo" : patient_photo_file,}
    
    # Store all processed new patient information to session variable
    session["fname"] = patient_header_info["FirstName"]
    session["lname"] = patient_header_info["LastName"]
    session["id"] = patient_header_info["ID"]
    session["dob"] = patient_header_info["Birthday"]
    session["doctor"] = patient_header_info["Doctor"]
    session["sex"] = patient_header_info["Sex"]
    session["age"] = age
    session["photo"] = patient_photo_file
    session["handmotion_completed"] = "Incomplete"     # Reset which tests are completed
    session["speech_completed"] = "Incomplete"
    session["tremor_completed"] = "Incomplete"
    session["survey_completed"] = "Incomplete"
    session["all_complete"] = False

    # Delete session data when switching patient so it does not cause file storage/finding issues
    if "session_num" in session:
        del session["session_num"]
    if "session_workspace" in session:
        del session["session_workspace"]
    return jsonify(patient_data)
   
@app.route('/home')
def homescreen():
    # Get username from Flask session, default to "Guest"
    return render_template("base.html", user=session["user"], session=session)

# Return JSON object of single patient from master patient list
@app.route("/create_new_patient", methods=["POST"])
def create_patient():
    # Create a 7 digit patient ID number
    id = "".join([str(randint(0,9)) for _ in range(7)])
    # If the ID has already been used, remake it, and check until there is an ID that is not in use
    while os.path.isdir("./static/patient_data/" + id):
        id = "".join([str(randint(0,9)) for _ in range(7)])    
    # Create patient folder and JSON file within that folder
    os.mkdir("./static/patient_data/" + id)
    # Create sessions folder within that patient's folder
    os.mkdir(f"./static/patient_data/{id}/{id}_sessions")
    # Create an empty JSON file that shows when this session was created
    with open(f"./static/patient_data/{id}/{id}_sessions/info.JSON", "w") as file:
        dump({}, file, indent=4)
        
    # Create dict to become JSON file
    new_patient = {
        "FirstName" : request.form.get("fname"),
        "LastName" : request.form.get("lname"),
        "ID" : id,
        "Birthday" : request.form.get("dob"),
        "Doctor" : request.form.get("attending"),
        "Sex" : request.form.get("sex"),
    }
    # Profile photo location
    photoUpload = f"./static/images/{request.form.get('photo-upload')}"

    # Define file locations to use in jumping JSON data
    fileLocation = "static/patient_data/" + id + "/" + id + ".json"
    masterLocation = "./static/patient_data/patient_database.json"

    # Create dict to be appended to master patient list
    new_master_entry = {
        "ID" : id,
        "First Name" : new_patient["FirstName"],
        "Last Name" : new_patient["LastName"],
        "File Location" : fileLocation
    }

    # Write to patient file JSON, transfer png profile photo (renaming it) to directory
    with open(fileLocation, "w") as file:
        file.write(dumps(new_patient, indent=4))
    copy(photoUpload, os.path.join("static/patient_data/" + id, id + ".png"))

    # Upload the patient's info into the master patient list
    with open(masterLocation, "r+") as file:
        master_list = load(file)
        master_list["patient"].append(new_master_entry)
        file.seek(0)    # Move cursor to beginning
        file.write(dumps(master_list, indent=4))
        file.truncate()

    return redirect(url_for("homescreen"))

# Render .html pages based when a button is clicked in the header panel
@app.route("/<path:page>")
def load_page(page):
    session["session_num"] = 1
    session["session_workspace"] = "./static/patient_data/9098978/9098978_sessions/session_1"
    session["all_complete"] = True
    session["handmotion_completed"] = "Complete"
    session["speech_completed"] = "Complete"
    session["survey_completed"] = "Complete"
    session["tremor_completed"] = "Complete"
    return render_template(page)

# Based on the "run test" button clicked, trigger one of the hardware data collection methods to open
@app.route("/start_test", methods=["POST"])
def run_test():
    # Ensure that a folder has been created for this session number to save data
    if "session_num" not in session:
        check_session_number()
    # Get test type
    test_type = request.form.get("test_type")

    # If the Survey button is clicked
    if test_type == ("survey"):
        # Record survey
        data = request.form.to_dict()  # Convert FormData to a dictionary
        # Define how survey answers correspond to numerical values
        survey_map = {"Never" : 0, "Rarely" : 1, "Occasionally" : 2, "Sometimes" : 3, "Frequently" : 4, "Always" : 5}

        # Create a dictionary that mimics the survey results, but with numerical results
        mapped_data = {key: survey_map.get(value) for key, value in data.items()}
        # Set categories and associated question topics to be used in radar graph in {category: [(question, score), ...], ...} format
        radar_categories = {
            "Sexual Concerns" : [("Sexual Concerns", mapped_data["question1"])],
            "Tremor" : [("Tremor", mapped_data["question2"])],
            "Rigidity" : [("Rigidity", mapped_data["question3"])],
            "Balance/Walking Difficulties" : [("Balance/Walking Difficulties", mapped_data["question4"]), ("Dizziness Upon Standing", mapped_data["question5"]), ("Falls", mapped_data["question6"])],
            "Motor Fluctuations/Dyskinesia" : [("Motor Fluctuations/Dyskinesia", mapped_data["question7"])],
            "Fatigue/Sleep Disturbances" : [("Fatigue/Sleep Disturbances", mapped_data["question8"])],
            "Anxiety/Depression/Memory" : [("Anxiety/Depression/Memory", mapped_data["question9"]), ("Hallucinations", mapped_data["question10"]), ("Delusions", mapped_data["question11"])],
            "Swallowing" : [("Swallowing", mapped_data["question12"])],
            "Gastrointestinal Issues/Constipation" : [("Gastrointestinal Issues/Constipation", mapped_data["question13"]), ("Urinary Frequency", mapped_data["question14"]), ("Urinary Urgency", mapped_data["question15"]), ("Urinary Incontinence", mapped_data["question16"])]
        }

        # Take an average of the questions in each category and place in a dictionary to be used for the radar chart
        averaged = {key:round(sum(qs[1] for qs in value)/len(value)) for key, value in radar_categories.items()}

        # Write mapped data to a csv file and store it in the session folder
        with open(os.path.join(session["session_workspace"], f"{session['session_num']}_survey.csv"), "w", newline="") as file:
            csv_writer = writer(file)  # Use csv.writer instead of DictWriter
            if file.tell() == 0:  # Write header only if file is empty
                csv_writer.writerow(["Question", "Response"])  # Header row
            # Write each key-value pair as a new row
            csv_writer.writerows(averaged.items())  # Writes each (key, value) pair as a row

        # Show all question results to be displayed side by side with averaged categories
        full_results = {
            "Sexual Concerns" : mapped_data["question1"],
            "Tremor" : mapped_data["question2"],
            "Rigidity" : mapped_data["question3"],
            "Balance/Walking Difficulties" : mapped_data["question4"],
            "Dizziness Upon Standing" : mapped_data["question5"],
            "Falls" : mapped_data["question6"],
            "Motor Fluctuations/Dyskinesia" : mapped_data["question7"],
            "Fatigue/Sleep Disturbances" : mapped_data["question8"],
            "Anxiety/Depression/Memory" : mapped_data["question9"],
            "Hallucinations" : mapped_data["question10"],
            "Delusions" : mapped_data["question11"],
            "Swallowing" : mapped_data["question12"],
            "Gastrointestinal Issues/Constipation" : mapped_data["question13"],
            "Urinary Frequency" : mapped_data["question14"],
            "Urinary Urgency" : mapped_data["question15"],
            "Urinary Incontinence" : mapped_data["question16"]
        }
        # Write complete data to a csv file and store it in the session folder
        with open(os.path.join(session["session_workspace"], f"{session['session_num']}_full_survey.csv"), "w", newline="") as file:
            csv_writer = writer(file)  # Use csv.writer instead of DictWriter
            if file.tell() == 0:  # Write header only if file is empty
                csv_writer.writerow(["Question", "Response"])  # Header row
            # Write each key-value pair as a new row
            csv_writer.writerows(full_results.items())  # Writes each (key, value) pair as a row

        session["survey_completed"] = "Complete"


    # If the Hand Motion trial button is clicked
    elif test_type == ("handmotion"):
        os.startfile(r"..\WakumTest\Wakum\Wintab Pressure Test\SampleCode\Debug\PressureTest")
        # NOTE For some reason the program does not open properly and record pen pressure until the window is minimized and opened again. This automatically completes this prociedure
        sleep(0.1)
        for window in getWindowsWithTitle("PressureTest"):
            if "PressureTest" in window.title:
                app_window = window
                break
        if app_window:
            app_window.minimize()  # Minimize the window
            app_window.maximize()  # Minimize the window

        # While the test is running, the program should do nothing (i.e. just let data be recorded)
        while is_test_running("PressureTest.exe"):
            pass
        # Once the window is closed (data is no longer being recorded), save the data in the session file and return to the test selection screen
        move(os.path.join(os.getcwd(), "pressure.csv"), os.path.join(session["session_workspace"], "pressure.csv"))
        session["handmotion_completed"] = "Complete"


    # If the Speech trial button is clicked
    elif test_type == ("speech"):
        # Start the recording, and record the status value as complete
        record_audio(keyword="Microphone (Yeti Stereo Microph")
        session["speech_completed"] = "Complete"
        # Move the data
        move(os.path.join(os.getcwd(), "speech_test.wav"), os.path.join(os.getcwd(), session["session_workspace"], "speech_test.wav"))
    

    # If the Tremor trial button is clicked
    elif test_type == ("tremor"):
        # Start witmotion software
        os.startfile(r"C:\WitMotion(V2024.12.27.0)/WitMotion")
        while is_test_running("WitMotion.exe"):
            pass
        # Define current WitMotion file storage directory
        dataDir = r"C:\WitMotion(V2024.12.27.0)\Record"
        # Determine current date to find folder in Record folder
        recordFolder = str(datetime.now().date())
        # Get the most recent data file from the data folder for today's date (i.e. the test that just finished)
        mostRecent = os.listdir(os.path.join(dataDir, recordFolder))[-1]

        # Create path to data file ("data_0.csv" is WitMotion's standard naming convention for data files)
        dataPath = os.path.join(dataDir, recordFolder, mostRecent, "data_0.csv")
        # Create path where data should be moved to
        targetPath = os.path.join(os.getcwd(), session["session_workspace"], "tremor.csv")

        move(dataPath, targetPath)
        session["tremor_completed"] = "Complete"

    # Check to see if all of the tests have been compelted
    if all([session["tremor_completed"] == "Complete", session["survey_completed"] == "Complete", session["handmotion_completed"] == "Complete", session["speech_completed"] == "Complete"]):
        session["all_complete"] = True

    return jsonify({"Status" : "Trial completed successfully"})

# Return data files associated with each session
@app.route('/session_variables')
def session_vars():
    return(jsonify(session))


# Run the machine learning algorithm
@app.route('/run_algorithm')
def run_algorithm():
    print("Running the algorithm!")
    # Run prediction on handmotion, voice samples, tremor samples
    predictions = run_prediction(f"{session['session_workspace']}/pressure.csv", f"{session['session_workspace']}/speech_test.wav", f"{session['session_workspace']}/tremor.csv")
    pprint(predictions, sort_dicts=False)
    # Write information to a JSON file
    with open(f"{session['session_workspace']}/{session['session_num']}_predictions.JSON", "w") as file:
        file.write(dumps(predictions, indent=4))
    return jsonify({"Status" : "Predictions completed successfully"})


# Return data files associated with each session
@app.route('/session_data/<sessionNum>')
def session_data(sessionNum):
    # Define full paths for each of the survey types
    averaged_survey_path = f"./static/patient_data/{session['id']}/{session['id']}_sessions/session_{sessionNum}/{sessionNum}_survey.csv"
    full_survey_path = f"./static/patient_data/{session['id']}/{session['id']}_sessions/session_{sessionNum}/{sessionNum}_full_survey.csv"
    # Convert data to pandas dataframe to return to JS
    averaged_data = read_csv(averaged_survey_path).to_dict(orient="records")
    full_data = read_csv(full_survey_path).to_dict(orient="records")
    # Read in prediction data
    with open(f"./static/patient_data/{session['id']}/{session['id']}_sessions/session_{sessionNum}/{sessionNum}_predictions.JSON") as file:
        predictions = load(file)

    return jsonify({
        "radarData" : averaged_data,
        "fullData" : full_data,
        "predictions" : predictions
    })

# Collect each of the session dates to fill in the Review page select combobox
@app.route("/view_test_dates")
def test_dates():
    with open(f"./static/patient_data/{session['id']}/{session['id']}_sessions/info.JSON") as file:
        return(jsonify(load(file)))

######################################################################################################
###---------------------------------------Program Functions----------------------------------------###
######################################################################################################
# Check the number of previous sessions, create a new one if one has not been started, and assign that session number to a Flask session variable
def check_session_number():
    # Get number of previously made sessions by counting folders stored in {id#}_sessions + info.JSON (which makes it one more than total number of files)
    session["session_num"] = len(os.listdir(f"./static/patient_data/{session['id']}/{session['id']}_sessions"))
    # Make directory for this session in the patient's folder
    os.makedirs(f"./static/patient_data/{session['id']}/{session['id']}_sessions/session_{session['session_num']}", exist_ok=True)
    # Save the session workspace for data to be stored to
    session["session_workspace"] = f"./static/patient_data/{session['id']}/{session['id']}_sessions/session_{session['session_num']}"
    # Update the info.JSON file to reflect what testing number this is and the date that it occurred
    with open(f"./static/patient_data/{session['id']}/{session['id']}_sessions/info.JSON", "r+") as file:
        session_list = load(file)
        # Get number of date entries (i.e. number of current sessions)
        session_list[session["session_num"]] = str(datetime.now().date())
        file.seek(0)    # Move cursor to beginning
        file.write(dumps(session_list, indent=4))
        file.truncate()

# Detect if applications (.exe files) are running
def is_test_running(process_name):
    for process in process_iter(['name']):
        if process.info['name'] and process_name.lower() in process.info['name'].lower():
            return True
    return False

######################################################################################################
###----------------------------------------------Main----------------------------------------------###
######################################################################################################
if __name__ == "__main__":
    app.run(debug=True)
    


