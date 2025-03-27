# database.py

import numpy as np
import pandas as pd
import os
import tempfile
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import init_db, get_session, Cohort, Patient, Specimen, CellPopulation

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