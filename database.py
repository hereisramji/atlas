# database.py

import numpy as np
import pandas as pd
import os
import tempfile
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import init_db, get_session, Cohort, Patient, Specimen, CellPopulation, Cell, CellMarker

class DatabaseManager:
    """Manager for database operations using SQLAlchemy models."""
    
    def __init__(self, db_url=None):
        """Initialize database connection and ensure tables exist."""
        if db_url is None:
            # Try to use a temp directory for Streamlit Cloud
            try:
                # First, try to use a directory that we know should be writable in most environments
                temp_dir = tempfile.gettempdir()
                db_path = os.path.join(temp_dir, "immune_atlas.db")
                print(f"Using database path: {db_path}")
                db_url = f"sqlite:///{db_path}"
            except Exception as e:
                # Fallback to current directory
                print(f"Error using temp directory: {str(e)}")
                db_url = "sqlite:///immune_atlas.db"
        
        self.engine = init_db(db_url)
        self.session = get_session(self.engine)
        print(f"Database initialized with connection: {db_url}")
    
    def load_sample_data(self):
        """Load sample data if the database is empty."""
        # Check if cohorts table is empty
        count_query = text("SELECT COUNT(*) FROM cohorts")
        try:
            cohort_count = self.session.execute(count_query).scalar()
            print(f"Found {cohort_count} existing cohorts")
            
            if cohort_count == 0:
                print("Loading sample data...")
                self._load_cohorts()
                self._generate_sample_patients()
                self._generate_sample_specimens()
                self._generate_sample_cell_populations()
                print("Sample data loaded successfully!")
        except Exception as e:
            print(f"Error checking cohorts: {str(e)}")
            # Try creating tables if they don't exist yet
            self.engine = init_db(str(self.engine.url))
            self.session = get_session(self.engine)
            
            # Try again after ensuring tables exist
            cohort_count = self.session.execute(count_query).scalar()
            if cohort_count == 0:
                print("Loading sample data after re-initializing tables...")
                self._load_cohorts()
                self._generate_sample_patients()
                self._generate_sample_specimens()
                self._generate_sample_cell_populations()
                print("Sample data loaded successfully!")
    
    def _load_cohorts(self):
        """Load sample cohort data."""
        cohorts_data = [
            Cohort(cohort_id=1, indication="Melanoma", specimens_count=76, 
                  patients_count=34, analyzed_specimens=76, cells_phenotyped=103477921),
            Cohort(cohort_id=2, indication="UC and Bladder", specimens_count=204, 
                  patients_count=79, analyzed_specimens=204, cells_phenotyped=114479742),
            Cohort(cohort_id=3, indication="Melanoma", specimens_count=468, 
                  patients_count=257, analyzed_specimens=460, cells_phenotyped=109679499),
            Cohort(cohort_id=4, indication="Melanoma", specimens_count=386, 
                  patients_count=142, analyzed_specimens=239, cells_phenotyped=122503137),
            Cohort(cohort_id=5, indication="NSCLC", specimens_count=35, 
                  patients_count=12, analyzed_specimens=35, cells_phenotyped=7379869)
        ]
        
        self.session.add_all(cohorts_data)
        self.session.commit()
        print(f"Added {len(cohorts_data)} cohorts")
    
    def _generate_sample_patients(self):
        """Generate sample patient data with responder status."""
        cohorts = self.session.query(Cohort).all()
        
        patient_id = 1
        patients = []
        
        for cohort in cohorts:
            # For each cohort, create the specified number of patients
            # Assume approximately 30% responders (randomized)
            for _ in range(cohort.patients_count):
                responder = bool(np.random.choice([0, 1], p=[0.7, 0.3]))
                patients.append(
                    Patient(
                        patient_id=patient_id,
                        cohort_id=cohort.cohort_id,
                        responder=responder
                    )
                )
                patient_id += 1
        
        self.session.add_all(patients)
        self.session.commit()
        print(f"Added {len(patients)} patients")
    
    def _generate_sample_specimens(self):
        """Generate sample specimen data with timepoints and specimen types."""
        patients = self.session.query(Patient).all()
        
        timepoints = ["Baseline", "C1D1", "C1D14", "C2D1", "C2D14"]
        specimen_types = ["Blood", "Tumor"]
        drug_classes = [None, "TCR", "PD-1"]
        
        specimen_id = 1
        specimens = []
        
        for patient in patients:
            # Each patient has 2-5 specimens at different timepoints
            num_specimens = np.random.randint(2, 6)
            selected_timepoints = np.random.choice(timepoints, num_specimens, replace=False)
            
            for timepoint in selected_timepoints:
                specimen_type = np.random.choice(specimen_types)
                drug_class = np.random.choice(drug_classes)
                
                specimens.append(
                    Specimen(
                        specimen_id=specimen_id,
                        patient_id=patient.patient_id,
                        timepoint=timepoint,
                        specimen_type=specimen_type,
                        drug_class=drug_class
                    )
                )
                specimen_id += 1
        
        self.session.add_all(specimens)
        self.session.commit()
        print(f"Added {len(specimens)} specimens")
    
    def _generate_sample_cell_populations(self):
        """Generate sample cell population data."""
        specimens = self.session.query(Specimen).all()
        
        # Cell types (based on the document)
        cell_types = [
            "CD4 T Central Memory",
            "CD4 T Effector Memory",
            "CD8 T Central Memory",
            "CD8 T Effector Memory",
            "NK Cells",
            "B Cells",
            "Monocytes",
            "Dendritic Cells"
        ]
        
        cell_id = 1
        batch_size = 500  # Reduced batch size for better memory management
        total_added = 0
        
        print(f"Generating cell populations for {len(specimens)} specimens...")
        
        for i, specimen in enumerate(specimens):
            # Generate counts for each cell type
            total_cells = np.random.randint(100000, 1000000)
            remaining_percentage = 100.0
            
            cell_populations_batch = []
            
            for j, cell_type in enumerate(cell_types):
                # Last cell type gets the remaining percentage
                if j == len(cell_types) - 1:
                    percentage = remaining_percentage
                else:
                    # Generate random percentage for this cell type
                    max_pct = min(remaining_percentage * 0.8, 50)
                    percentage = np.random.uniform(0.5, max_pct)
                    remaining_percentage -= percentage
                
                cell_count = int((percentage / 100) * total_cells)
                
                cell_populations_batch.append(
                    CellPopulation(
                        id=cell_id,
                        specimen_id=specimen.specimen_id,
                        cell_type=cell_type,
                        cell_count=cell_count,
                        percentage=percentage
                    )
                )
                cell_id += 1
            
            # Add in batches to avoid memory issues
            self.session.add_all(cell_populations_batch)
            total_added += len(cell_populations_batch)
            
            # Commit every batch_size specimens to avoid memory issues
            if (i + 1) % batch_size == 0 or i == len(specimens) - 1:
                print(f"Committing batch... ({i+1}/{len(specimens)} specimens processed)")
                self.session.commit()
        
        print(f"Added {total_added} cell populations")
        
        # After creating cell populations, generate individual cells
        self._generate_individual_cells()
    
    def _generate_individual_cells(self):
        """Generate individual cell data with marker measurements."""
        # Common markers to generate
        markers = {
            "CD4 T Central Memory": ["CD3", "CD4", "CD45RA", "CCR7", "CD62L"],
            "CD4 T Effector Memory": ["CD3", "CD4", "CD45RO", "CD27"],
            "CD8 T Central Memory": ["CD3", "CD8", "CD45RA", "CCR7", "CD62L"],
            "CD8 T Effector Memory": ["CD3", "CD8", "CD45RO", "CD27"],
            "NK Cells": ["CD56", "CD16", "NKG2D", "CD3-"],
            "B Cells": ["CD19", "CD20", "HLA-DR"],
            "Monocytes": ["CD14", "CD11b", "CD33", "HLA-DR"],
            "Dendritic Cells": ["CD11c", "HLA-DR", "CD86", "CD83"]
        }
        
        print("Starting to generate individual cells...")
        cell_populations = self.session.query(CellPopulation).all()
        
        # Limit to 100 cells per population for manageability
        max_cells_per_population = 100
        cell_id = 1
        marker_id = 1
        total_cells = 0
        total_markers = 0
        
        batch_size = 1000  # Batch size for cells
        cells_batch = []
        markers_batch = []
        
        for i, population in enumerate(cell_populations):
            # For demo purposes, only generate cells for a subset of the total count
            cells_to_generate = min(max_cells_per_population, population.cell_count)
            
            for j in range(cells_to_generate):
                # Create cell object
                cell = Cell(
                    cell_id=cell_id,
                    specimen_id=population.specimen_id,
                    population_id=population.id
                )
                cells_batch.append(cell)
                
                # Generate marker data for this cell
                cell_markers = markers.get(population.cell_type, ["CD45"])
                for marker in cell_markers:
                    # Positive cells have high intensity, negative cells have low intensity
                    is_positive = np.random.random() > 0.2  # 80% chance of being positive for relevant markers
                    
                    # Generate appropriate intensity based on positivity
                    if is_positive:
                        intensity = np.random.uniform(1000, 10000)
                    else:
                        intensity = np.random.uniform(10, 500)
                    
                    # Create marker measurement
                    marker_obj = CellMarker(
                        id=marker_id,
                        cell_id=cell_id,
                        marker_name=marker,
                        intensity=intensity,
                        positive=is_positive
                    )
                    markers_batch.append(marker_obj)
                    marker_id += 1
                    total_markers += 1
                
                cell_id += 1
                total_cells += 1
                
                # Commit in batches to avoid memory issues
                if len(cells_batch) >= batch_size:
                    print(f"Committing batch of {len(cells_batch)} cells with {len(markers_batch)} markers...")
                    self.session.add_all(cells_batch)
                    self.session.add_all(markers_batch)
                    self.session.commit()
                    cells_batch = []
                    markers_batch = []
            
            # Progress update
            if (i + 1) % 100 == 0:
                print(f"Processed {i+1} cell populations of {len(cell_populations)}")
        
        # Commit any remaining batch
        if cells_batch:
            print(f"Committing final batch of {len(cells_batch)} cells with {len(markers_batch)} markers...")
            self.session.add_all(cells_batch)
            self.session.add_all(markers_batch)
            self.session.commit()
        
        print(f"Added {total_cells} individual cells with {total_markers} marker measurements")
    
    def get_cell_details(self, cell_id):
        """Retrieve details for a specific cell with its markers."""
        try:
            cell = self.session.query(Cell).filter(Cell.cell_id == cell_id).first()
            
            if not cell:
                return None
                
            # Get all markers for this cell
            markers = self.session.query(CellMarker).filter(CellMarker.cell_id == cell_id).all()
            
            # Get the cell population info
            population = self.session.query(CellPopulation).filter(
                CellPopulation.id == cell.population_id
            ).first()
            
            result = {
                'cell_id': cell.cell_id,
                'specimen_id': cell.specimen_id,
                'population_id': cell.population_id,
                'cell_type': population.cell_type if population else "Unknown",
                'markers': [
                    {
                        'marker_name': m.marker_name,
                        'intensity': m.intensity,
                        'positive': m.positive
                    }
                    for m in markers
                ]
            }
            
            return result
        except Exception as e:
            print(f"Error getting cell details: {str(e)}")
            return None
    
    def get_population_cells(self, population_id, limit=100):
        """Retrieve cells for a specific cell population."""
        try:
            cells = self.session.query(Cell).filter(
                Cell.population_id == population_id
            ).limit(limit).all()
            
            return [
                {
                    'cell_id': c.cell_id
                }
                for c in cells
            ]
        except Exception as e:
            print(f"Error getting cells for population {population_id}: {str(e)}")
            return []
    
    def get_cohorts(self):
        """Retrieve all cohorts as a DataFrame."""
        try:
            cohorts = self.session.query(Cohort).all()
            return [
                {
                    'cohort_id': c.cohort_id,
                    'indication': c.indication,
                    'specimens_count': c.specimens_count,
                    'patients_count': c.patients_count,
                    'analyzed_specimens': c.analyzed_specimens,
                    'cells_phenotyped': c.cells_phenotyped
                } 
                for c in cohorts
            ]
        except Exception as e:
            print(f"Error getting cohorts: {str(e)}")
            return []
    
    def get_cohort_patients(self, cohort_id):
        """Retrieve patients for a specific cohort."""
        try:
            patients = self.session.query(Patient).filter(Patient.cohort_id == cohort_id).all()
            
            # Debug - get specimen counts for each patient
            patient_ids = [p.patient_id for p in patients]
            print(f"DEBUG: Found {len(patients)} patients for cohort {cohort_id}")
            
            # Get specimen counts for first few patients
            if patient_ids:
                sample_size = min(5, len(patient_ids))
                for i in range(sample_size):
                    pid = patient_ids[i]
                    count = self.session.query(Specimen).filter(Specimen.patient_id == pid).count()
                    print(f"DEBUG: Patient {pid} has {count} specimens")
            
            # Print total specimen count and average per patient
            total_specimens = self.session.query(Specimen).count()
            if len(patients) > 0:
                avg_specimens = total_specimens / len(patients)
                print(f"DEBUG: Average {avg_specimens:.2f} specimens per patient")
            
            return [
                {
                    'patient_id': p.patient_id,
                    'cohort_id': p.cohort_id,
                    'responder': p.responder
                }
                for p in patients
            ]
        except Exception as e:
            print(f"Error getting patients for cohort {cohort_id}: {str(e)}")
            return []
    
    def get_patient_specimens(self, patient_id):
        """Retrieve specimens for a specific patient."""
        try:
            print(f"DEBUG: Querying specimens for patient_id={patient_id}")
            specimens = self.session.query(Specimen).filter(Specimen.patient_id == patient_id).all()
            print(f"DEBUG: Found {len(specimens)} specimens for patient {patient_id}")
            
            # Additional debugging
            total_specimens = self.session.query(Specimen).count()
            print(f"DEBUG: Total specimens in database: {total_specimens}")
            
            # Check some random patient IDs with specimens
            if total_specimens > 0:
                sample_query = self.session.query(
                    Specimen.patient_id, 
                    text("COUNT(*) as specimen_count")
                ).group_by(Specimen.patient_id).limit(5)
                sample_patients = sample_query.all()
                print(f"DEBUG: Sample patients with specimens: {sample_patients}")
            
            return [
                {
                    'specimen_id': s.specimen_id,
                    'patient_id': s.patient_id,
                    'timepoint': s.timepoint,
                    'specimen_type': s.specimen_type,
                    'drug_class': s.drug_class
                }
                for s in specimens
            ]
        except Exception as e:
            print(f"Error getting specimens for patient {patient_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_specimen_cell_populations(self, specimen_id):
        """Retrieve cell populations for a specific specimen."""
        try:
            cell_pops = self.session.query(CellPopulation).filter(
                CellPopulation.specimen_id == specimen_id
            ).all()
            
            return [
                {
                    'id': cp.id,
                    'specimen_id': cp.specimen_id,
                    'cell_type': cp.cell_type,
                    'cell_count': cp.cell_count,
                    'percentage': cp.percentage
                }
                for cp in cell_pops
            ]
        except Exception as e:
            print(f"Error getting cell populations for specimen {specimen_id}: {str(e)}")
            return []
    
    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close()
            print("Database session closed")


if __name__ == "__main__":
    print("Initializing database...")
    db = DatabaseManager()
    db.load_sample_data()
    
    # Verify the data
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            cohort_count = conn.execute(text("SELECT COUNT(*) FROM cohorts")).scalar()
            patient_count = conn.execute(text("SELECT COUNT(*) FROM patients")).scalar()
            specimen_count = conn.execute(text("SELECT COUNT(*) FROM specimens")).scalar()
            cell_count = conn.execute(text("SELECT COUNT(*) FROM cell_populations")).scalar()
        
        print("\nDatabase Summary:")
        print(f"- Cohorts: {cohort_count}")
        print(f"- Patients: {patient_count}")
        print(f"- Specimens: {specimen_count}")
        print(f"- Cell populations: {cell_count}")
    except Exception as e:
        print(f"Error verifying data: {str(e)}")
    
    print("\nDatabase initialized with sample data!")
    db.close()