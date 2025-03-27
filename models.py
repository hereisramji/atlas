# models.py

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

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
    
    def __repr__(self):
        return f"<CellPopulation(id={self.id}, cell_type='{self.cell_type}', percentage={self.percentage})>"


def init_db(db_url="sqlite:///immune_atlas.db"):
    """Initialize the database and create tables."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Create a new session."""
    Session = sessionmaker(bind=engine)
    return Session()