import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt

# Set page configuration
st.set_page_config(page_title="Immune Atlas Demo", layout="wide")

# Title and Introduction
st.title("Welcome to the Immune Atlas")
st.write("""
The Immune Atlas aggregates and analyzes cytometry datasets to accelerate drug development by identifying optimal cancer types and patient subsets. Explore how you can contribute data or leverage our insights below.
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
section = st.sidebar.radio("Choose an Action:", ["I am depositing data", "I am looking at data"])

# Section 1: Depositing Data
if section == "I am depositing data":
    st.header("Contribute to the Immune Atlas")
    st.write("""
    By contributing deidentified cytometry datasets, you help build a powerful resource for cancer research and drug development. We offer tailored incentives for both industry and academic contributors.
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

    # Create columns for the form layout
    col1, col2 = st.columns(2)

    with col1:
        # First column of inputs
        disease = st.text_input("Disease *", help="E.g., NSCLC, Melanoma, Bladder Cancer")
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
    else:
        institution_name = st.text_input("Institution Name")
        researcher_name = st.text_input("Principal Investigator Name")
        publication = st.text_input("Related Publication (if any)")

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
            # Success message with summary
            st.success("Dataset submitted successfully! Thank you for your contribution.")
            st.balloons()
            
            # Summary of submission
            st.subheader("Submission Summary")
            summary_data = {
                "Disease": [disease],
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
            
            if contributor_type == "Industry/Pharmaceutical Company":
                summary_data["Contributor"] = [company_name]
                summary_data["Attribution Requested"] = ["Yes" if attribution else "No"]
            else:
                summary_data["Institution"] = [institution_name]
                summary_data["Researcher"] = [researcher_name]
                summary_data["Related Publication"] = [publication if publication else "None"]
                
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

# Section 2: Looking at Data
elif section == "I am looking at data":
    st.header("Explore the Immune Atlas Data")
    st.write("""
    Analyze aggregated cytometry datasets to answer key questions like "Which cancer type should I focus on?" or "Which patient subset will respond to my drug?"
    """)

    # Sample dataset
    st.subheader("Sample Dataset")
    sample_data = {
        "Disease": ["NSCLC", "NSCLC", "Melanoma", "Bladder Cancer", "Colorectal Cancer"],
        "Drug Class": ["PD-1", "PD-1", "PD-1", "PD-1", "TCR"],
        "Specific Drug": ["Pembrolizumab", "Nivolumab", "Pembrolizumab", "Atezolizumab", "[TCR Drug X]"],
        "Number of Patients": [60, 60, 120, 120, 120],
        "Number of Timepoints": [4, 4, 4, 4, 4],
        "Responders": [20, 20, 40, 40, 40],
        "Non-Responders": [20, 20, 40, 40, 40],
        "Started to Respond, Then Tumor Escaped": [20, 20, 40, 40, 40],
        "Number of Specimens": [240, 240, 480, 480, 480]
    }
    df = pd.DataFrame(sample_data)
    st.dataframe(df)

    # Interactive Marker Expression Analysis Tool
    st.subheader("Marker Expression Analysis Tool")
    st.write("""
    Analyze how biomarker expression differs between responders and non-responders over time.
    Select your target marker and cancer type to see expression patterns that may predict response.
    """)

    # Create sample data - this would be replaced with your actual database
    # Create a list of timepoints for the x-axis
    timepoints = ["Baseline", "Day 1", "Day 14", "Day 28", "Day 42"]

    # Create a dictionary to store marker data
    # Format: {disease: {marker: {response_status: [values for each timepoint]}}}
    marker_data = {
        "NSCLC": {
            "CD69": {
                "Responders": [0.1, 0.3, 0.5, 0.7, 0.9],
                "Non-Responders": [0.1, 0.2, 0.3, 0.25, 0.2]
            },
            "CD27": {
                "Responders": [0.2, 0.4, 0.6, 0.65, 0.7],
                "Non-Responders": [0.2, 0.25, 0.3, 0.35, 0.3]
            },
            "PD-1": {
                "Responders": [0.5, 0.45, 0.4, 0.3, 0.2],
                "Non-Responders": [0.5, 0.6, 0.7, 0.8, 0.9]
            }
        },
        "Melanoma": {
            "CD69": {
                "Responders": [0.15, 0.4, 0.6, 0.8, 0.95],
                "Non-Responders": [0.15, 0.25, 0.35, 0.3, 0.25]
            },
            "CD27": {
                "Responders": [0.25, 0.45, 0.65, 0.7, 0.75],
                "Non-Responders": [0.25, 0.3, 0.35, 0.4, 0.35]
            },
            "PD-1": {
                "Responders": [0.55, 0.5, 0.45, 0.35, 0.25],
                "Non-Responders": [0.55, 0.65, 0.75, 0.85, 0.95]
            }
        },
        "Bladder Cancer": {
            "CD69": {
                "Responders": [0.12, 0.35, 0.55, 0.75, 0.85],
                "Non-Responders": [0.12, 0.2, 0.25, 0.2, 0.15]
            },
            "CD27": {
                "Responders": [0.22, 0.42, 0.62, 0.67, 0.72],
                "Non-Responders": [0.22, 0.27, 0.32, 0.37, 0.32]
            },
            "PD-1": {
                "Responders": [0.52, 0.47, 0.42, 0.32, 0.22],
                "Non-Responders": [0.52, 0.62, 0.72, 0.82, 0.92]
            }
        },
        "Colorectal Cancer": {
            "CD69": {
                "Responders": [0.08, 0.25, 0.45, 0.65, 0.75],
                "Non-Responders": [0.08, 0.15, 0.2, 0.15, 0.1]
            },
            "CD27": {
                "Responders": [0.18, 0.38, 0.58, 0.63, 0.68],
                "Non-Responders": [0.18, 0.23, 0.28, 0.33, 0.28]
            },
            "PD-1": {
                "Responders": [0.48, 0.43, 0.38, 0.28, 0.18],
                "Non-Responders": [0.48, 0.58, 0.68, 0.78, 0.88]
            }
        }
    }

    # Add "Other Markers" to demonstrate dropdown capabilities
    other_markers = ["CD28", "CD8", "CTLA-4", "LAG-3", "TIM-3"]
    for disease in marker_data:
        for marker in other_markers:
            # Generate some random but plausible data
            responder_baseline = np.random.uniform(0.1, 0.3)
            nonresponder_baseline = responder_baseline
            
            responder_values = [responder_baseline]
            nonresponder_values = [nonresponder_baseline]
            
            # Responders tend to increase or decrease based on marker
            direction = 1 if np.random.random() > 0.3 else -1
            for i in range(1, len(timepoints)):
                responder_values.append(responder_values[-1] + direction * np.random.uniform(0.05, 0.15))
                nonresponder_values.append(nonresponder_values[-1] + direction * np.random.uniform(-0.05, 0.05))
                
            # Ensure values stay within reasonable range
            responder_values = [max(0, min(1, val)) for val in responder_values]
            nonresponder_values = [max(0, min(1, val)) for val in nonresponder_values]
            
            marker_data[disease][marker] = {
                "Responders": responder_values,
                "Non-Responders": nonresponder_values
            }

    # Create dropdowns for user selection
    col1, col2 = st.columns(2)

    with col1:
        # Get all unique disease types and markers
        disease_types = list(marker_data.keys())
        selected_disease = st.selectbox("Select Disease Type", disease_types)

    with col2:
        # Get all markers for the selected disease
        markers = list(marker_data[selected_disease].keys())
        selected_marker = st.selectbox("Select Target Marker", markers)

    # Create a DataFrame for the selected data
    selected_data = marker_data[selected_disease][selected_marker]
    df = pd.DataFrame({
        "Timepoint": timepoints * 2,
        "Response Status": ["Responders"] * len(timepoints) + ["Non-Responders"] * len(timepoints),
        "Expression Level": selected_data["Responders"] + selected_data["Non-Responders"]
    })

    # Create a visualization using Altair
    st.write(f"### {selected_marker} Expression in {selected_disease} by Response Status")

    # Create line chart
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('Timepoint:N', title='Timepoint'),
        y=alt.Y('Expression Level:Q', title=f'{selected_marker} Expression Level (MFI)', scale=alt.Scale(domain=[0, 1])),
        color=alt.Color('Response Status:N', scale=alt.Scale(
            domain=['Responders', 'Non-Responders'],
            range=['#2ca02c', '#d62728']  # Green for responders, red for non-responders
        )),
        strokeWidth=alt.value(3),
        tooltip=['Timepoint', 'Response Status', 'Expression Level']
    ).properties(
        width=600,
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Add interpretation based on the selected data
    responder_trend = selected_data["Responders"][-1] - selected_data["Responders"][0]
    nonresponder_trend = selected_data["Non-Responders"][-1] - selected_data["Non-Responders"][0]
    trend_diff = abs(responder_trend - nonresponder_trend)

    if trend_diff > 0.3:
        predictive_value = "strong"
    elif trend_diff > 0.15:
        predictive_value = "moderate"
    else:
        predictive_value = "limited"

    # Interpretation section
    st.write("### Interpretation")
    st.write(f"""
    Based on Teiko's internal dataset for {selected_disease}, {selected_marker} expression shows **{predictive_value} predictive value** for treatment response:

    - **Responders** started at {selected_data["Responders"][0]:.2f} and {"increased" if responder_trend > 0 else "decreased"} to {selected_data["Responders"][-1]:.2f} by {timepoints[-1]}
    - **Non-Responders** started at {selected_data["Non-Responders"][0]:.2f} and {"increased" if nonresponder_trend > 0 else "decreased"} to {selected_data["Non-Responders"][-1]:.2f} by {timepoints[-1]}
    """)

    # Add additional information about the marker if available
    marker_info = {
        "CD69": "An early activation marker expressed on T cells, B cells, and NK cells. High expression may indicate active immune response.",
        "CD27": "A co-stimulatory molecule important for T cell activation and survival. Sustained expression may indicate effective T cell responses.",
        "PD-1": "An inhibitory checkpoint receptor expressed on activated T cells. Decreasing expression in responders may indicate relief from immunosuppression.",
        "CD28": "A co-stimulatory receptor essential for T cell activation and survival. Upregulation may indicate effective T cell priming.",
        "CD8": "A marker for cytotoxic T cells, which are important for tumor cell killing. Higher levels may indicate stronger anti-tumor immunity.",
        "CTLA-4": "An inhibitory checkpoint receptor that downregulates immune responses. Decreasing levels may indicate relief of immunosuppression.",
        "LAG-3": "An inhibitory receptor that regulates T cell function. Downregulation may correlate with improved T cell activity.",
        "TIM-3": "An inhibitory receptor associated with T cell exhaustion. Decreasing expression may indicate recovery of T cell function."
    }

    if selected_marker in marker_info:
        st.write(f"**About {selected_marker}:** {marker_info[selected_marker]}")

    # Add suggestions section based on the selected marker and disease
    st.write("### Suggestions for Drug Development")

    if responder_trend > 0 and nonresponder_trend < 0:
        st.write(f"""
        - Consider {selected_marker} as a potential pharmacodynamic biomarker for your drug in {selected_disease}
        - Monitor {selected_marker} expression at baseline and day 14-28 to identify potential responders early
        - Explore combination therapies that might enhance {selected_marker} expression in non-responders
        """)
    elif responder_trend > 0 and nonresponder_trend > 0 and responder_trend > nonresponder_trend:
        st.write(f"""
        - {selected_marker} shows promise as a pharmacodynamic marker, but additional markers may be needed for accurate response prediction
        - Consider a multi-marker panel including {selected_marker} for patient stratification
        - Investigate mechanisms driving stronger {selected_marker} upregulation in responders
        """)
    elif responder_trend < 0 and nonresponder_trend > 0:
        st.write(f"""
        - {selected_marker} shows a strong inverse correlation with response
        - Consider {selected_marker} suppression as a potential mechanism of action
        - Monitor patients with high baseline {selected_marker} carefully, as they may be less likely to respond
        """)
    else:
        st.write(f"""
        - {selected_marker} shows subtle differences between responders and non-responders in {selected_disease}
        - Consider exploring additional markers with stronger predictive value
        - {selected_marker} might be more valuable as part of a multi-marker signature rather than as a standalone biomarker
        """)

    # Add feature for comparing your drug's data (placeholder for future functionality)
    st.write("### Compare Your Drug (Coming Soon)")
    st.write("""
    Future functionality will allow you to upload your drug's marker expression data and compare it against our database.
    This will help identify whether your drug's pharmacodynamic profile matches that of successful treatments.
    """)

    # Placeholder for upload feature (to be implemented)
    upload_col1, upload_col2 = st.columns(2)
    with upload_col1:
        upload_placeholder = st.file_uploader("Upload your data (demo only)", disabled=True)
    with upload_col2:
        st.button("Compare with database", disabled=True)

    # Add advanced analytics section
    st.write("### Advanced Analytics")
    show_advanced = st.checkbox("Show additional analytics")

    if show_advanced:
        # Create tabs for different analytics views
        tab1, tab2, tab3 = st.tabs(["Response Probability", "Marker Correlation", "Marker Clustering"])
        
        with tab1:
            st.write("#### Response Probability by Marker Expression")
            st.write("This chart shows the probability of response based on marker expression levels at different timepoints.")
            
            # Generate some sample probability data
            prob_data = []
            for tp_idx, tp in enumerate(timepoints):
                # Skip baseline since it's usually the same
                if tp_idx == 0:
                    continue
                    
                expr_levels = np.linspace(0, 1, 10)
                # Calculate response probability based on the difference between responder and non-responder values
                resp_val = selected_data["Responders"][tp_idx]
                nonresp_val = selected_data["Non-Responders"][tp_idx]
                
                # If responders have higher values, probability increases with expression
                if resp_val > nonresp_val:
                    probs = [max(0, min(1, 0.5 + (val - (resp_val + nonresp_val)/2) * 2)) for val in expr_levels]
                else:
                    probs = [max(0, min(1, 0.5 - (val - (resp_val + nonresp_val)/2) * 2)) for val in expr_levels]
                
                for i, expr in enumerate(expr_levels):
                    prob_data.append({
                        "Expression Level": expr,
                        "Response Probability": probs[i],
                        "Timepoint": tp
                    })
            
            prob_df = pd.DataFrame(prob_data)
            
            # Create probability chart
            prob_chart = alt.Chart(prob_df).mark_line().encode(
                x=alt.X('Expression Level:Q', title=f'{selected_marker} Expression Level'),
                y=alt.Y('Response Probability:Q', title='Probability of Response'),
                color=alt.Color('Timepoint:N'),
                strokeWidth=alt.value(2)
            ).properties(
                width=600,
                height=300
            ).interactive()
            
            st.altair_chart(prob_chart, use_container_width=True)
            
            # Add explanation
            st.write(f"""
            This chart shows the estimated probability of response based on {selected_marker} expression level at each timepoint.
            For example, at Day 28, a {selected_marker} expression level of {(selected_data["Responders"][3] + 0.1):.2f} 
            correlates with approximately {max(0, min(1, 0.7 + np.random.uniform(-0.1, 0.1))):.0%} probability of response.
            """)
            
        with tab2:
            st.write("#### Correlation with Other Markers")
            st.write(f"How {selected_marker} expression correlates with other markers in {selected_disease}.")
            
            # Generate correlation data
            corr_markers = [m for m in markers if m != selected_marker]
            corr_values = [np.random.uniform(-0.8, 0.8) for _ in corr_markers]
            
            # Sort by absolute correlation value
            corr_data = sorted(zip(corr_markers, corr_values), key=lambda x: abs(x[1]), reverse=True)
            corr_df = pd.DataFrame({
                "Marker": [x[0] for x in corr_data],
                "Correlation": [x[1] for x in corr_data]
            })
            
            # Create correlation chart
            corr_chart = alt.Chart(corr_df).mark_bar().encode(
                x=alt.X('Correlation:Q', title='Pearson Correlation'),
                y=alt.Y('Marker:N', sort='-x', title=None),
                color=alt.condition(
                    alt.datum.Correlation > 0,
                    alt.value("#2ca02c"),  # Positive correlation
                    alt.value("#d62728")   # Negative correlation
                ),
                tooltip=['Marker', 'Correlation']
            ).properties(
                width=600,
                height=300
            )
            
            st.altair_chart(corr_chart, use_container_width=True)
            
            # Add explanation
            most_pos = corr_data[0] if corr_data[0][1] > 0 else None
            most_neg = [x for x in corr_data if x[1] < 0][0] if any(x[1] < 0 for x in corr_data) else None
            
            if most_pos:
                st.write(f"**Positive correlation:** {selected_marker} shows strongest positive correlation with {most_pos[0]} ({most_pos[1]:.2f}), suggesting they may be co-regulated or part of the same pathway.")
                
            if most_neg:
                st.write(f"**Negative correlation:** {selected_marker} shows strongest negative correlation with {most_neg[0]} ({most_neg[1]:.2f}), suggesting they may have opposing regulation or functions.")
        
        with tab3:
            st.write("#### Marker Clustering Analysis")
            st.write("This visualization shows how markers cluster together based on their expression patterns.")
            
            # Use matplotlib for a simple cluster visualization
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Generate random 2D coordinates for markers
            np.random.seed(42)  # For reproducibility
            marker_coords = {}
            for marker in markers:
                marker_coords[marker] = (np.random.uniform(0, 10), np.random.uniform(0, 10))
            
            # Plot the markers
            for marker, (x, y) in marker_coords.items():
                color = 'red' if marker == selected_marker else 'blue'
                size = 100 if marker == selected_marker else 50
                ax.scatter(x, y, c=color, s=size, alpha=0.7)
                ax.text(x + 0.1, y + 0.1, marker, fontsize=12)
            
            # Draw lines between markers that are close (simulating clusters)
            for m1 in markers:
                x1, y1 = marker_coords[m1]
                for m2 in markers:
                    if m1 != m2:
                        x2, y2 = marker_coords[m2]
                        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                        if dist < 3:  # Arbitrary threshold for "close" markers
                            ax.plot([x1, x2], [y1, y2], 'k-', alpha=0.2)
            
            ax.set_xlabel('Dimension 1 (t-SNE)')
            ax.set_ylabel('Dimension 2 (t-SNE)')
            ax.set_title(f'Marker Clustering in {selected_disease} (t-SNE Visualization)')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Remove axis ticks as they don't have meaning in t-SNE
            ax.set_xticks([])
            ax.set_yticks([])
            
            st.pyplot(fig)
            
            st.write("""
            This t-SNE plot visualizes how different markers cluster based on their expression patterns across patient samples.
            Markers that appear close together in this plot tend to have similar expression patterns and may be functionally related.
            """)
                
            # Add a note about the visualization
            st.info("Note: This is a simulated visualization for demonstration purposes. In the full product, this would be based on actual marker expression data across all samples in the database.")

    # Additional guidance
    st.write("### How to Use This Tool")
    st.write("""
    1. Select your target cancer type from the dropdown menu
    2. Choose a marker of interest to analyze
    3. Examine how marker expression differs between responders and non-responders over time
    4. Use these insights to guide your biomarker and patient selection strategy
    5. In the future, you'll be able to upload your own drug's data for direct comparison
    """)

    # Add visualization of CD69 performance over time
    st.subheader("Pharmacodynamic Profile Comparison")
    st.write("""
    Compare your drug's pharmacodynamic profile (e.g., CD69 median channel value) against the average of publicly available datasets. 
    Identify cancer types or patient subsets where your drug outperforms.
    """)

    # Create sample data for CD69 median channel values over time
    # These values approximate the graph from your document
    time_points = np.linspace(0, 3.5, 8)
    cancer_types = ["NSCLC", "Melanoma", "Bladder Cancer", "Colorectal Cancer", "Your drug"]

    # CD69 values based on the slope patterns in your document
    cd69_values = {
        "NSCLC": [0.0, 0.03, 0.05, 0.07, 0.09, 0.11, 0.14, 0.16],
        "Melanoma": [0.0, 0.07, 0.12, 0.15, 0.2, 0.24, 0.28, 0.32],
        "Bladder Cancer": [0.0, 0.1, 0.17, 0.23, 0.3, 0.35, 0.41, 0.47],
        "Colorectal Cancer": [0.0, 0.15, 0.29, 0.4, 0.5, 0.65, 0.78, 0.9],
        "Your drug": [0.0, 0.12, 0.22, 0.3, 0.38, 0.45, 0.52, 0.6]
    }

    # Create a DataFrame for plotting
    data = []
    for cancer in cancer_types:
        for i, t in enumerate(time_points):
            data.append({
                "Time": t,
                "Cancer Type": cancer,
                "CD69 Median Channel Value (MCV)": cd69_values[cancer][i]
            })
    df_cd69 = pd.DataFrame(data)

    # Set up colors that match the PDF document
    colors = {
        "NSCLC": "#4292c6",  # Blue
        "Melanoma": "#fd8d3c",  # Orange
        "Bladder Cancer": "#74c476",  # Green
        "Colorectal Cancer": "#e6550d",  # Red
        "Your drug": "#000000"  # Black
    }

    # Create the Altair chart
    st.write("### CD69 Median Channel Value Over Time")
    st.write("""
    This chart shows how your drug's CD69 median channel value compares to different cancer types over time.
    Your drug outperforms NSCLC, Melanoma, and Bladder Cancer but not Colorectal Cancer.
    """)

    chart = alt.Chart(df_cd69).mark_line().encode(
        x=alt.X('Time:Q', title='Time'),
        y=alt.Y('CD69 Median Channel Value (MCV):Q', title='CD69 Median Channel Value (MCV)'),
        color=alt.Color('Cancer Type:N', 
                       scale=alt.Scale(
                           domain=list(colors.keys()),
                           range=list(colors.values())
                       ),
                       legend=alt.Legend(title="Cancer Type")),
        strokeDash=alt.condition(
            alt.datum['Cancer Type'] == 'Your drug',
            alt.value([0]),  # solid line for "Your drug"
            alt.value([5, 5])  # dashed line for other cancer types
        ),
        strokeWidth=alt.condition(
            alt.datum['Cancer Type'] == 'Your drug',
            alt.value(3),  # thicker line for "Your drug"
            alt.value(2)
        )
    ).properties(
        width=600,
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Add interpretation
    st.write("""
    **Interpretation:**
    - Your drug shows stronger CD69 activation than NSCLC, Melanoma, and Bladder Cancer samples
    - However, Colorectal Cancer samples show higher CD69 values than your drug
    - This suggests your drug may be more effective for NSCLC, Melanoma, and Bladder Cancer
    - The data indicates you might want to prioritize clinical development in these cancer types
    """)

# Footer
st.write("---")
st.write("Contact us to learn more or start contributing: info@teiko.bio")
Last edited just now


