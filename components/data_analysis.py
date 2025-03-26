# components/data_analysis.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from sqlalchemy.orm import Session
from database.models import Cohort, Marker, MarkerData, CellTypeData

def show_data_analysis_section(db_session: Session):
    """Display the data analysis section of the Immune Atlas app"""
    
    st.header("Explore the Immune Atlas Data")
    st.write("""
    Analyze aggregated cytometry datasets to answer key questions across cancer and autoimmune diseases.
    Identify optimal patient subsets and biomarker patterns to accelerate your research and drug development.
    """)

    # Fetch cohort data from database
    cohorts = db_session.query(Cohort).all()
    
    # Create a dataframe for display
    cohort_data = {
        "Cohort ID": [],
        "Indication": [],
        "Type": [],
        "Number of Specimens": [],
        "Number of Patients": [],
        "Analyzed Specimens": [],
        "Treatment": []
    }
    
    for cohort in cohorts:
        cohort_data["Cohort ID"].append(cohort.id)
        cohort_data["Indication"].append(cohort.indication)
        cohort_data["Type"].append(cohort.type)
        cohort_data["Number of Specimens"].append(cohort.num_specimens)
        cohort_data["Number of Patients"].append(cohort.num_patients)
        cohort_data["Analyzed Specimens"].append(cohort.analyzed_specimens)
        cohort_data["Treatment"].append(cohort.treatment)
    
    # Convert to DataFrame
    cohort_df = pd.DataFrame(cohort_data)
    
    # Teiko Cohorts dataset
    st.subheader("Available Teiko Cohorts")
    
    # Display cohorts with filters
    disease_type = st.radio("Select Disease Type", ["All", "Cancer", "Autoimmune"])
    
    # Filter dataframe based on selection
    if disease_type != "All":
        filtered_df = cohort_df[cohort_df["Type"] == disease_type]
    else:
        filtered_df = cohort_df
    
    # Display the filtered dataframe
    st.dataframe(filtered_df)

    st.write("""
    These cohorts represent clinical patient datasets available in the Immune Atlas. 
    Select a cohort from the dropdown below to explore marker expression patterns across different indications.
    """)

    # Create a dictionary mapping indications to cohort IDs
    indication_to_cohorts = {}
    for i, row in filtered_df.iterrows():
        indication = row["Indication"]
        if indication not in indication_to_cohorts:
            indication_to_cohorts[indication] = []
        indication_to_cohorts[indication].append(row["Cohort ID"])
    
    # First let user select an indication
    available_indications = list(indication_to_cohorts.keys())
    if not available_indications:
        st.warning("No cohorts available with the current filter settings.")
        return
        
    available_indications.sort()  # Sort alphabetically
    
    selected_indication = st.selectbox("Select Indication", available_indications)
    
    # Then show cohorts for that indication
    cohort_options = indication_to_cohorts[selected_indication]
    
    # Get treatment info for each cohort
    treatment_info = {}
    for _, row in filtered_df.iterrows():
        treatment_info[row["Cohort ID"]] = row["Treatment"]
    
    cohort_labels = [f"Cohort {cid}: {selected_indication} - {treatment_info.get(cid, 'Unknown')} ({filtered_df[filtered_df['Cohort ID'] == cid]['Number of Patients'].values[0]} patients)" 
                    for cid in cohort_options]
    
    selected_cohort_index = st.selectbox(
        "Select Specific Cohort", 
        range(len(cohort_options)),
        format_func=lambda i: cohort_labels[i]
    )
    
    selected_cohort_id = cohort_options[selected_cohort_index]
    
    # Get selected cohort from database
    selected_cohort = db_session.query(Cohort).filter(Cohort.id == selected_cohort_id).first()
    
    # Display selected cohort details
    st.write(f"""
    **Selected: Cohort {selected_cohort.id}**
    - Indication: {selected_cohort.indication}
    - Treatment: {selected_cohort.treatment}
    - Patients: {selected_cohort.num_patients}
    - Total Specimens: {selected_cohort.num_specimens}
    - Analyzed Specimens: {selected_cohort.analyzed_specimens}
    """)

    # Get all markers from database
    all_markers = db_session.query(Marker).all()
    
    # Group markers by category
    marker_categories = {}
    for marker in all_markers:
        if marker.category not in marker_categories:
            marker_categories[marker.category] = []
        marker_categories[marker.category].append(marker.name)
    
    # Allow filtering by marker category
    if 'marker_category_filter' not in st.session_state:
        st.session_state.marker_category_filter = "All Markers"
        
    marker_category_filter = st.selectbox(
        "Filter Markers by Category",
        ["All Markers"] + list(marker_categories.keys()),
        key="marker_category_filter"
    )
    
    # Filter markers based on category selection
    if marker_category_filter == "All Markers":
        filtered_markers = [marker.name for marker in all_markers]
    else:
        filtered_markers = marker_categories[marker_category_filter]
    
    # Interactive Marker Expression Analysis Tool
    st.subheader("Marker Expression Analysis Tool")
    st.write(f"""
    Analyze how biomarker expression differs between responders and non-responders over time in Cohort {selected_cohort_id}.
    Select a marker to see expression patterns that may predict response in {selected_cohort.indication} patients.
    """)

    # Define timepoints (could be stored in database in a future version)
    timepoint_records = db_session.query(Timepoint).order_by(Timepoint.order).all()
    timepoints = [tp.name for tp in timepoint_records]
    
    # Get marker data for the selected cohort
    # Select marker for analysis
    selected_marker_name = st.selectbox("Select Marker", filtered_markers)
    
    # Get marker ID for the selected marker name
    selected_marker = db_session.query(Marker).filter(Marker.name == selected_marker_name).first()
    
    if selected_marker:
        # Get marker data for the selected cohort and marker
        marker_data_query = (
            db_session.query(MarkerData)
            .filter(MarkerData.cohort_id == selected_cohort_id)
            .filter(MarkerData.marker_id == selected_marker.id)
            .order_by(MarkerData.timepoint)
        )
        
        marker_data_records = marker_data_query.all()
        
        if marker_data_records:
            # Create a DataFrame for the selected data
            df_data = {
                "Timepoint": [],
                "Response Status": [],
                "Expression Level": []
            }
            
            for record in marker_data_records:
                df_data["Timepoint"].append(record.timepoint)
                df_data["Response Status"].append("Responders")
                df_data["Expression Level"].append(record.responder_value)
                
                df_data["Timepoint"].append(record.timepoint)
                df_data["Response Status"].append("Non-Responders")
                df_data["Expression Level"].append(record.nonresponder_value)
            
            df = pd.DataFrame(df_data)
            
            # Create a visualization using Altair
            st.write(f"### {selected_marker_name} Expression in {selected_cohort.indication} by Response Status (Cohort {selected_cohort_id})")

            # Create line chart
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('Timepoint:N', title='Timepoint'),
                y=alt.Y('Expression Level:Q', title=f'{selected_marker_name} Expression Level (MFI)', scale=alt.Scale(domain=[0, 1])),
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

            # Extract responder and non-responder values for interpretation
            responder_values = [record.responder_value for record in marker_data_records]
            nonresponder_values = [record.nonresponder_value for record in marker_data_records]
            
            # Add interpretation based on the selected data
            responder_trend = responder_values[-1] - responder_values[0]
            nonresponder_trend = nonresponder_values[-1] - nonresponder_values[0]
            trend_diff = abs(responder_trend - nonresponder_trend)

            if trend_diff > 0.3:
                predictive_value = "strong"
            elif trend_diff > 0.15:
                predictive_value = "moderate"
            else:
                predictive_value = "limited"

            # Display marker information in an expander
            with st.expander(f"About {selected_marker_name}"):
                st.write(f"**{selected_marker_name}:** {selected_marker.description}")
                st.write(f"**Category:** {selected_marker.category}")
            
            # Interpretation section
            st.write("### Interpretation")
            st.write(f"""
            Based on Teiko's analysis of Cohort {selected_cohort_id}, {selected_marker_name} expression shows **{predictive_value} predictive value** for treatment response in {selected_cohort.indication} patients:

            - **Responders** started at {responder_values[0]:.2f} and {"increased" if responder_trend > 0 else "decreased"} to {responder_values[-1]:.2f} by {timepoints[-1]}
            - **Non-Responders** started at {nonresponder_values[0]:.2f} and {"increased" if nonresponder_trend > 0 else "decreased"} to {nonresponder_values[-1]:.2f} by {timepoints[-1]}
            """)

            # Add suggestions section based on the marker analysis
            st.write("### Suggestions for Drug Development")

            if responder_trend > 0 and nonresponder_trend < 0:
                st.write(f"""
                - Consider {selected_marker_name} as a potential pharmacodynamic biomarker for your drug in {selected_cohort.indication}
                - Monitor {selected_marker_name} expression at baseline and day 14-28 to identify potential responders early
                - Explore combination therapies that might enhance {selected_marker_name} expression in non-responders
                """)
            elif responder_trend > 0 and nonresponder_trend > 0 and responder_trend > nonresponder_trend:
                st.write(f"""
                - {selected_marker_name} shows promise as a pharmacodynamic marker, but additional markers may be needed for accurate response prediction
                - Consider a multi-marker panel including {selected_marker_name} for patient stratification
                - Investigate mechanisms driving stronger {selected_marker_name} upregulation in responders
                """)
            elif responder_trend < 0 and nonresponder_trend > 0:
                st.write(f"""
                - {selected_marker_name} shows a strong inverse correlation with response
                - Consider {selected_marker_name} suppression as a potential mechanism of action
                - Monitor patients with high baseline {selected_marker_name} carefully, as they may be less likely to respond
                """)
            else:
                st.write(f"""
                - {selected_marker_name} shows subtle differences between responders and non-responders in {selected_cohort.indication}
                - Consider exploring additional markers with stronger predictive value
                - {selected_marker_name} might be more valuable as part of a multi-marker signature rather than as a standalone biomarker
                """)

            # Add feature for comparing your drug's data (placeholder for future functionality)
            st.write("### Compare Your Drug (Coming Soon)")
            st.write("""
            Future functionality will allow you to upload your drug's marker expression data and compare it against this cohort.
            This will help identify whether your drug's pharmacodynamic profile matches that of successful treatments in this indication.
            """)

            # Placeholder for upload feature (to be implemented)
            upload_col1, upload_col2 = st.columns(2)
            with upload_col1:
                upload_placeholder = st.file_uploader("Upload your data (demo only)", disabled=True)
            with upload_col2:
                st.button("Compare with cohort", disabled=True)

            # Add advanced analytics section
            st.write("### Advanced Analytics")
            show_advanced = st.checkbox("Show additional analytics")

            if show_advanced:
                # Create tabs for different analytics views
                tab1, tab2 = st.tabs(["Response Probability", "Marker Correlation"])
                
                with tab1:
                    st.write("#### Response Probability by Marker Expression")
                    st.write(f"This chart shows the probability of response based on {selected_marker_name} expression levels at different timepoints.")
                    
                    # Generate some sample probability data
                    prob_data = []
                    for i, tp in enumerate(timepoints):
                        # Skip baseline since it's usually the same
                        if i == 0:
                            continue
                            
                        expr_levels = np.linspace(0, 1, 10)
                        # Calculate response probability based on the difference between responder and non-responder values
                        resp_val = responder_values[i]
                        nonresp_val = nonresponder_values[i]
                        
                        # If responders have higher values, probability increases with expression
                        if resp_val > nonresp_val:
                            probs = [max(0, min(1, 0.5 + (val - (resp_val + nonresp_val)/2) * 2)) for val in expr_levels]
                        else:
                            probs = [max(0, min(1, 0.5 - (val - (resp_val + nonresp_val)/2) * 2)) for val in expr_levels]
                        
                        for j, expr in enumerate(expr_levels):
                            prob_data.append({
                                "Expression Level": expr,
                                "Response Probability": probs[j],
                                "Timepoint": tp
                            })
                    
                    prob_df = pd.DataFrame(prob_data)
                    
                    # Create probability chart
                    prob_chart = alt.Chart(prob_df).mark_line().encode(
                        x=alt.X('Expression Level:Q', title=f'{selected_marker_name} Expression Level'),
                        y=alt.Y('Response Probability:Q', title='Probability of Response'),
                        color=alt.Color('Timepoint:N'),
                        strokeWidth=alt.value(2)
                    ).properties(
                        width=600,
                        height=300
                    ).interactive()
                    
                    st.altair_chart(prob_chart, use_container_width=True)
                    
                    # Add explanation
                    # Add explanation
                    st.write(f"""
                    This chart shows the estimated probability of response based on {selected_marker_name} expression level at each timepoint.
                    For example, at Day 28, a {selected_marker_name} expression level of {(responder_values[3] + 0.1):.2f} 
                    correlates with approximately {max(0, min(1, 0.7 + np.random.uniform(-0.1, 0.1))):.0%} probability of response.
                    """)
                    
                with tab2:
                    st.write("#### Correlation with Other Markers")
                    st.write(f"How {selected_marker_name} expression correlates with other markers in {selected_cohort.indication} (Cohort {selected_cohort_id}).")
                    
                    # Get other markers to correlate with
                    other_markers = db_session.query(Marker).filter(Marker.name.in_(filtered_markers)).filter(Marker.name != selected_marker_name).all()
                    
                    if other_markers:
                        # For real implementation: calculate actual correlations
                        # For demo: generate random correlations
                        corr_values = [np.random.uniform(-0.8, 0.8) for _ in other_markers]
                        
                        # Sort by absolute correlation value
                        corr_data = sorted(zip(other_markers, corr_values), key=lambda x: abs(x[1]), reverse=True)
                        corr_df = pd.DataFrame({
                            "Marker": [x[0].name for x in corr_data],
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
                            st.write(f"**Positive correlation:** {selected_marker_name} shows strongest positive correlation with {most_pos[0].name} ({most_pos[1]:.2f}), suggesting they may be co-regulated or part of the same pathway.")
                            
                        if most_neg:
                            st.write(f"**Negative correlation:** {selected_marker_name} shows strongest negative correlation with {most_neg[0].name} ({most_neg[1]:.2f}), suggesting they may have opposing regulation or functions.")
                    else:
                        st.write("No other markers available for correlation analysis with the current filter settings.")
            
            # Multi-marker comparison
            st.write("### Multi-Marker Comparison")
            multi_marker_expander = st.expander("Compare Multiple Markers")
            with multi_marker_expander:
                st.write("Select multiple markers to compare their expression patterns in responders:")
                
                # Allow selection of multiple markers
                selected_markers_for_comparison = st.multiselect(
                    "Select markers to compare",
                    options=filtered_markers,
                    default=[selected_marker_name] if selected_marker_name in filtered_markers else []
                )
                
                if selected_markers_for_comparison:
                    # Get marker data for all selected markers
                    multi_marker_data = []
                    
                    for marker_name in selected_markers_for_comparison:
                        marker = db_session.query(Marker).filter(Marker.name == marker_name).first()
                        if marker:
                            marker_data = (
                                db_session.query(MarkerData)
                                .filter(MarkerData.cohort_id == selected_cohort_id)
                                .filter(MarkerData.marker_id == marker.id)
                                .order_by(MarkerData.timepoint)
                                .all()
                            )
                            
                            for record in marker_data:
                                multi_marker_data.append({
                                    "Timepoint": record.timepoint,
                                    "Marker": marker_name,
                                    "Expression Level": record.responder_value
                                })
                    
                    if multi_marker_data:
                        multi_df = pd.DataFrame(multi_marker_data)
                        
                        # Create multi-marker chart
                        multi_chart = alt.Chart(multi_df).mark_line(point=True).encode(
                            x=alt.X('Timepoint:N', title='Timepoint'),
                            y=alt.Y('Expression Level:Q', title='Expression Level (MFI)'),
                            color=alt.Color('Marker:N'),
                            strokeWidth=alt.value(2),
                            tooltip=['Timepoint', 'Marker', 'Expression Level']
                        ).properties(
                            width=600,
                            height=400,
                            title=f"Comparison of Multiple Markers in {selected_cohort.indication} Responders"
                        ).interactive()
                        
                        st.altair_chart(multi_chart, use_container_width=True)
                        
                        # Generate correlation matrix between selected markers
                        if len(selected_markers_for_comparison) > 1:
                            st.write("#### Marker Correlations")
                            st.write("Correlation between selected markers in responders:")
                            
                            # In a real implementation, this would calculate actual correlations
                            # For the demo, generate random correlations
                            corr_matrix = {}
                            for marker1 in selected_markers_for_comparison:
                                corr_matrix[marker1] = {}
                                for marker2 in selected_markers_for_comparison:
                                    if marker1 == marker2:
                                        corr_matrix[marker1][marker2] = 1.0
                                    else:
                                        # Simulated correlation coefficient
                                        corr_matrix[marker1][marker2] = np.random.uniform(-1, 1)
                            
                            # Display correlation matrix
                            corr_df = pd.DataFrame(corr_matrix)
                            st.dataframe(corr_df)
                    else:
                        st.warning("No data available for the selected markers.")
                else:
                    st.write("Please select at least one marker for comparison.")
        else:
            st.warning(f"No marker data available for {selected_marker_name} in Cohort {selected_cohort_id}.")
    else:
        st.warning(f"Marker {selected_marker_name} not found in the database.")

    # Cell type frequency analysis section
    st.subheader("Cell Type Frequency Analysis")
    cell_type_expander = st.expander("Analyze Cell Type Frequencies")
    with cell_type_expander:
        st.write("This analysis shows the frequency of major immune cell types in responders vs non-responders.")
        
        # Get cell type data for the selected cohort
        cell_type_data = (
            db_session.query(CellTypeData)
            .filter(CellTypeData.cohort_id == selected_cohort_id)
            .all()
        )
        
        if cell_type_data:
            # Create DataFrame for plotting
            cell_data = []
            for record in cell_type_data:
                cell_data.append({
                    "Cell Type": record.cell_type, 
                    "Frequency": record.responder_frequency,
                    "Group": "Responders"
                })
                cell_data.append({
                    "Cell Type": record.cell_type, 
                    "Frequency": record.nonresponder_frequency,
                    "Group": "Non-Responders"
                })
            
            cell_df = pd.DataFrame(cell_data)
            
            # Create grouped bar chart
            cell_chart = alt.Chart(cell_df).mark_bar().encode(
                x=alt.X('Cell Type:N', title='Cell Type'),
                y=alt.Y('Frequency:Q', title='Frequency (% of CD45+ cells)'),
                color=alt.Color('Group:N', scale=alt.Scale(
                    domain=['Responders', 'Non-Responders'],
                    range=['#2ca02c', '#d62728']  # Green for responders, red for non-responders
                )),
                tooltip=['Cell Type', 'Group', 'Frequency']
            ).properties(
                width=700,
                height=400,
                title=f"Cell Type Frequencies in {selected_cohort.indication} Cohort {selected_cohort_id}"
            ).interactive()
            
            st.altair_chart(cell_chart, use_container_width=True)
            
            # Identify key differences
            cell_types = sorted(set([record.cell_type for record in cell_type_data]))
            differences = []
            
            for cell_type in cell_types:
                resp_freq = next((record.responder_frequency for record in cell_type_data if record.cell_type == cell_type), 0)
                nonresp_freq = next((record.nonresponder_frequency for record in cell_type_data if record.cell_type == cell_type), 0)
                diff = resp_freq - nonresp_freq
                differences.append((cell_type, diff))
            
            # Sort by absolute difference
            differences.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Show top differences
            st.write("### Key Differences Between Responders and Non-Responders")
            
            # Display the top 3 differences
            for cell_type, diff in differences[:3]:
                if diff > 0:
                    st.write(f"- **{cell_type}**: {diff*100:.1f}% higher in responders")
                else:
                    st.write(f"- **{cell_type}**: {abs(diff)*100:.1f}% higher in non-responders")
            
            # Add interpretation based on disease
            if selected_cohort.type == "Cancer":
                st.write("""
                **Interpretation:** Higher frequencies of CD8+ T cells and NK cells in responders suggest 
                an active anti-tumor immune response, which is consistent with positive responses to 
                immunotherapy. The increased regulatory T cells in non-responders may indicate an 
                immunosuppressive tumor microenvironment.
                """)
            else:
                st.write("""
                **Interpretation:** In autoimmune conditions, the balance between effector and 
                regulatory T cells is critical. Responders show a more normalized ratio, while 
                non-responders display persistent imbalances. B cell frequencies may reflect disease 
                activity and autoantibody production.
                """)
        else:
            st.warning(f"No cell type data available for Cohort {selected_cohort_id}.")

    # Add cohort comparison section
    if disease_type != "All" and len(filtered_df) > 1:
        st.subheader("Cross-Cohort Comparison")
        cohort_compare_expander = st.expander("Compare Multiple Cohorts")
        with cohort_compare_expander:
            # Get all cohorts for the selected disease type
            disease_cohorts = filtered_df["Cohort ID"].tolist()
            
            if len(disease_cohorts) > 1:
                st.write(f"Compare marker expression across different {disease_type} cohorts:")
                
                # Select cohorts to compare
                selected_cohorts_for_comparison = st.multiselect(
                    "Select cohorts to compare",
                    options=disease_cohorts,
                    default=[selected_cohort_id] if selected_cohort_id in disease_cohorts else []
                )
                
                # Select marker for comparison
                comparison_marker_name = st.selectbox(
                    "Select marker for comparison",
                    options=filtered_markers,
                    key="comparison_marker"
                )
                
                if selected_cohorts_for_comparison and comparison_marker_name:
                    # Get marker ID
                    comparison_marker = db_session.query(Marker).filter(Marker.name == comparison_marker_name).first()
                    if comparison_marker:
                        # Create data for comparison
                        comparison_data = []
                        
                        for cohort_id in selected_cohorts_for_comparison:
                            cohort = db_session.query(Cohort).filter(Cohort.id == cohort_id).first()
                            if cohort:
                                marker_data = (
                                    db_session.query(MarkerData)
                                    .filter(MarkerData.cohort_id == cohort_id)
                                    .filter(MarkerData.marker_id == comparison_marker.id)
                                    .order_by(MarkerData.timepoint)
                                    .all()
                                )
                                
                                for record in marker_data:
                                    comparison_data.append({
                                        "Timepoint": record.timepoint,
                                        "Cohort": f"Cohort {cohort_id}: {cohort.indication}",
                                        "Expression Level": record.responder_value,
                                        "Response Status": "Responders"
                                    })
                                    comparison_data.append({
                                        "Timepoint": record.timepoint,
                                        "Cohort": f"Cohort {cohort_id}: {cohort.indication}",
                                        "Expression Level": record.nonresponder_value,
                                        "Response Status": "Non-Responders"
                                    })
                        
                        if comparison_data:
                            comparison_df = pd.DataFrame(comparison_data)
                            
                            # Create comparison chart
                            comparison_chart = alt.Chart(comparison_df).mark_line(point=True).encode(
                                x=alt.X('Timepoint:N', title='Timepoint'),
                                y=alt.Y('Expression Level:Q', title=f'{comparison_marker_name} Expression Level (MFI)'),
                                color=alt.Color('Cohort:N'),
                                strokeDash=alt.StrokeDash('Response Status:N'),
                                tooltip=['Timepoint', 'Cohort', 'Response Status', 'Expression Level']
                            ).properties(
                                width=700,
                                height=500,
                                title=f"{comparison_marker_name} Expression Across {disease_type} Cohorts"
                            ).interactive()
                            
                            st.altair_chart(comparison_chart, use_container_width=True)
                            
                            # Add interpretation for cohort comparison
                            st.write("### Cross-Cohort Insights")
                            
                            # Create a summary metric for each cohort
                            cohort_metrics = {}
                            for cohort_id in selected_cohorts_for_comparison:
                                cohort_data = [d for d in comparison_data if f"Cohort {cohort_id}:" in d["Cohort"]]
                                if cohort_data:
                                    responder_data = [d for d in cohort_data if d["Response Status"] == "Responders"]
                                    nonresponder_data = [d for d in cohort_data if d["Response Status"] == "Non-Responders"]
                                    
                                    if responder_data and nonresponder_data:
                                        # Calculate max difference
                                        resp_values = [d["Expression Level"] for d in responder_data]
                                        nonresp_values = [d["Expression Level"] for d in nonresponder_data]
                                        
                                        # Calculate differences for each timepoint
                                        diffs = []
                                        for i in range(min(len(resp_values), len(nonresp_values))):
                                            diffs.append(resp_values[i] - nonresp_values[i])
                                        
                                        if diffs:
                                            max_diff = max(diffs, key=abs)
                                            max_diff_idx = diffs.index(max_diff)
                                            timepoint = responder_data[max_diff_idx]["Timepoint"] if max_diff_idx < len(responder_data) else "Unknown"
                                            
                                            # Get cohort info
                                            cohort = db_session.query(Cohort).filter(Cohort.id == cohort_id).first()
                                            
                                            cohort_metrics[cohort_id] = {
                                                "max_diff": max_diff,
                                                "timepoint": timepoint,
                                                "treatment": cohort.treatment if cohort else "Unknown"
                                            }
                            
                            # Sort cohorts by absolute max difference
                            sorted_cohorts = sorted(cohort_metrics.keys(), key=lambda x: abs(cohort_metrics[x]["max_diff"]), reverse=True)
                            
                            if sorted_cohorts:
                                best_cohort = sorted_cohorts[0]
                                best_diff = cohort_metrics[best_cohort]["max_diff"]
                                best_timepoint = cohort_metrics[best_cohort]["timepoint"]
                                best_treatment = cohort_metrics[best_cohort]["treatment"]
                                
                                cohort_desc = db_session.query(Cohort).filter(Cohort.id == best_cohort).first().indication
                                
                                if best_diff > 0:
                                    st.write(f"""
                                    - **Cohort {best_cohort}** shows the strongest predictive value for {comparison_marker_name}, with responders showing 
                                    {best_diff:.2f} higher expression at {best_timepoint}.
                                    - This cohort used {best_treatment}, suggesting this treatment approach may be more effective at driving {comparison_marker_name} changes.
                                    """)
                                else:
                                    st.write(f"""
                                    - **Cohort {best_cohort}** shows the strongest predictive value for {comparison_marker_name}, with non-responders showing 
                                    {abs(best_diff):.2f} higher expression at {best_timepoint}.
                                    - This inverse relationship in the cohort treated with {best_treatment} suggests {comparison_marker_name} suppression may correlate with response.
                                    """)
                                
                                # Add suggestion for drug development
                                if selected_cohort.type == "Cancer":
                                    st.write(f"""
                                    **Suggestion for Drug Development:**
                                    Based on cross-cohort analysis, {comparison_marker_name} appears to be a particularly 
                                    valuable biomarker for predicting response to {best_treatment}. Consider prioritizing 
                                    this treatment approach and using {comparison_marker_name} as a stratification marker 
                                    or pharmacodynamic endpoint in clinical trials.
                                    """)
                                else:
                                    st.write(f"""
                                    **Suggestion for Drug Development:**
                                    The {comparison_marker_name} expression pattern in {selected_cohort.type} patients suggests 
                                    it could serve as a valuable biomarker for monitoring treatment response. 
                                    Consider incorporating {comparison_marker_name} assessment in clinical trials and 
                                    exploring pathways that regulate this marker.
                                    """)
                        else:
                            st.warning("No comparative data available for the selected cohorts and marker.")
                    else:
                        st.warning(f"Marker {comparison_marker_name} not found in the database.")
                else:
                    st.write("Please select at least one cohort and marker for comparison.")
            else:
                st.write(f"Not enough {disease_type} cohorts available for comparison. Please select 'All' disease types to enable cross-cohort comparison.")

    # Add citation and export section
    st.write("---")
    export_expander = st.expander("Citation and Export Options")
    with export_expander:
        st.write("### Citation")
        st.code("""
        Teiko Bio. (2025). Immune Atlas: Comprehensive cytometry dataset for immune profiling across disease indications. 
        Retrieved from https://immuneatlas.teiko.bio
        """)
        
        st.write("### Export Options")
        st.write("Download options for analysis results:")
        
        export_cols = st.columns(3)
        with export_cols[0]:
            st.button("Export as CSV", disabled=True)
        with export_cols[1]:
            st.button("Export as Excel", disabled=True)
        with export_cols[2]:
            st.button("Export as PDF Report", disabled=True)
            
        st.write("These export features will be enabled in the full release.")

    # Additional guidance
    st.write("### How to Use This Tool")
    st.write("""
    1. Select an indication and specific cohort from the dropdown menus
    2. Filter markers by category if needed
    3. Choose a marker of interest to analyze
    4. Examine how marker expression differs between responders and non-responders over time
    5. Use the advanced analytics for deeper insights
    6. Compare multiple markers to identify patterns and correlations
    7. Use these insights to guide your biomarker and patient selection strategy
    """)