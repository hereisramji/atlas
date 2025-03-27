# database.py

import numpy as np
from sqlalchemy.orm import Session
from models import init_db, get_session, Cohort, Patient, Specimen, CellPopulation

class DatabaseManager:
    """Manager for database operations using SQLAlchemy models."""
    
    def __init__(self, db_url="sqlite:///immune_atlas.db"):
        """Initialize database connection and ensure tables exist."""
        self.engine = init_db(db_url)
        self.session = get_session(self.engine)
    
    def load_sample_data(self):
        """Load sample data if the database is empty."""
        # Check if cohorts table is empty
        if self.session.query(Cohort).count() == 0:
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
        batch_size = 1000
        cell_populations_batch = []
        
        for specimen in specimens:
            # Generate counts for each cell type
            total_cells = np.random.randint(100000, 1000000)
            remaining_percentage = 100.0
            
            for i, cell_type in enumerate(cell_types):
                # Last cell type gets the remaining percentage
                if i == len(cell_types) - 1:
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
                if len(cell_populations_batch) >= batch_size:
                    self.session.add_all(cell_populations_batch)
                    self.session.commit()
                    cell_populations_batch = []
        
        # Add any remaining cell populations
        if cell_populations_batch:
            self.session.add_all(cell_populations_batch)
            self.session.commit()
    
    def get_cohorts(self):
        """Retrieve all cohorts as a DataFrame."""
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
    
    def get_cohort_patients(self, cohort_id):
        """Retrieve patients for a specific cohort."""
        patients = self.session.query(Patient).filter(Patient.cohort_id == cohort_id).all()
        return [
            {
                'patient_id': p.patient_id,
                'cohort_id': p.cohort_id,
                'responder': p.responder
            }
            for p in patients
        ]
    
    def get_patient_specimens(self, patient_id):
        """Retrieve specimens for a specific patient."""
        specimens = self.session.query(Specimen).filter(Specimen.patient_id == patient_id).all()
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
    
    def get_specimen_cell_populations(self, specimen_id):
        """Retrieve cell populations for a specific specimen."""
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
    
    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close()