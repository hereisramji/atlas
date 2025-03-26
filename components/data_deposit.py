# components/data_deposit.py
import streamlit as st
from sqlalchemy.orm import Session
from database.models import Cohort
import pandas as pd

def show_data_deposit_section(db_session: Session):
    """Display the data deposit section of the Immune Atlas app"""
    
    st.header("Contribute to the Immune Atlas")
    st.write("""
    By contributing deidentified cytometry datasets, you help build a powerful resource for cancer research and drug development. 
    We offer tailored incentives for both industry and academic contributors.
    """)

    # Tabs for Incentives
    tab1, tab2 = st.tabs(["For Drug Developers (Industry)", "For Academics"])
    
    with tab1:
        st.subheader("Incentives for Drug Developers")
        st.write("""
        - **Data Contribution**: Provide datasets (e.g., 207 DLBCL patients treated with Axi-Cel, CD27+CD28+CD8+ T cells).
        - **Payment Model**:
          - Revenue Share: Percentage of subscription revenue (e.g., $10,000/year for Atlas access) based on usage proportion, capped at 20\% amongst contributors.
          - Licensing Bonus: \$5,000 - \$50,000 for high-impact datasets (e.g., cited in drug approvals).
        - **Deidentification Support**: Tools to ensure HIPAA/GDPR compliance.
        - **Attribution**: Optional credit in publications (e.g., "Data provided by XYZ Pharma").
        - **Example**: XYZ Pharma earns \$100 from 100 queries (\$1 each) \+ \$500 from 5\% of a \$10,000 subscription, totaling \$600 plus potential bonuses.
        """)

    with tab2:
        st.subheader("Incentives for Academics")
        st.write("""
        - **Data Contribution**: Provide datasets (e.g., 100 untreated NSCLC patients).
        - **Payment Model**: Revenue share up to 20% of subscription revenue, split by usage.
        - **Non-Financial Incentives**:
          - Co-authorship or acknowledgment in Atlas papers.
          - Free/discounted Atlas access (e.g., 1-year subscription worth $10,000).
          - Public ranking of dataset usage (e.g., "Top 10 Most Used Academic Datasets").
          - Deidentification support for privacy compliance.
        - **Example**: Stanford earns \$120,000 for 40\% of 250 queries from a \$300,000 pool.
        """)

        # Sample payout table
        st.write("Example Academic Payout Distribution:")
        payout_data = {
            "Institution": ["Stanford", "MGH", "UCSF", "HCI"],
            "Number of Queries": [100, 80, 40, 30],
            "Proportion of Queries": ["40%", "32%", "16%", "12%"],
            "Revenue Share": ["8%", "6%", "3%", "2%"],
            "Revenue Payout": ["$120,000", "$96,000", "$48,000", "$36,000"]
        }
        st.table(payout_data)
    
    # Add the data upload component here
    st.header("Upload Your Data")
    st.write("""
    Please provide information about your dataset below. Fields marked with * are required.
    """)

    # Get existing disease options from the database
    existing_indications = db_session.query(Cohort.indication).distinct().all()
    existing_indications = [ind[0] for ind in existing_indications]  # Extract from tuples
    
    # Create columns for the form layout
    col1, col2 = st.columns(2)

    with col1:
        # First column of inputs
        disease = st.text_input("Disease *", help="E.g., NSCLC, Melanoma, Bladder Cancer")
        
        # Get disease type based on indication
        disease_type_options = ["Cancer", "Autoimmune"]
        default_index = 0
        if disease in existing_indications:
            # Find the disease type from the database
            cohort = db_session.query(Cohort).filter(Cohort.indication == disease).first()
            if cohort and cohort.type in disease_type_options:
                default_index = disease_type_options.index(cohort.type)
        
        disease_type = st.selectbox("Disease Type *", options=disease_type_options, index=default_index)
        
        drug_class = st.text_input("Drug Class *", help="E.g., PD-1, TCR")
        specific_drug = st.text_input("Specific Drug", help="Optional: E.g., Pembrolizumab, Nivolumab")
        num_patients = st.number_input("Number of Patients *", min_value=1, value=10, step=1)
        num_timepoints = st.number_input("Number of Timepoints *", min_value=1, value=4, step=1)

    with col2:
        # Second column of inputs
        responders = st.number_input("Responders *", min_value=0, value=0, step=1)
        non_responders = st.number_input("Non-Responders *", min_value=0, value=0, step=1)
        tumor_escaped = st.number_input("Tumor Escaped", min_value=0, value=0, step=1, 
                                    help="Optional: Patients who initially responded but then relapsed")
        
        # Calculate number of specimens automatically
        num_specimens = num_patients * num_timepoints
        st.number_input("Number of Specimens", min_value=num_specimens, value=num_specimens, 
                   step=1, disabled=True, 
                   help="Automatically calculated as Number of Patients × Number of Timepoints")
        
        # Validation check
        patient_sum = responders + non_responders + tumor_escaped
        if patient_sum != num_patients:
            st.warning(f"Sum of Responders, Non-Responders, and Tumor Escaped ({patient_sum}) does not match Number of Patients ({num_patients})")

    # File upload for the actual data
    st.subheader("Upload Your Dataset Files")
    st.write("""
    Please upload your cytometry data files. We accept FCS files or CSV/Excel files with processed cytometry data.
    All files will be deidentified during processing.
    """)

    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True)

    if uploaded_files:
        st.write(f"{len(uploaded_files)} file(s) uploaded")
        # Display list of uploaded files
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size} bytes)")

    # Consent and submit
    st.subheader("Consent and Submission")
    consent = st.checkbox("I confirm that this data has been properly deidentified and I have the right to share it")
    contributor_type = st.radio("I am contributing as:", ["Industry/Pharmaceutical Company", "Academic Institution"])

    if contributor_type == "Industry/Pharmaceutical Company":
        company_name = st.text_input("Company Name")
        attribution = st.checkbox("I would like attribution in publications using this data")
        contributor_details = {"Company": company_name, "Attribution": "Yes" if attribution else "No"}
    else:
        institution_name = st.text_input("Institution Name")
        researcher_name = st.text_input("Principal Investigator Name")
        publication = st.text_input("Related Publication (if any)")
        contributor_details = {
            "Institution": institution_name, 
            "Researcher": researcher_name,
            "Publication": publication if publication else "None"
        }

    submit_button = st.button("Submit Dataset", disabled=not consent)

    if submit_button:
        # Validation before submission
        if not disease or not drug_class or num_patients < 1 or num_timepoints < 1:
            st.error("Please fill in all required fields marked with *")
        elif patient_sum != num_patients:
            st.error("The sum of Responders, Non-Responders, and Tumor Escaped must equal the Number of Patients")
        elif not uploaded_files:
            st.error("Please upload at least one data file")
        else:
            # In a real app, you would save to the database here
            # For this demo, we'll just show a success message
            
            # Create a new cohort object
            # new_cohort = Cohort(
            #     indication=disease,
            #     type=disease_type,
            #     num_specimens=num_specimens,
            #     num_patients=num_patients,
            #     analyzed_specimens=num_specimens,
            #     treatment=specific_drug if specific_drug else drug_class
            # )
            # db_session.add(new_cohort)
            # db_session.commit()
            
            # Success message with summary
            st.success("Dataset submitted successfully! Thank you for your contribution.")
            st.balloons()
            
            # Summary of submission
            st.subheader("Submission Summary")
            summary_data = {
                "Disease": [disease],
                "Type": [disease_type],
                "Drug Class": [drug_class],
                "Specific Drug": [specific_drug if specific_drug else "Not specified"],
                "Number of Patients": [num_patients],
                "Number of Timepoints": [num_timepoints],
                "Responders": [responders],
                "Non-Responders": [non_responders],
                "Tumor Escaped": [tumor_escaped],
                "Number of Specimens": [num_specimens],
                "Files Uploaded": [len(uploaded_files)]
            }
            
            # Add contributor-specific details
            for key, value in contributor_details.items():
                summary_data[key] = [value]
                
            st.dataframe(pd.DataFrame(summary_data))
            
            # Incentives reminder based on contributor type
            if contributor_type == "Industry/Pharmaceutical Company":
                st.info("""
                **Thank you for your contribution!** As an industry contributor, you may be eligible for:
                - Revenue share from Atlas subscriptions based on dataset usage
                - Licensing bonuses for high-impact datasets
                - Optional attribution in publications
                
                We will contact you shortly with confirmation and additional details.
                """)
            else:
                st.info("""
                **Thank you for your contribution!** As an academic contributor, you may be eligible for:
                - Revenue share from Atlas subscriptions based on dataset usage
                - Co-authorship or acknowledgment in Atlas papers
                - Free/discounted Atlas access
                - Public ranking in "Top Used Academic Datasets"
                
                We will contact you shortly with confirmation and additional details.
                """)