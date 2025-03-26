# database/seed_data.py
from sqlalchemy.orm import Session
from .db_connect import get_session, init_db
from .models import Cohort, Marker, MarkerData, CellTypeData, Timepoint
import numpy as np

def seed_cohorts(session: Session):
    """Seed the cohorts table with initial data"""
    cohorts = [
        # Cancer cohorts
        Cohort(id=1, indication="Melanoma", type="Cancer", num_specimens=76, num_patients=34, 
               analyzed_specimens=76, treatment="Anti-PD-1 (Pembrolizumab)"),
        Cohort(id=2, indication="UC and Bladder", type="Cancer", num_specimens=204, num_patients=79, 
               analyzed_specimens=204, treatment="Anti-PD-L1 (Atezolizumab)"),
        Cohort(id=3, indication="Melanoma", type="Cancer", num_specimens=468, num_patients=257, 
               analyzed_specimens=460, treatment="Anti-PD-1 + Anti-CTLA-4 Combo"),
        Cohort(id=4, indication="Melanoma", type="Cancer", num_specimens=386, num_patients=142, 
               analyzed_specimens=239, treatment="Anti-PD-1 (Nivolumab)"),
        Cohort(id=5, indication="NSCLC", type="Cancer", num_specimens=35, num_patients=12, 
               analyzed_specimens=35, treatment="Anti-PD-1 (Pembrolizumab)"),
        Cohort(id=6, indication="Melanoma", type="Cancer", num_specimens=501, num_patients=132, 
               analyzed_specimens=501, treatment="TIL Therapy"),
        
        # Autoimmune disease cohorts
        Cohort(id=7, indication="SLE", type="Autoimmune", num_specimens=127, num_patients=56, 
               analyzed_specimens=127, treatment="Standard of Care"),
        Cohort(id=8, indication="Rheumatoid Arthritis", type="Autoimmune", num_specimens=185, num_patients=80, 
               analyzed_specimens=183, treatment="JAK Inhibitor"),
        Cohort(id=9, indication="Lupus", type="Autoimmune", num_specimens=206, num_patients=89, 
               analyzed_specimens=202, treatment="B Cell Depletion Therapy"),
        Cohort(id=10, indication="Type 1 Diabetes", type="Autoimmune", num_specimens=94, num_patients=40, 
               analyzed_specimens=91, treatment="Experimental Immunotherapy"),
        Cohort(id=11, indication="Multiple Sclerosis", type="Autoimmune", num_specimens=152, num_patients=67, 
               analyzed_specimens=148, treatment="Anti-CD20 Therapy"),
        Cohort(id=12, indication="Crohn's Disease", type="Autoimmune", num_specimens=178, num_patients=74, 
               analyzed_specimens=172, treatment="Anti-TNF Therapy")
    ]
    
    session.add_all(cohorts)
    session.commit()
    print(f"Added {len(cohorts)} cohorts to the database")

def seed_markers(session: Session):
    """Seed the markers table with Super Panel v5 proteins"""
    
    # Define marker categories for organization
    marker_categories = {
        "T Cell Markers": ["CD3", "CD4", "CD8a", "CD27", "CD28", "CD45RA", "CD127", "Foxp3", "CD25", "gdTCR"],
        "Activation Markers": ["CD69", "CD95", "Ki67", "ICOS", "CD38", "HLA-DR"],
        "Checkpoint Molecules": ["PD-1", "PD-L1", "CTLA-4", "TIM3", "LAG-3", "TIGIT"],
        "NK Cell Markers": ["CD56", "CD16", "CD57", "KLRG-1"],
        "Myeloid Cell Markers": ["CD11b", "CD11c", "CD14", "CD33", "CD66b", "CD86", "CD123", "LOX-1", "CD15"],
        "B Cell Markers": ["CD19", "CD74", "IgG4"],
        "Other Markers": ["CD45", "CD161", "CD39", "GranzymeB", "Tbet", "CCR7"]
    }
    
    # Marker descriptions
    marker_info = {
        "CD45": "Common leukocyte antigen, expressed on all hematopoietic cells except mature erythrocytes and platelets.",
        "CD8a": "Co-receptor for MHC Class I-restricted T cell activation, primarily on cytotoxic T cells.",
        "CD33": "Sialic acid-binding immunoglobulin-like lectin expressed on myeloid cells and some lymphoid cells.",
        "HLA-DR": "MHC Class II cell surface receptor, important for antigen presentation to CD4+ T cells.",
        "CD66b": "Granulocyte activation marker, primarily expressed on neutrophils.",
        "CD57": "Marker associated with terminally differentiated or senescent NK and T cells.",
        "KLRG-1": "Killer cell lectin-like receptor G1, indicates terminally differentiated T cells and NK cells.",
        "CD3": "T cell co-receptor, part of the T cell receptor complex essential for T cell activation.",
        "CD19": "B cell co-receptor, important for B cell development and activation.",
        "CD69": "Early activation marker expressed on activated lymphocytes and NK cells.",
        "GranzymeB": "Serine protease released by cytotoxic T cells and NK cells, mediates apoptosis in target cells.",
        "CD4": "Co-receptor for MHC Class II-restricted T cell activation, primarily on helper T cells.",
        "CD11b": "Integrin alpha M, expressed on myeloid cells, mediates leukocyte adhesion and migration.",
        "CD11c": "Integrin alpha X, highly expressed on dendritic cells and some myeloid populations.",
        "CD14": "Co-receptor for bacterial lipopolysaccharide detection, primarily on monocytes and macrophages.",
        "TIGIT": "T cell immunoreceptor with Ig and ITIM domains, inhibitory checkpoint on T cells and NK cells.",
        "CD86": "Co-stimulatory molecule on antigen-presenting cells, binds CD28 for T cell activation.",
        "CD123": "IL-3 receptor alpha chain, expressed on basophils, plasmacytoid DCs, and some leukemic cells.",
        "gdTCR": "Gamma delta T cell receptor, defines a subset of T cells with distinct antigen recognition.",
        "CD45RA": "Isoform of CD45, expressed on naive T cells and terminally differentiated effector cells.",
        "TIM3": "T cell immunoglobulin and mucin domain-3, inhibitory receptor associated with T cell exhaustion.",
        "CD95": "Fas receptor, mediates apoptosis upon binding to Fas ligand.",
        "PD-L1": "Programmed death-ligand 1, binds to PD-1 to inhibit T cell activity, often upregulated in tumors.",
        "CCR7": "Chemokine receptor important for lymphocyte trafficking to lymph nodes, marks central memory T cells.",
        "CD27": "Co-stimulatory protein of the TNF-receptor superfamily, important for T and B cell activation.",
        "CD39": "Ectonucleotidase that degrades ATP, often expressed on regulatory T cells and activated T cells.",
        "Tbet": "T-box transcription factor, master regulator of Th1 cell development and function.",
        "CTLA-4": "Cytotoxic T-lymphocyte-associated protein 4, inhibitory checkpoint that downregulates T cell activation.",
        "Foxp3": "Transcription factor essential for regulatory T cell development and function.",
        "CD28": "Co-stimulatory receptor on T cells that binds CD80/CD86 for T cell activation.",
        "CD161": "C-type lectin receptor, expressed on NK cells and subsets of T cells including Th17 cells.",
        "CD127": "IL-7 receptor alpha chain, important for T cell development and homeostasis.",
        "CD74": "MHC Class II invariant chain, involved in antigen presentation and cell signaling.",
        "CD25": "IL-2 receptor alpha chain, upregulated on activated T cells and constitutively expressed on Tregs.",
        "Ki67": "Nuclear protein associated with cellular proliferation, marks actively dividing cells.",
        "ICOS": "Inducible T cell co-stimulator, important for T cell activation and effector function.",
        "LOX-1": "Lectin-like oxidized LDL receptor 1, expressed on endothelial cells, macrophages, and dendritic cells.",
        "CD15": "Lewis X carbohydrate adhesion molecule, expressed on neutrophils and some myeloid cells.",
        "CD38": "Cyclic ADP ribose hydrolase, expressed on activated lymphocytes and plasma cells.",
        "IgG4": "Immunoglobulin G subclass 4, associated with tolerance in chronic antigen exposure.",
        "PD-1": "Programmed cell death protein 1, inhibitory checkpoint receptor expressed on activated T cells.",
        "LAG-3": "Lymphocyte-activation gene 3, inhibitory receptor that binds MHC class II molecules.",
        "CD56": "Neural cell adhesion molecule, expressed on NK cells and some T cell subsets.",
        "CD16": "Fc gamma receptor III, mediates antibody-dependent cellular cytotoxicity, primarily on NK cells."
    }

    markers = []
    marker_id = 1
    
    # Create marker objects
    for category, marker_names in marker_categories.items():
        for name in marker_names:
            markers.append(
                Marker(
                    id=marker_id,
                    name=name,
                    category=category,
                    description=marker_info.get(name, "")
                )
            )
            marker_id += 1
    
    session.add_all(markers)
    session.commit()
    print(f"Added {len(markers)} markers to the database")

def seed_timepoints(session: Session):
    """Seed the timepoints table with initial data"""
    timepoints = [
        Timepoint(id=1, name="Baseline", order=1),
        Timepoint(id=2, name="Day 1", order=2),
        Timepoint(id=3, name="Day 14", order=3),
        Timepoint(id=4, name="Day 28", order=4),
        Timepoint(id=5, name="Day 42", order=5)
    ]
    
    session.add_all(timepoints)
    session.commit()
    print(f"Added {len(timepoints)} timepoints to the database")

def seed_marker_data(session: Session):
    """Seed sample marker data for each cohort"""
    # Get all cohorts and markers
    cohorts = session.query(Cohort).all()
    markers = session.query(Marker).all()
    
    # Get timepoints properly as model objects
    timepoints = session.query(Timepoint).order_by(Timepoint.order).all()
    
    marker_data_objects = []
    data_id = 1
    
    # Define the timepoint names (for the rest of your logic)
    timepoint_names = ["Baseline", "Day 1", "Day 14", "Day 28", "Day 42"]
    
    for cohort in cohorts:
        for marker in markers:
            # Set baseline values depending on the marker category
            if marker.category == "Checkpoint Molecules":
                # Checkpoint molecules often start high in non-responders
                responder_baseline = np.random.uniform(0.3, 0.5)
                nonresponder_baseline = np.random.uniform(0.4, 0.6)
                # Responders often show decreasing checkpoint expression
                responder_direction = -1
                nonresponder_direction = 1
            elif marker.category == "Activation Markers":
                # Activation markers often start low and increase in responders
                responder_baseline = np.random.uniform(0.1, 0.3)
                nonresponder_baseline = np.random.uniform(0.1, 0.3)
                # Responders often show increasing activation marker expression
                responder_direction = 1
                nonresponder_direction = -0.2
            elif marker.category == "T Cell Markers":
                # T cell markers might show varied patterns
                responder_baseline = np.random.uniform(0.2, 0.4)
                nonresponder_baseline = np.random.uniform(0.2, 0.4)
                responder_direction = 0.5
                nonresponder_direction = -0.2
            else:
                # Default pattern for other markers
                responder_baseline = np.random.uniform(0.2, 0.4)
                nonresponder_baseline = responder_baseline
                responder_direction = np.random.choice([-1, 1])
                nonresponder_direction = responder_direction * np.random.uniform(-0.5, 0.5)
            
            # Create the time series data
            responder_values = [responder_baseline]
            nonresponder_values = [nonresponder_baseline]
            
            # Generate values for each timepoint
            for i in range(1, len(timepoint_names)):
                # More pronounced changes in later timepoints
                time_factor = i / len(timepoint_names)
                
                # Generate next value with some randomness
                next_responder = responder_values[-1] + responder_direction * np.random.uniform(0.05, 0.15) * time_factor
                next_nonresponder = nonresponder_values[-1] + nonresponder_direction * np.random.uniform(0.02, 0.08) * time_factor
                
                # Add some noise
                next_responder += np.random.uniform(-0.02, 0.02)
                next_nonresponder += np.random.uniform(-0.02, 0.02)
                
                # Ensure values stay within reasonable range
                responder_values.append(max(0.01, min(0.99, next_responder)))
                nonresponder_values.append(max(0.01, min(0.99, next_nonresponder)))
            
            # Add data for each timepoint
            for i, timepoint in enumerate(timepoints):
                if i < len(responder_values):  # Make sure we have enough values
                    marker_data_objects.append(
                        MarkerData(
                            id=data_id,
                            cohort_id=cohort.id,
                            marker_id=marker.id,
                            timepoint_id=timepoint.id,  # Use timepoint.id, not timepoint as a string
                            responder_value=responder_values[i],
                            nonresponder_value=nonresponder_values[i]
                        )
                    )
                    data_id += 1

def seed_cell_type_data(session: Session):
    """Seed cell type frequency data for each cohort"""
    # Define cell types
    cell_types = [
        "CD8+ T Cells", "CD4+ T Cells", "Regulatory T Cells", 
        "NK Cells", "B Cells", "Monocytes", "Dendritic Cells", 
        "Neutrophils", "MDSC"
    ]
    
    # Disease-specific cell type patterns
    cell_type_patterns = {
        "Melanoma": {
            "Responders": [0.25, 0.30, 0.06, 0.12, 0.10, 0.08, 0.04, 0.03, 0.02],
            "Non-Responders": [0.15, 0.25, 0.10, 0.08, 0.12, 0.12, 0.03, 0.07, 0.08]
        },
        "NSCLC": {
            "Responders": [0.22, 0.28, 0.05, 0.15, 0.12, 0.07, 0.05, 0.04, 0.02],
            "Non-Responders": [0.12, 0.22, 0.09, 0.10, 0.14, 0.13, 0.04, 0.08, 0.08]
        },
        "UC and Bladder": {
            "Responders": [0.24, 0.26, 0.04, 0.14, 0.13, 0.08, 0.05, 0.04, 0.02],
            "Non-Responders": [0.14, 0.20, 0.11, 0.09, 0.15, 0.11, 0.04, 0.07, 0.09]
        },
        "SLE": {
            "Responders": [0.18, 0.32, 0.12, 0.08, 0.15, 0.05, 0.05, 0.03, 0.02],
            "Non-Responders": [0.15, 0.25, 0.14, 0.07, 0.18, 0.06, 0.04, 0.06, 0.05]
        },
        "Rheumatoid Arthritis": {
            "Responders": [0.16, 0.30, 0.10, 0.09, 0.16, 0.08, 0.04, 0.05, 0.02],
            "Non-Responders": [0.12, 0.24, 0.12, 0.08, 0.20, 0.09, 0.03, 0.07, 0.05]
        },
        "Lupus": {
            "Responders": [0.17, 0.31, 0.11, 0.08, 0.17, 0.06, 0.04, 0.04, 0.02],
            "Non-Responders": [0.14, 0.26, 0.13, 0.07, 0.19, 0.07, 0.03, 0.06, 0.05]
        },
        "Type 1 Diabetes": {
            "Responders": [0.19, 0.29, 0.09, 0.10, 0.15, 0.07, 0.05, 0.04, 0.02],
            "Non-Responders": [0.15, 0.24, 0.11, 0.08, 0.17, 0.08, 0.04, 0.06, 0.07]
        },
        "Multiple Sclerosis": {
            "Responders": [0.20, 0.30, 0.08, 0.09, 0.14, 0.08, 0.05, 0.04, 0.02],
            "Non-Responders": [0.16, 0.25, 0.12, 0.07, 0.16, 0.09, 0.04, 0.05, 0.06]
        },
        "Crohn's Disease": {
            "Responders": [0.18, 0.28, 0.07, 0.10, 0.16, 0.09, 0.05, 0.05, 0.02],
            "Non-Responders": [0.14, 0.24, 0.11, 0.08, 0.18, 0.10, 0.04, 0.06, 0.05]
        }
    }
    
    cell_type_objects = []
    data_id = 1
    
    # Get all cohorts
    cohorts = session.query(Cohort).all()
    
    for cohort in cohorts:
        # Use default if the indication is not in the patterns
        if cohort.indication not in cell_type_patterns:
            selected_pattern = cell_type_patterns["Melanoma"]
        else:
            selected_pattern = cell_type_patterns[cohort.indication]
        
        # Add some noise to make it look realistic for this specific cohort
        responder_freqs = [max(0.01, min(0.99, val + np.random.uniform(-0.02, 0.02))) 
                          for val in selected_pattern["Responders"]]
        nonresponder_freqs = [max(0.01, min(0.99, val + np.random.uniform(-0.02, 0.02))) 
                             for val in selected_pattern["Non-Responders"]]
        
        # Create cell type data objects
        for i, cell_type in enumerate(cell_types):
            cell_type_objects.append(
                CellTypeData(
                    id=data_id,
                    cohort_id=cohort.id,
                    cell_type=cell_type,
                    responder_frequency=responder_freqs[i],
                    nonresponder_frequency=nonresponder_freqs[i]
                )
            )
            data_id += 1
    
    session.add_all(cell_type_objects)
    session.commit()
    print(f"Added {len(cell_type_objects)} cell type data points to the database")

def seed_database():
    """Main function to seed the entire database"""
    print("Initializing database...")
    init_db()
    
    session = get_session()
    try:
        print("Seeding database...")
        seed_cohorts(session)
        seed_markers(session)
        seed_timepoints(session)
        seed_marker_data(session)
        seed_cell_type_data(session)
        print("Database seeding completed successfully!")
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()