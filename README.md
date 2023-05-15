# USV_Project
This purpose of this project is to classifiy mouse pups into two categories: healty or has an ASD


**Installation**
* In order to run this project use python3.8 and install requiremets.txt
* The main function to run is ASD_Tool/ASD_tool.py

pip install --upgrade pip
python3 -m pip install -r requirements.txt

for the whole original project:
download https://drive.google.com/drive/folders/1oSipZLnoeQB0Awz8U68KYeCPsULy_dQ7

in case of incapatability issues with tensorflow:
pip install ~/Downloads/tensorflow-2.4.1-py3-none-any.whl

**Input**

The input for this function are 
1. the files which are located in the folder running_files. This files are created manually according to the recoring hirarchy, such as mom's name, pup's name, and session and from the file "קובץ עכברים" which is created manually in the labrotary. The input file contains the following columns:

"Name", "Day", "Session", "Start Point (Hz)", "End Point (Hz)", "Duration (time)", "Syllable number", "Recording Number", "Mother Genotype", "Sex", "ISI_time", "Offspring Genotype"

TODO: create a script in order to automatically generate the files similar to the files in the running_files folder.
TODO: create "קובץ עכברים" for the year 2023

2. the recorings which are located in the USD_Recorings
3. The Strain of the mouses. This was added manually according to the year as follows: 2015 and 2018 → 1, 2022 → 2


**Steps in the ASD_tool.py**

1. Syl Classification
    statistics_generator.py extracts the features, 
    statistics_tests.py filter out reaults which are less than 50% accuracy
2. audio_feature_extraction_reduction_by_recording.py (converted from עותק של audio_feature_extraction_REDUCTION_BY_RECORDING_new.ipynb) - creates features
3. Features.py (converted from עותק של StartEndFrequency.ipynb) - extracts start and end of the frequency
4. Add Strain according to year

Features:
Mother - mother's name
Name - pup's name
Number Recording - recording number
freq_s_9syll: freq_s_0syll – average of the start of the frequency for each syllable
freq_e_9syll: freq_e_0syll – average of the end of the frequency for each syllable
dist_9syll: dist_0syll - distribution of each syllable
dur_9syll: dur_0syll – average duration for each syllable
Mother Gen: WT → 1 ,HT → 0 
Sex: – male → 0, female → 1
time_ISI_avg – average time between the syllables
Age – age of the mouse
Session – session number
Strain: BALB.C → 2 ,BALB.C X C57B6 → 1
Pup Gen: WT → 1 ,HT → 0
idx_mouse – id of the mouse

5. final_classification.py (converted from עותק של final_classification_new.ipynb) extracts confusiopn matrix and other statistics on the final model. The columns which are inut to the final classification are:
'syll1_s_freq','syll2_s_freq','syll3_s_freq','syll4_s_freq','syll5_s_freq','syll6_s_freq','syll7_s_freq','syll8_s_freq','syll9_s_freq','syll10_s_freq','syll1_e_freq','syll2_e_freq','syll3_e_freq','syll4_e_freq','syll5_e_freq','syll6_e_freq','syll7_e_freq','syll8_e_freq','syll9_e_freq','syll10_e_freq','syll1_dist','syll2_dist','syll3_dist','syll4_dist','syll5_dist','syll6_dist','syll7_dist','syll8_dist','syll9_dist','syll10_dist','syll1_dur','syll2_dur','syll3_dur','syll4_dur','syll5_dur','syll6_dur','syll7_dur','syll8_dur','syll9_dur','syll10_dur','mother_gen','pup_sex','avg_ISI_time','pup_age','session','pup_strain','pup_gen','mouse_idx'


Segmentation:
Complex - 0
Frequency steps - 1
Composite - 2
Two syllables - 3
Upward - 4
Flat - 5
Harmonic - 6
Downward - 7
Chevron - 8
Short - 9
Undefined - 10








