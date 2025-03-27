# models.py

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()

class Cohort(Base):
    """Model representing a patient cohort with a specific cancer indication."""
    __tablename__ = 'cohorts'
    
    cohort_id = Column(Integer, primary_key=True)
    indication = Column(String, nullable=False)
    specimens_count = Column(Integer, nullable=False)
    patients_count = Column(Integer, nullable=False)
    analyzed_specimens = Column(Integer, nullable=False)
    cells_phenotyped = Column(Integer, nullable=False)
    
    # Relationships
    patients = relationship("Patient", back_populates="cohort", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cohort(cohort_id={self.cohort_id}, indication='{self.indication}')>"


class Patient(Base):
    """Model representing a patient in a cohort."""
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, ForeignKey('cohorts.cohort_id'), nullable=False)
    responder = Column(Boolean, nullable=False)
    
    # Relationships
    cohort = relationship("Cohort", back_populates="patients")
    specimens = relationship("Specimen", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(patient_id={self.patient_id}, responder={self.responder})>"


class Specimen(Base):
    """Model representing a biological specimen from a patient."""
    __tablename__ = 'specimens'
    
    specimen_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    timepoint = Column(String, nullable=False)
    specimen_type = Column(String, nullable=False)
    drug_class = Column(String, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="specimens")
    cell_populations = relationship("CellPopulation", back_populates="specimen", cascade="all, delete-orphan")
    cells = relationship("Cell", back_populates="specimen", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Specimen(specimen_id={self.specimen_id}, timepoint='{self.timepoint}', type='{self.specimen_type}')>"


class CellPopulation(Base):
    """Model representing a cell population quantification in a specimen."""
    __tablename__ = 'cell_populations'
    
    id = Column(Integer, primary_key=True)
    specimen_id = Column(Integer, ForeignKey('specimens.specimen_id'), nullable=False)
    cell_type = Column(String, nullable=False)
    cell_count = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    
    # Relationships
    specimen = relationship("Specimen", back_populates="cell_populations")
    cells = relationship("Cell", back_populates="population", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CellPopulation(id={self.id}, cell_type='{self.cell_type}', percentage={self.percentage})>"


class Cell(Base):
    """Model representing an individual cell with its flow cytometry measurements."""
    __tablename__ = 'cells'
    
    cell_id = Column(Integer, primary_key=True)
    specimen_id = Column(Integer, ForeignKey('specimens.specimen_id'), nullable=False)
    population_id = Column(Integer, ForeignKey('cell_populations.id'), nullable=False)
    
    # Relationships
    specimen = relationship("Specimen", back_populates="cells")
    population = relationship("CellPopulation", back_populates="cells")
    markers = relationship("CellMarker", back_populates="cell", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cell(cell_id={self.cell_id})>"


class CellMarker(Base):
    """Model representing marker expression measurements for individual cells."""
    __tablename__ = 'cell_markers'
    
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cells.cell_id'), nullable=False)
    marker_name = Column(String, nullable=False)
    intensity = Column(Float, nullable=False)  # Fluorescence intensity
    positive = Column(Boolean, nullable=False)  # Whether the cell is positive for this marker
    
    # Relationships
    cell = relationship("Cell", back_populates="markers")
    
    def __repr__(self):
        return f"<CellMarker(cell_id={self.cell_id}, marker='{self.marker_name}', intensity={self.intensity})>"


def init_db(db_url="sqlite:///immune_atlas.db"):
    """Initialize the database and create tables."""
    try:
        print(f"Creating engine with URL: {db_url}")
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        print("Tables created successfully")
        return engine
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        # Try with a different location if there's a permission error
        if "permission" in str(e).lower() and "sqlite://" in db_url:
            try:
                # Try in user's home directory
                home_dir = os.path.expanduser("~")
                alt_path = os.path.join(home_dir, "immune_atlas.db")
                alt_url = f"sqlite:///{alt_path}"
                print(f"Trying alternative path: {alt_url}")
                engine = create_engine(alt_url)
                Base.metadata.create_all(engine)
                print(f"Tables created successfully at alternative location: {alt_path}")
                return engine
            except Exception as alt_error:
                print(f"Error with alternative path: {str(alt_error)}")
                # Fall back to in-memory SQLite as a last resort
                print("Falling back to in-memory SQLite database")
                engine = create_engine("sqlite:///:memory:")
                Base.metadata.create_all(engine)
                return engine
        else:
            raise


def get_session(engine):
    """Create a new session."""
    Session = sessionmaker(bind=engine)
    return Session()