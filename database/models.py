# database/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Cohort(Base):
    __tablename__ = 'cohorts'
    
    id = Column(Integer, primary_key=True)
    indication = Column(String)
    type = Column(String)
    num_specimens = Column(Integer)
    num_patients = Column(Integer)
    analyzed_specimens = Column(Integer)
    treatment = Column(String)
    
    # Relationships
    marker_data = relationship("MarkerData", back_populates="cohort")
    cell_type_data = relationship("CellTypeData", back_populates="cohort")
    
class Marker(Base):
    __tablename__ = 'markers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    category = Column(String)
    description = Column(String)
    
    # Relationships
    marker_data = relationship("MarkerData", back_populates="marker")
    
# Update MarkerData in models.py
class MarkerData(Base):
    __tablename__ = 'marker_data'
    
    id = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, ForeignKey('cohorts.id'))
    marker_id = Column(Integer, ForeignKey('markers.id'))
    timepoint_id = Column(Integer, ForeignKey('timepoints.id'))  # Changed from timepoint string
    responder_value = Column(Float)
    nonresponder_value = Column(Float)
    
    # Relationships
    cohort = relationship("Cohort", back_populates="marker_data")
    marker = relationship("Marker", back_populates="marker_data")
    timepoint = relationship("Timepoint")  # Add this relationship

class CellTypeData(Base):
    __tablename__ = 'cell_type_data'
    
    id = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, ForeignKey('cohorts.id'))
    cell_type = Column(String)
    responder_frequency = Column(Float)
    nonresponder_frequency = Column(Float)
    
    # Relationships
    cohort = relationship("Cohort", back_populates="cell_type_data")

# Add this to models.py
class Timepoint(Base):
    __tablename__ = 'timepoints'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    order = Column(Integer)  # For sorting timepoints in the correct order