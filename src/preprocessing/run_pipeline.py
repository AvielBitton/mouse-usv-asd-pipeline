import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Allow imports from the project scripts directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))

from pytictoc import TicToc
from normalize_folder_structure import normalize_year
from pathlib import Path
from utils import (
    setup_logger,
    list_metadata_files,
    is_already_processed,
    is_segmentation_file_exist,
    get_output_filename,
    OUTPUTS_LEGACY_DIR,
    OUTPUTS_EXTERNAL_INPUT_DIR,
    parse_args,
    get_files_to_process,
)
from steps import (
    prepare_recording_metadata,
    run_segmentation,
    read_segmentation_results,
    compute_basic_features,
    run_classification,
    enrich_segmentation_columns,
    run_feature_extraction,
    run_aggregated_feature_extraction,
    run_external_aggregated_feature_extraction,
)


##################################################
#### 1: setup & file selection
##################################################
logger = setup_logger()
pipeline_outputs_dir = OUTPUTS_LEGACY_DIR
external_input_file = os.path.join(
    OUTPUTS_EXTERNAL_INPUT_DIR,
    "segmentation_classification_all_data.xlsx",
)


# Normalize folder structure (day/session/ch dirs) before processing.
# Only needed for 2023+ data which arrives with non-standard naming
# (e.g. "DAY 6" instead of "day_6", "SESSION 1" instead of "session1",
# extra "ch1/" sub-directories). Pre-2023 data already uses canonical names.
# Idempotent: already-correct names are skipped.
NORMALIZE_FROM_YEAR = 2023
recordings_root = Path("USV_Recordings")
for year_dir in sorted(recordings_root.iterdir()):
    if year_dir.is_dir() and year_dir.name.isdigit() and len(year_dir.name) == 4:
        if int(year_dir.name) >= NORMALIZE_FROM_YEAR:
            normalize_year(year_dir)

input_files = list_metadata_files("metadata")
logger.info(f"Found {len(input_files)} metadata file(s): {input_files}")

# Parse CLI arguments to check if user specified a single file to process
args = parse_args()
# Determine which files to process: all files or single file if --metadata-file was provided
# This function validates the file exists and logs the selection
files_to_process = get_files_to_process(input_files, args.metadata_file, logger)

for file_name in files_to_process:
  try:
    t = TicToc() #create instance of class
    t.tic() #Start timer
    logger.info(f"Starting file: {file_name}")

    # Skip files with existing outputs (xlsx/csv/npy) to resume safely and avoid unnecessary reprocessing
    if is_already_processed(file_name, pipeline_outputs_dir):
      logger.info(f"Skipping file (already processed): {file_name}")
      continue

    ##################################################
    #### 2: segmentation
    ##################################################
    # Load metadata + audio recordings
    (
        year,
        mother, matgen, name, sex, pupgen, age, session, rec_num,
        SignalVec, signal_name, rate, missing_count,
    ) = prepare_recording_metadata(
        file_name=file_name,
        metadata_dir="metadata",
        recordings_root="USV_Recordings",
        sr=250000,
        logger=logger,
    )
    siz = len(SignalVec)

    # Check if segmentation already exists - if so, skip segmentation step
    if is_segmentation_file_exist(file_name, pipeline_outputs_dir):
      logger.info(f"Segmentation already exists for {file_name}, skipping segmentation step")
      output_filename = get_output_filename(file_name)
      output_xlsx = os.path.join(pipeline_outputs_dir, output_filename)
    else:
      # Run segmentation: process recordings, detect syllables, save to Excel
      output_xlsx = run_segmentation(
          file_name=file_name,
          SignalVec=SignalVec,
          signal_name=signal_name,
          rate=rate,
          mother=mother,
          matgen=matgen,
          name=name,
          sex=sex,
          pupgen=pupgen,
          age=age,
          session=session,
          rec_num=rec_num,
          missing_count=missing_count,
          outputs_dir=pipeline_outputs_dir,
          logger=logger,
      )

    ##################################################
    #### 3: basic features (ISI time + start/end frequencies)
    ##################################################
    # Get output filename (different from metadata filename)
    output_filename = get_output_filename(file_name)
    
    # Read segmentation results from Excel file (using column names)
    (
        motherSyl, matgenSyl, nameSyl, sexSyl, pupgenSyl,
        ageSyl, sessionSyl, rec_numSyl, startSyl, endSyl,
    ) = read_segmentation_results(
        os.path.join(pipeline_outputs_dir, output_filename),
        logger=logger,
    )

    # Compute basic features and add 3 columns to Excel: 'ISI_time', 'Start Point (Hz)', 'End Point (Hz)'
    compute_basic_features(
        file_path=os.path.join(pipeline_outputs_dir, output_filename),
        signal_vec=SignalVec,
        siz=siz,
        mother=mother,
        name=name,
        age=age,
        session=session,
        rec_num=rec_num,
        mother_syl=motherSyl,
        name_syl=nameSyl,
        age_syl=ageSyl,
        session_syl=sessionSyl,
        rec_num_syl=rec_numSyl,
        start_syl=startSyl,
        end_syl=endSyl,
        rate=rate,
        logger=logger,
    )

    ##################################################
    #### 4: classification
    ##################################################
    output_xlsx, output_npy = run_classification(
        file_path=os.path.join(pipeline_outputs_dir, output_filename),
        year=year,
        model_path='src/models/model_weights.h6',
        age_syl=ageSyl,
        matgen_syl=matgenSyl,
        pupgen_syl=pupgenSyl,
        mother_syl=motherSyl,
        name_syl=nameSyl,
        sex_syl=sexSyl,
        session_syl=sessionSyl,
        rec_num_syl=rec_numSyl,
        start_syl=startSyl,
        end_syl=endSyl,
        logger=logger,
    )

    ##################################################
    #### 5: enrich segmentation columns
    ##################################################
    enrich_segmentation_columns(
        file_path=os.path.join(pipeline_outputs_dir, output_filename),
        year=year,
        logger=logger,
    )

    ##################################################
    #### 6: feature extraction (per file)
    ##################################################
    output_csv = run_feature_extraction(
        file_path=os.path.join(pipeline_outputs_dir, output_filename),
        year=year,
        logger=logger,
    )

    logger.info(f"Exported: {output_xlsx}, {output_csv}, {output_npy}")
    logger.info(f"Finished processing file: {file_name}")
    t.toc() #Time elapsed since t.tic()
  except Exception as e:
    logger.exception(f"Error processing file {file_name}: {e}")
    raise


##################################################
#### 7: aggregation (all files)
##################################################
if __name__ == "__main__":
  run_aggregated_feature_extraction(outputs_dir=pipeline_outputs_dir, logger=logger)
  run_external_aggregated_feature_extraction(
      external_file=external_input_file,
      enabled_filters=args.external_filter,
      logger=logger,
  )
