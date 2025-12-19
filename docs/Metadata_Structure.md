# Metadata Files Structure

## Overview

The metadata files are organized by year (2015, 2018, 2022) and contain information about mouse mothers, pups, recording sessions, and experimental conditions.

## File Organization

### 2015 Data (8 files)
- **Files**: `Data 2015 For Syl Segmentation_1.xlsx` through `_8.xlsx`
- **Total records**: ~9,500 records across all files
- **Why split into 8 parts?**
  - Each file contains different groups of mothers and pups
  - Files are organized by experimental groups/batches
  - Some files contain only HT (Heterozygous) genotype, some only WT (Wild Type), some mixed
  - Different files cover different combinations of Days (6, 8, 10, 12)
  - Each file has a different range of Recording Numbers, suggesting separate processing periods

### 2018 Data (4 files)
- **Files**: `Data 2018 For Syl Segmentation_1.xlsx` through `_4.xlsx`
- **Total records**: ~5,600 records across all files
- Each file contains 1-2 unique mothers and 3-5 unique pups
- Minimal overlap between files

### 2022 Data (4 files)
- **Files**: `Data 2022 For Syl Segmentation_2.xlsx` through `_4.xlsx`
- **Total records**: ~3,700 records across all files
- Each file contains 2-3 unique mothers and 3-8 unique pups
- Some overlap between files (shared mothers)

## File Structure

Each metadata file contains the following columns:
- **Mother**: Mother mouse ID
- **Mother Genotype**: HT (Heterozygous) or WT (Wild Type)
- **Name**: Pup name/ID
- **Sex**: Mouse sex
- **Offspring Genotype**: Pup genotype
- **Day**: Experimental day (typically 6, 8, 10, or 12)
- **Session**: Recording session number (1 or 2)
- **Recording Number**: Unique recording identifier

## Key Observations

1. **Division by experimental groups**: Files are split by different mother/pup groups, not randomly
2. **Genotype separation**: Some files contain only one genotype (HT or WT), others are mixed
3. **Day coverage**: Most files cover multiple days (6, 8, 10, 12), but some are limited to specific days
4. **Recording ranges**: Each file has a distinct range of Recording Numbers, indicating separate processing batches

## Usage

The pipeline processes each metadata file independently:
- Loads metadata from `metadata/` directory
- Extracts year from filename (characters 5-9)
- Processes all recordings listed in the file
- Generates output files in `outputs/` directory
