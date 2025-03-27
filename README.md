# Immune Atlas Application

This repository contains a Streamlit application for analyzing cytometry data across different cancer types to identify optimal patient subsets for drug development.

## Overview

The Immune Atlas is designed to aggregate and analyze cytometry datasets to help answer critical questions in drug development:

1. Which cancer type should I focus on?
2. Within a cancer type, which subset of patients is likely to respond?
3. Within a drug type, which subset of patients is likely to respond?
4. How to optimize the product?

## Components

1. **Streamlit Application** (`app.py`): Interactive web interface for exploring cytometry data
2. **Database Module** (`immune_atlas_db.py`): SQLite database schema and data generation scripts
3. **Utility Functions** (`immune_atlas_utils.py`): Helper functions for data analysis and visualization

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/immune-atlas.git
cd immune-atlas

# Install requirements
pip install -r requirements.txt
```

## Usage

```bash
# Initialize the database with sample data
python immune_atlas_db.py

# Start the Streamlit application
streamlit run app.py
```

## Features

### Cohort Explorer
- View available cohorts and their statistics
- Analyze patient demographics and response rates
- Explore specimen distribution

### Cell Population Analysis
- Analyze specific cell types across responders and non-responders
- Track cell population changes over different timepoints
- Compare cell distributions between blood and tumor specimens

### Responder Analysis
- Identify cell types that discriminate between responders and non-responders
- Analyze response patterns by drug class
- Generate predictive insights for patient selection

## Data Structure

The application uses a database with the following tables:

1. **cohorts**: Information about patient cohorts by cancer type
2. **patients**: Individual patient records with response status
3. **specimens**: Specimen data including timepoint and specimen type
4. **cell_populations**: Cell type counts and percentages for each specimen

## Sample Data

The application includes a data generation module that creates realistic sample data for testing and demonstration purposes. The generated data includes:

- 5 cohorts (Melanoma, UC and Bladder, NSCLC)
- Patients with responder/non-responder status
- Specimens at different timepoints (Baseline, C1D1, C1D14, C2D1, C2D14)
- Cell population data for various immune cell types


## Acknowledgements

This application is based on the Immune Atlas specification for aggregating and analyzing cytometry datasets.