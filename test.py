# I used that do convert it:
import pandas as pd
dataframes1 = {}
patientfile = "static/patient_data/4067391/4067391_sessions/session_2/tremor.csv"
df = pd.read_csv(patientfile)

# df['id'].dtype
columns = ['Time', 'Acceleration X(g)', 'Acceleration Y(g)', 'Acceleration Z(g)', 'A', 'B', 'C']
 
# df2 = pd.read_csv(file_path, delimiter=",")
df.columns = columns
df =df.drop(columns=['A', 'B', 'C'])
df.to_csv("static/patient_data/4067391/4067391_sessions/session_2/tremor.csv", index=False)
# print(df)