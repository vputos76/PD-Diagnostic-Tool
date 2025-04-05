import pickle
# from tabulate import tabulate
import pandas as pd
from feature_extraction import HandMotionFeatureExtractor, Feature_Extraction_v, FeatureExtractor_RT
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from pprint import pprint

def run_prediction(hm, voice, rt):

    # patientfile_HM = "utils/test_ML_patient_data/pressure.csv"
    # patientfile_v = "utils/test_ML_patient_data/AH_545616858-3A749CBC-3FEB-4D35-820E-E45C3E5B9B6A.wav"
    # patientfile_RT = "utils/test_ML_patient_data/RT_test.csv"
    patientfile_HM = hm
    patientfile_v = voice
    patientfile_RT = rt
    ################################ Hand Motion ##################################################
    extractor = HandMotionFeatureExtractor()  
    extractor.extract_features(patientfile_HM)  
    HM_df = extractor.get_feature_dataframe() 

    with open("utils/trained_models/scaler_HM.pkl", "rb") as f:
        scaler_HM = pickle.load(f)
    # with open("trained_models/pca_HM.pkl", "rb") as f:
    #     pca_HM = pickle.load(f)
    with open("utils/trained_models/best_XGB_model_HM.pkl", "rb") as f:
        best_model_HM = pickle.load(f)

    scaled_data_HM = scaler_HM.transform(HM_df)
    # pca_data_HM = pca_HM.transform(scaled_data_HM)
    predictions_HM = best_model_HM.predict(scaled_data_HM)
    confidences_HM = best_model_HM.predict_proba(scaled_data_HM)
    # print("Hand Motion", predictions_HM)

    ############################ voice ##########################################################
    extractor_v = Feature_Extraction_v()
    extractor_v.remove_noise_and_trim(patientfile_v, "utils/test_ML_patient_data/output_test.wav")
    df_v = extractor_v.extract_voice_features("utils/test_ML_patient_data/output_test.wav", 20, 16000, "Hertz")

    with open("utils/trained_models/scaler_knn_v.pkl", "rb") as f:
        scaler_v = pickle.load(f)
    # with open("trained_models/pca_v.pkl", "rb") as f:
    #     pca_v = pickle.load(f)
    with open("utils/trained_models/KNN_model_voice.pkl", "rb") as f:
        best_model_v = pickle.load(f)

    scaled_data_v = scaler_v.transform(df_v)
    # pca_data_v = pca_v.transform(scaled_data_v)
    predictions_v = best_model_v.predict(scaled_data_v)
    confidences_v = best_model_v.predict_proba(scaled_data_v)
    # print("voice", predictions_v)

    ######################################### resting tremor ##############################################
    extractor_RT = FeatureExtractor_RT()
    df_RT = extractor_RT.process_dataframe(patientfile_RT)

    with open("utils/trained_models/scaler_rf.pkl", "rb") as f:
        scaler_rt = pickle.load(f)
    # with open("trained_models/pca_v.pkl", "rb") as f:
    #     pca_v = pickle.load(f)
    with open("utils/trained_models/best_rf_model_RT.pkl", "rb") as f:
        best_model_rt = pickle.load(f)

    scaled_data_RT = scaler_rt.transform(df_RT)
    # pca_data_v = pca_v.transform(scaled_data_v)
    predictions_RT = best_model_rt.predict(scaled_data_RT)
    confidences_RT = best_model_rt.predict_proba(scaled_data_RT)
    # print("Resting Tremor", predictions_RT)

    ################################## Weighetd Voting #############################################
    conf_HM = confidences_HM[0][1]  
    conf_v  = confidences_v[0][1] 
    conf_RT = confidences_RT[0][1] 

    # Extract predictions (0 or 1)
    pred_HM = predictions_HM[0]
    pred_v  = predictions_v[0]
    pred_RT = predictions_RT[0]

    weighted_vote = (conf_HM * pred_HM) + (conf_v * pred_v) + (conf_RT * pred_RT)
    # threshold at 1.5 (half of max sum 3)
    final_class = 1 if weighted_vote >= 1.5 else 0


    ############################ Display Results in a Table #############################################
    # results_df = pd.DataFrame([
    #     ["Hand Motion", pred_HM, f"{conf_HM:.4f}"],
    #     ["Voice", pred_v, f"{conf_v:.4f}"],
    #     ["Resting Tremor", pred_RT, f"{conf_RT:.4f}"],
    #     ["Weighted Vote", f"{weighted_vote:.4f}", "N/A"],
    #     ["Final Classification", final_class, "N/A"]
    # ], columns=["Model", "Prediction", "Confidence"])

    results_dict = {
        "conf_HM": round(float(conf_HM), 3),
        "conf_v": round(float(conf_v), 3),
        "conf_RT": round(float(conf_RT), 3),
        "pred_HM": round(float(pred_HM), 3),
        "pred_v": round(float(pred_v), 3),
        "pred_RT": round(float(pred_RT), 3),
        "weighted_vote": round(float(weighted_vote), 3),
        "final_class": round(float(final_class), 3)
    }

    return results_dict

if __name__ == "__main__":
    x = run_prediction(
        hm="static/patient_data/4067391/4067391_sessions/session_2/pressure.csv",
        voice="static/patient_data/4067391/4067391_sessions/session_2/speech_test.wav",
        rt="static/patient_data/4067391/4067391_sessions/session_2/tremor.csv")
    
    pprint(x, sort_dicts=False)