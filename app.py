import streamlit as st
import pandas as pd

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
          - Per-Use Fee: $0.10-$1 per access, scaled by dataset complexity and demand.
          - Revenue Share: 5-10% of subscription revenue (e.g., $10,000/year for Atlas access) based on usage proportion.
          - Licensing Bonus: $5,000-$50,000 for high-impact datasets (e.g., cited in drug approvals).
        - **Deidentification Support**: Tools to ensure HIPAA/GDPR compliance.
        - **Attribution**: Optional credit in publications (e.g., "Data provided by XYZ Pharma").
        - **Example**: XYZ Pharma earns $100 from 100 queries ($1 each) + $500 from 5% of a $10,000 subscription, totaling $600 plus potential bonuses.
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
        - **Example**: Stanford earns $120,000 for 40% of 250 queries from a $300,000 pool.
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

    # Example analysis
    st.subheader("Example Analysis")
    st.write("""
    Compare your drug's pharmacodynamic profile (e.g., CD69 median channel value) against the average of publicly available datasets. Identify cancer types or patient subsets where your drug outperforms.
    """)
    st.write("For instance, your drug might outperform the average in NSCLC, Melanoma, and Bladder Cancer but not in Colorectal Cancer.")

    # Placeholder for visualization
    st.write("Visualize Response Rates:")
    response_data = pd.DataFrame({
        "Cancer Type": ["NSCLC", "Melanoma", "Bladder Cancer", "Colorectal Cancer"],
        "Response Rate": [33.33, 33.33, 33.33, 33.33]  # Simplified for demo
    })
    st.bar_chart(response_data.set_index("Cancer Type"))

# Footer
st.write("---")
st.write("Contact us to learn more or start contributing: info@teiko.bio")