# Mouse USV ASD Pipeline

This project processes ultrasonic vocalizations (USVs) of mouse pups and classifies each pup as **healthy** or **ASD-related**, following the workflow used in the original research.

The system covers the full pipeline: loading recordings and metadata, extracting syllables, running segmentation, generating acoustic features, and performing ASD classification.

---

## Repository Structure

### **ASD_Tool/**
Main implementation of the project:

- End-to-end pipeline scripts
- Feature extraction functions
- Segmentation logic (based on the original research flow)
- Classification models and utilities
- Evaluation helpers

This is the core folder containing the actual algorithmic work.

---

### **running_data/**
Example input structure:

- Metadata files prepared manually in the lab  
- Sample session folders  
- Example audio recordings  

These show how input data should be organized for the pipeline.

---

### **docs/**
Documentation and notes, including:  
- Notes on the original research process  

---

### **requirements.txt**
Dependency list for the original project, including TensorFlow, librosa, numpy, pandas, and all required Python packages.

---

### **README.md**
Project overview and description.

---

## Pipeline Overview

1. **Load Metadata**  
   Reads the metadata file containing: pup name, session, day, start/end frequencies, and other fields.

2. **Load Audio Files**  
   Imports the WAV recordings for each session.

3. **Segmentation**  
   Extracts syllables (USVs) from raw audio.  
   **Important:** The original segmentation script from the lab is missing and must be obtained to reproduce the results fully.

4. **Feature Extraction**  
   Derives acoustic and spectral features from each syllable.

5. **Classification**  
   Uses the original ASD classifier to categorize each pup as healthy or ASD-related.

6. **Output**  
   Generates per-pup predictions, processed data files, and logs.

---

## Current Status

- Feature extraction and classification modules are included in the repository.
- The segmentation module used in the original research is **not included** and is required to complete the full pipeline.
- The available data is partial. Full dataset access requires access to the BGU lab servers.

---
