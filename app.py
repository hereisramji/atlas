# app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
from sqlalchemy import text
from sqlalchemy import func, desc
from models import Patient, Specimen

# Import custom modules
import immune_atlas_utils as utils
from database import DatabaseManager

# Application title and description
st.set_page_config(page_title="Immune Atlas", layout="wide")
st.title("Immune Atlas - Cytometry Data Explorer")
st.markdown("""
This application provides insights into cytometry datasets across different cancer types, 
helping identify optimal patient subsets for drug development.
""")

# Database debugging function
def check_database():
    try:
        engine = db.engine
        with engine.connect() as conn:
            cohort_count = conn.execute(text("SELECT COUNT(*) FROM cohorts")).scalar()
            patient_count = conn.execute(text("SELECT COUNT(*) FROM patients")).scalar()
            specimen_count = conn.execute(text("SELECT COUNT(*) FROM specimens")).scalar()
            cell_pop_count = conn.execute(text("SELECT COUNT(*) FROM cell_populations")).scalar()
            cell_count = conn.execute(text("SELECT COUNT(*) FROM cells")).scalar()
            marker_count = conn.execute(text("SELECT COUNT(*) FROM cell_markers")).scalar()
            
            # Get some specimen statistics
            specimen_stats = conn.execute(text("""
                SELECT p.patient_id, COUNT(s.specimen_id) as specimen_count
                FROM patients p 
                LEFT JOIN specimens s ON p.patient_id = s.patient_id
                GROUP BY p.patient_id
                ORDER BY specimen_count DESC
                LIMIT 5
            """)).fetchall()
            
        st.sidebar.write("Database Status:")
        st.sidebar.write(f"- Cohorts: {cohort_count}")
        st.sidebar.write(f"- Patients: {patient_count}")
        st.sidebar.write(f"- Specimens: {specimen_count}")
        st.sidebar.write(f"- Cell populations: {cell_pop_count}")
        st.sidebar.write(f"- Individual cells: {cell_count}")
        st.sidebar.write(f"- Cell markers: {marker_count}")
        
        if specimen_stats:
            st.sidebar.write("Patients with most specimens:")
            for patient_id, count in specimen_stats:
                st.sidebar.write(f"- Patient {patient_id}: {count} specimens")
        
        if cohort_count == 0:
            st.sidebar.error("No cohorts found. Database may not be initialized.")
            
    except Exception as e:
        st.sidebar.error(f"Database error: {str(e)}")
        st.sidebar.info("Trying to initialize database...")
        try:
            db.load_sample_data()
            st.sidebar.success("Database initialized successfully! Please refresh the page.")
        except Exception as init_error:
            st.sidebar.error(f"Failed to initialize database: {str(init_error)}")

# Initialize database and load sample data
@st.cache_resource
def get_database():
    """Get or create database with sample data."""
    st.sidebar.info("Initializing database connection...")
    try:
        db = DatabaseManager()
        st.sidebar.info("Loading sample data...")
        db.load_sample_data()
        st.sidebar.success("Database ready!")
        return db
    except Exception as e:
        st.sidebar.error(f"Error initializing database: {str(e)}")
        return None

db = get_database()

# Check database status
if db:
    check_database()
else:
    st.error("Failed to initialize database. Please check server logs.")
    st.stop()

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox(
    "Choose the app mode",
    ["Cohort Explorer", "Cell Population Analysis", "Individual Cell Analysis", "Responder Analysis"]
)

# Cohort Explorer
if app_mode == "Cohort Explorer":
    st.header("Cohort Explorer")
    
    # Display cohorts table
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
    
    # Debug output
    st.write(f"Debug: Found {len(cohorts_data)} cohorts")
    
    if not cohorts_df.empty:
        st.write("### Available Cohorts")
        st.dataframe(cohorts_df)
        
        # Select a cohort for detailed exploration
        selected_cohort = st.selectbox(
            "Select a cohort to explore",
            cohorts_df["cohort_id"].tolist(),
            format_func=lambda x: f"{x} - {cohorts_df[cohorts_df['cohort_id'] == x]['indication'].iloc[0]}"
        )
        
        if selected_cohort:
            # Get patients for the selected cohort
            patients_data = db.get_cohort_patients(selected_cohort)
            patients_df = pd.DataFrame(patients_data)
            
            # Debug output
            st.write(f"Debug: Found {len(patients_data)} patients for cohort {selected_cohort}")
            
            if not patients_df.empty:
                # Display patient stats
                responders = patients_df[patients_df["responder"] == True].shape[0]
                non_responders = patients_df[patients_df["responder"] == False].shape[0]
                
                st.write(f"### Cohort {selected_cohort} - Patient Statistics")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Patients", patients_df.shape[0])
                col2.metric("Responders", responders)
                col3.metric("Non-Responders", non_responders)
                
                # Plot responder distribution
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(
                    [responders, non_responders],
                    labels=["Responders", "Non-Responders"],
                    autopct='%1.1f%%',
                    colors=["#4CAF50", "#F44336"]
                )
                ax.set_title(f"Responder Distribution for Cohort {selected_cohort}")
                st.pyplot(fig)
            else:
                st.warning(f"No patients found for cohort {selected_cohort}")
    else:
        st.warning("No cohorts found in the database. Please check database initialization.")

# Cell Population Analysis
elif app_mode == "Cell Population Analysis":
    st.header("Cell Population Analysis")
    
    # Select a cohort
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
    
    if not cohorts_df.empty:
        selected_cohort = st.selectbox(
            "Select a cohort",
            cohorts_df["cohort_id"].tolist(),
            format_func=lambda x: f"{x} - {cohorts_df[cohorts_df['cohort_id'] == x]['indication'].iloc[0]}"
        )
        
        # Get a specimen from the cohort to identify available cell types
        if selected_cohort:
            patients_data = db.get_cohort_patients(selected_cohort)
            patients_df = pd.DataFrame(patients_data)
            
            # Find a patient that has specimens
            if not patients_df.empty:
                # Use SQLAlchemy ORM style instead of raw SQL
                patient_with_specimens = (
                    db.session.query(
                        Patient.patient_id,
                        func.count(Specimen.specimen_id).label("specimen_count")
                    )
                    .join(Specimen, Patient.patient_id == Specimen.patient_id)
                    .filter(Patient.cohort_id == selected_cohort)
                    .group_by(Patient.patient_id)
                    .having(func.count(Specimen.specimen_id) > 0)
                    .order_by(desc("specimen_count"))
                    .first()
                )
                
                if patient_with_specimens:
                    first_patient = patient_with_specimens[0]
                    st.info(f"Using patient {first_patient} with {patient_with_specimens[1]} specimens for analysis")
                else:
                    first_patient = patients_df["patient_id"].iloc[0]
                    st.warning(f"No patients with specimens found for cohort {selected_cohort}")
                
                # Debug output
                st.write(f"Debug: Found {len(patients_data)} patients for cohort {selected_cohort}")
                
                if not patients_df.empty:
                    first_patient = patients_df["patient_id"].iloc[0]
                    specimens_data = db.get_patient_specimens(first_patient)
                    specimens_df = pd.DataFrame(specimens_data)
                    
                    # Debug output
                    st.write(f"Debug: Found {len(specimens_data)} specimens for patient {first_patient}")
                    
                    if not specimens_df.empty:
                        first_specimen = specimens_df["specimen_id"].iloc[0]
                        cell_pops_data = db.get_specimen_cell_populations(first_specimen)
                        cell_pops_df = pd.DataFrame(cell_pops_data)
                        
                        # Debug output
                        st.write(f"Debug: Found {len(cell_pops_data)} cell populations for specimen {first_specimen}")
                        
                        # Get unique cell types
                        cell_types = cell_pops_df["cell_type"].unique().tolist() if not cell_pops_df.empty else []
                        
                        if cell_types:
                            # Select a cell type to analyze
                            selected_cell_type = st.selectbox("Select a cell type", cell_types)
                            
                            if selected_cell_type:
                                # Get cell type data for responders vs non-responders
                                cell_data = utils.get_cell_type_comparison(db.session, selected_cohort, selected_cell_type)
                                
                                # Debug output
                                st.write(f"Debug: Found {len(cell_data)} records for cell type comparison")
                                
                                if not cell_data.empty:
                                    st.write(f"### {selected_cell_type} Analysis")
                                    
                                    # Visualize average percentage by timepoint and responder status
                                    fig = utils.generate_timepoint_chart(cell_data, selected_cell_type)
                                    st.pyplot(fig)
                                    
                                    # Additional analysis - show raw data
                                    st.write("### Raw Data")
                                    st.dataframe(cell_data)
                                    
                                    # Bar chart comparing responders vs non-responders
                                    st.write("### Responders vs Non-Responders Comparison")
                                    
                                    # Aggregate data by responder status
                                    responder_summary = cell_data.groupby("responder_status")["avg_percentage"].mean().reset_index()
                                    
                                    fig, ax = plt.subplots(figsize=(8, 6))
                                    sns.barplot(x="responder_status", y="avg_percentage", data=responder_summary, ax=ax)
                                    plt.title(f"Average {selected_cell_type} Percentage by Response")
                                    plt.xlabel("Response Status")
                                    plt.ylabel("Average Percentage (%)")
                                    plt.tight_layout()
                                    
                                    st.pyplot(fig)
                                else:
                                    st.warning("No data available for the selected cell type and cohort combination.")
                        else:
                            st.warning("No cell types found in specimen data.")
                    else:
                        st.warning(f"No specimens found for patient {first_patient}.")
                else:
                    st.warning(f"No patients found for cohort {selected_cohort}.")
    else:
        st.warning("No cohorts found in the database. Please check database initialization.")

# Individual Cell Analysis
elif app_mode == "Individual Cell Analysis":
    st.header("Individual Cell Analysis")
    
    # Select a cohort
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
    
    if not cohorts_df.empty:
        selected_cohort = st.selectbox(
            "Select a cohort",
            cohorts_df["cohort_id"].tolist(),
            format_func=lambda x: f"{x} - {cohorts_df[cohorts_df['cohort_id'] == x]['indication'].iloc[0]}"
        )
        
        if selected_cohort:
            # Get patients for this cohort
            patients_data = db.get_cohort_patients(selected_cohort)
            patients_df = pd.DataFrame(patients_data)
            
            if not patients_df.empty:
                # Select a patient
                selected_patient = st.selectbox(
                    "Select a patient",
                    patients_df["patient_id"].tolist(),
                    format_func=lambda x: f"Patient {x} ({'Responder' if patients_df[patients_df['patient_id'] == x]['responder'].iloc[0] else 'Non-Responder'})"
                )
                
                if selected_patient:
                    # Get specimens for this patient
                    specimens_data = db.get_patient_specimens(selected_patient)
                    specimens_df = pd.DataFrame(specimens_data)
                    
                    if not specimens_df.empty:
                        # Select a specimen
                        selected_specimen = st.selectbox(
                            "Select a specimen",
                            specimens_df["specimen_id"].tolist(),
                            format_func=lambda x: f"Specimen {x} - {specimens_df[specimens_df['specimen_id'] == x]['timepoint'].iloc[0]} ({specimens_df[specimens_df['specimen_id'] == x]['specimen_type'].iloc[0]})"
                        )
                        
                        if selected_specimen:
                            # Get cell populations for this specimen
                            cell_pops_data = db.get_specimen_cell_populations(selected_specimen)
                            cell_pops_df = pd.DataFrame(cell_pops_data)
                            
                            if not cell_pops_df.empty:
                                # Select a cell population
                                selected_population = st.selectbox(
                                    "Select a cell population",
                                    cell_pops_df["id"].tolist(),
                                    format_func=lambda x: f"{cell_pops_df[cell_pops_df['id'] == x]['cell_type'].iloc[0]} ({cell_pops_df[cell_pops_df['id'] == x]['cell_count'].iloc[0]} cells, {cell_pops_df[cell_pops_df['id'] == x]['percentage'].iloc[0]:.2f}%)"
                                )
                                
                                if selected_population:
                                    # Get cells for this population
                                    cells_data = db.get_population_cells(selected_population)
                                    
                                    if cells_data:
                                        st.write(f"### Cells in {cell_pops_df[cell_pops_df['id'] == selected_population]['cell_type'].iloc[0]} Population")
                                        
                                        cells_df = pd.DataFrame(cells_data)
                                        
                                        # Display cells table
                                        st.dataframe(cells_df)
                                        
                                        # Allow selection of a specific cell for detailed analysis
                                        if not cells_df.empty:
                                            selected_cell = st.selectbox(
                                                "Select a cell to view marker details",
                                                cells_df["cell_id"].tolist(),
                                                format_func=lambda x: f"Cell {x}"
                                            )
                                            
                                            if selected_cell:
                                                # Get cell detail with markers
                                                cell_detail = db.get_cell_details(selected_cell)
                                                
                                                if cell_detail:
                                                    st.write(f"### Cell {selected_cell} Details")
                                                    
                                                    # Display cell properties
                                                    col1, col2 = st.columns(2)
                                                    col1.metric("Cell ID", cell_detail["cell_id"])
                                                    col2.metric("Cell Type", cell_detail["cell_type"])
                                                    
                                                    # Display marker data
                                                    if cell_detail["markers"]:
                                                        st.write("### Marker Expression")
                                                        
                                                        markers_df = pd.DataFrame(cell_detail["markers"])
                                                        
                                                        # Display markers table
                                                        st.dataframe(markers_df)
                                                        
                                                        # Create bar chart of marker intensities
                                                        fig, ax = plt.subplots(figsize=(12, 6))
                                                        bars = ax.bar(markers_df["marker_name"], markers_df["intensity"])
                                                        
                                                        # Color bars based on positive/negative status
                                                        for i, bar in enumerate(bars):
                                                            if markers_df.iloc[i]["positive"]:
                                                                bar.set_color("green")
                                                            else:
                                                                bar.set_color("red")
                                                                
                                                        plt.title("Marker Expression Intensity")
                                                        plt.xlabel("Marker")
                                                        plt.ylabel("Fluorescence Intensity")
                                                        plt.xticks(rotation=45, ha="right")
                                                        plt.tight_layout()
                                                        
                                                        # Add legend
                                                        from matplotlib.patches import Patch
                                                        legend_elements = [
                                                            Patch(facecolor="green", label="Positive"),
                                                            Patch(facecolor="red", label="Negative")
                                                        ]
                                                        ax.legend(handles=legend_elements)
                                                        
                                                        st.pyplot(fig)
                                                    else:
                                                        st.warning("No marker data available for this cell.")
                                                else:
                                                    st.error("Could not retrieve cell details.")
                                        else:
                                            st.warning("No cells found in this population.")
                                    else:
                                        st.warning("No cells found for this population.")
                            else:
                                st.warning("No cell populations found for this specimen.")
                    else:
                        st.warning("No specimens found for this patient.")
            else:
                st.warning("No patients found for this cohort.")
    else:
        st.warning("No cohorts found in the database.")

# Responder Analysis
elif app_mode == "Responder Analysis":
    st.header("Responder Analysis")
    
    # Select a cohort
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
    
    if not cohorts_df.empty:
        selected_cohort = st.selectbox(
            "Select a cohort",
            cohorts_df["cohort_id"].tolist(),
            format_func=lambda x: f"{x} - {cohorts_df[cohorts_df['cohort_id'] == x]['indication'].iloc[0]}"
        )
        
        if selected_cohort:
            # Get cell type distribution differences between responders and non-responders
            discriminating_cell_types = utils.find_discriminating_cell_types(db.session, selected_cohort)
            
            # Debug output
            st.write(f"Debug: Found {len(discriminating_cell_types)} discriminating cell types")
            
            if not discriminating_cell_types.empty:
                st.write("### Cell Types Discriminating Between Responders and Non-Responders")
                
                # Display the discriminating cell types
                st.dataframe(discriminating_cell_types)
                
                # Plot differences
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.barplot(x='cell_type', y='difference', data=discriminating_cell_types, ax=ax)
                plt.title('Difference in Cell Type Percentage (Responders - Non-Responders)')
                plt.xlabel('Cell Type')
                plt.ylabel('Percentage Difference')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Plot side-by-side comparison
                fig, ax = plt.subplots(figsize=(14, 8))
                
                # Prepare data for plotting
                plot_data = pd.melt(
                    discriminating_cell_types,
                    id_vars=['cell_type'],
                    value_vars=['avg_percentage_responder', 'avg_percentage_non_responder'],
                    var_name='Group',
                    value_name='Percentage'
                )
                
                # Clean up group names for display
                plot_data['Group'] = plot_data['Group'].map({
                    'avg_percentage_responder': 'Responders',
                    'avg_percentage_non_responder': 'Non-Responders'
                })
                
                # Plot side-by-side bars
                sns.barplot(x='cell_type', y='Percentage', hue='Group', data=plot_data, ax=ax)
                plt.title('Cell Type Distribution Comparison')
                plt.xlabel('Cell Type')
                plt.ylabel('Average Percentage (%)')
                plt.xticks(rotation=45, ha='right')
                plt.legend(title='')
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Allow user to select a cell type for detailed analysis
                st.write("### Detailed Cell Type Analysis")
                selected_cell_type = st.selectbox(
                    "Select a cell type for detailed analysis",
                    discriminating_cell_types["cell_type"].tolist()
                )
                
                if selected_cell_type:
                    # Get drug distribution for the selected cell type
                    drug_distribution = utils.get_cell_type_distribution_by_drug(
                        db.session, selected_cohort, selected_cell_type
                    )
                    
                    # Debug output
                    st.write(f"Debug: Found {len(drug_distribution)} drug distribution records")
                    
                    if not drug_distribution.empty:
                        st.write(f"### {selected_cell_type} Distribution by Drug Class")
                        st.dataframe(drug_distribution)
                        
                        # Plot distribution by drug class
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(x='drug_class', y='avg_percentage', hue='responder_status', data=drug_distribution, ax=ax)
                        plt.title(f'{selected_cell_type} Distribution by Drug Class')
                        plt.xlabel('Drug Class')
                        plt.ylabel('Average Percentage (%)')
                        plt.tight_layout()
                        
                        st.pyplot(fig)
                    else:
                        st.warning("No drug class data available for this cell type.")
            else:
                st.warning("No discriminating cell types found for this cohort.")
    else:
        st.warning("No cohorts found in the database. Please check database initialization.")

# Footer with additional information
st.sidebar.markdown("---")
st.sidebar.info(
    """
    This Immune Atlas application helps identify optimal cancer types and 
    patient subsets for drug development by analyzing cytometry datasets.
    """
)

# Ensure database is closed when the app exits
def cleanup():
    if db:
        db.close()

import atexit
atexit.register(cleanup)