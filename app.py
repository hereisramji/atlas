# app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

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

# Initialize database and load sample data
@st.cache_resource
def get_database():
    """Get or create database with sample data."""
    db = DatabaseManager()
    db.load_sample_data()
    return db

db = get_database()

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox(
    "Choose the app mode",
    ["Cohort Explorer", "Cell Population Analysis", "Responder Analysis"]
)

# Cohort Explorer
if app_mode == "Cohort Explorer":
    st.header("Cohort Explorer")
    
    # Display cohorts table
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
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

# Cell Population Analysis
elif app_mode == "Cell Population Analysis":
    st.header("Cell Population Analysis")
    
    # Select a cohort
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
    selected_cohort = st.selectbox(
        "Select a cohort",
        cohorts_df["cohort_id"].tolist(),
        format_func=lambda x: f"{x} - {cohorts_df[cohorts_df['cohort_id'] == x]['indication'].iloc[0]}"
    )
    
    # Get a specimen from the cohort to identify available cell types
    if selected_cohort:
        patients_data = db.get_cohort_patients(selected_cohort)
        patients_df = pd.DataFrame(patients_data)
        
        if not patients_df.empty:
            first_patient = patients_df["patient_id"].iloc[0]
            specimens_data = db.get_patient_specimens(first_patient)
            specimens_df = pd.DataFrame(specimens_data)
            
            if not specimens_df.empty:
                first_specimen = specimens_df["specimen_id"].iloc[0]
                cell_pops_data = db.get_specimen_cell_populations(first_specimen)
                cell_pops_df = pd.DataFrame(cell_pops_data)
                
                # Get unique cell types
                cell_types = cell_pops_df["cell_type"].unique().tolist() if not cell_pops_df.empty else []
                
                # Select a cell type to analyze
                selected_cell_type = st.selectbox("Select a cell type", cell_types)
                
                if selected_cell_type:
                    # Get cell type data for responders vs non-responders
                    cell_data = utils.get_cell_type_comparison(db.session, selected_cohort, selected_cell_type)
                    
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
                        st.write("No data available for the selected cell type and cohort combination.")

# Responder Analysis
elif app_mode == "Responder Analysis":
    st.header("Responder Analysis")
    
    # Select a cohort
    cohorts_data = db.get_cohorts()
    cohorts_df = pd.DataFrame(cohorts_data)
    selected_cohort = st.selectbox(
        "Select a cohort",
        cohorts_df["cohort_id"].tolist(),
        format_func=lambda x: f"{x} - {cohorts_df[cohorts_df['cohort_id'] == x]['indication'].iloc[0]}"
    )
    
    if selected_cohort:
        # Get cell type distribution differences between responders and non-responders
        discriminating_cell_types = utils.find_discriminating_cell_types(db.session, selected_cohort)
        
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
                    st.write("No drug class data available for this cell type.")
        else:
            st.write("No data available for the selected cohort.")

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
    db.close()

import atexit
atexit.register(cleanup)