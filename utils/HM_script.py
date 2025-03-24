import pickle
from feature_extraction_HM import HandMotionFeatureExtractor

patientfilepath = "test_data/pressure.csv"

extractor = HandMotionFeatureExtractor()  # Create an instance
extractor.extract_features(patientfilepath)  # Extract features
HM_df = extractor.get_feature_dataframe() 

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
with open("trained_models/scaler_HM.pkl", "rb") as f:
    scaler = pickle.load(f)
with open("trained_models/pca_HM.pkl", "rb") as f:
    pca = pickle.load(f)
with open("trained_models/best_svm_model_HandMotion.pkl", "rb") as f:
    best_svm_model = pickle.load(f)

scaled_data = scaler.transform(HM_df)
pca_data = pca.transform(scaled_data)

# Get predictions
predictions = best_svm_model.predict(pca_data)
print(predictions)