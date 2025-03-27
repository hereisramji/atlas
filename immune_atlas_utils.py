# immune_atlas_utils.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Union, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, and_, Float, distinct

from database.models import Cohort, Patient, Specimen, CellPopulation

def get_cell_type_comparison(session: Session, cohort_id: int, cell_type: str, 
                            timepoints: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Get comparison data for a specific cell type between responders and non-responders.
    
    Args:
        session: SQLAlchemy session
        cohort_id: ID of the cohort to analyze
        cell_type: Cell type to analyze
        timepoints: Optional list of timepoints to filter by
    
    Returns:
        DataFrame with comparison data
    """
    # Build the query using SQLAlchemy ORM
    query = (
        session.query(
            Patient.responder,
            Specimen.timepoint,
            Specimen.specimen_type,
            Specimen.drug_class,
            func.avg(CellPopulation.percentage).label('avg_percentage'),
            func.avg(CellPopulation.cell_count).label('avg_cell_count'),
            func.count(distinct(Patient.patient_id)).label('patient_count')
        )
        .join(Specimen, Patient.patient_id == Specimen.patient_id)
        .join(CellPopulation, Specimen.specimen_id == CellPopulation.specimen_id)
        .filter(
            Patient.cohort_id == cohort_id,
            CellPopulation.cell_type == cell_type
        )
    )
    
    # Add timepoint filter if specified
    if timepoints:
        query = query.filter(Specimen.timepoint.in_(timepoints))
    
    # Complete the query with grouping and ordering
    query = query.group_by(
        Patient.responder,
        Specimen.timepoint,
        Specimen.specimen_type,
        Specimen.drug_class
    ).order_by(Specimen.timepoint)
    
    # Execute the query and convert to DataFrame
    result = query.all()
    
    # Convert to DataFrame
    columns = ['responder', 'timepoint', 'specimen_type', 'drug_class', 'avg_percentage', 
               'avg_cell_count', 'patient_count']
    df = pd.DataFrame(result, columns=columns)
    
    # Convert responder column to string for better display
    if not df.empty and 'responder' in df.columns:
        df["responder_status"] = df["responder"].map({True: "Responder", False: "Non-Responder"})
    
    return df

def generate_timepoint_chart(data: pd.DataFrame, cell_type: str, metric: str = 'avg_percentage',
                           figsize: Tuple[int, int] = (12, 6)) -> plt.Figure:
    """
    Generate a chart showing cell type metrics over time for responders vs non-responders.
    
    Args:
        data: DataFrame with cell type data
        cell_type: Name of the cell type being analyzed
        metric: Metric to plot ('avg_percentage' or 'avg_cell_count')
        figsize: Figure size as (width, height)
    
    Returns:
        Matplotlib figure
    """
    # Verify data has required columns
    required_cols = ['responder_status', 'timepoint', metric]
    if not all(col in data.columns for col in required_cols):
        missing = [col for col in required_cols if col not in data.columns]
        raise ValueError(f"Data missing required columns: {missing}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Prepare data for plotting
    pivot_data = data.pivot_table(
        index="timepoint",
        columns="responder_status",
        values=metric
    ).reset_index()
    
    # Define standard timepoint order
    all_timepoints = ["Baseline", "C1D1", "C1D14", "C2D1", "C2D14"]
    
    # Handle missing timepoints by reindexing
    pivot_data = pivot_data.set_index("timepoint").reindex(all_timepoints).reset_index()
    
    # Set colors for consistency
    colors = {"Responder": "#4CAF50", "Non-Responder": "#F44336"}
    
    # Plot lines for each responder status
    for status in ["Responder", "Non-Responder"]:
        if status in pivot_data.columns:
            plt.plot(
                pivot_data["timepoint"], 
                pivot_data[status], 
                'o-', 
                label=status, 
                color=colors[status]
            )
    
    # Set chart attributes
    metric_label = "Average Percentage (%)" if metric == 'avg_percentage' else "Average Cell Count"
    plt.title(f"{cell_type} {metric_label} by Timepoint")
    plt.xlabel("Timepoint")
    plt.ylabel(metric_label)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    return fig

def find_discriminating_cell_types(session: Session, cohort_id: int, 
                                 min_difference: float = 5.0) -> pd.DataFrame:
    """
    Find cell types that discriminate best between responders and non-responders.
    
    Args:
        session: SQLAlchemy session
        cohort_id: ID of the cohort to analyze
        min_difference: Minimum percentage difference to consider significant
        
    Returns:
        DataFrame with cell types sorted by discrimination power
    """
    # Create subquery for responder data
    responder_subquery = (
        session.query(
            CellPopulation.cell_type,
            func.avg(CellPopulation.percentage).label('avg_percentage_responder')
        )
        .join(Specimen, CellPopulation.specimen_id == Specimen.specimen_id)
        .join(Patient, Specimen.patient_id == Patient.patient_id)
        .filter(
            Patient.cohort_id == cohort_id,
            Patient.responder == True
        )
        .group_by(CellPopulation.cell_type)
        .subquery()
    )
    
    # Create subquery for non-responder data
    non_responder_subquery = (
        session.query(
            CellPopulation.cell_type,
            func.avg(CellPopulation.percentage).label('avg_percentage_non_responder')
        )
        .join(Specimen, CellPopulation.specimen_id == Specimen.specimen_id)
        .join(Patient, Specimen.patient_id == Patient.patient_id)
        .filter(
            Patient.cohort_id == cohort_id,
            Patient.responder == False
        )
        .group_by(CellPopulation.cell_type)
        .subquery()
    )
    
    # Join the subqueries and calculate differences
    query = (
        session.query(
            responder_subquery.c.cell_type,
            responder_subquery.c.avg_percentage_responder,
            non_responder_subquery.c.avg_percentage_non_responder,
            (responder_subquery.c.avg_percentage_responder - 
             non_responder_subquery.c.avg_percentage_non_responder).label('difference'),
            func.abs(responder_subquery.c.avg_percentage_responder - 
                    non_responder_subquery.c.avg_percentage_non_responder).label('abs_difference')
        )
        .join(
            non_responder_subquery,
            responder_subquery.c.cell_type == non_responder_subquery.c.cell_type
        )
        .order_by(desc('abs_difference'))
    )
    
    # Execute the query and convert to DataFrame
    result = query.all()
    columns = ['cell_type', 'avg_percentage_responder', 'avg_percentage_non_responder', 
              'difference', 'abs_difference']
    df = pd.DataFrame(result, columns=columns)
    
    # Filter for minimum difference if specified
    if not df.empty and min_difference > 0:
        df = df[df['abs_difference'] >= min_difference]
    
    return df

def get_cell_type_distribution_by_drug(session: Session, cohort_id: int, cell_type: str) -> pd.DataFrame:
    """
    Get cell type distribution across different drug classes.
    
    Args:
        session: SQLAlchemy session
        cohort_id: ID of the cohort to analyze
        cell_type: Cell type to analyze
        
    Returns:
        DataFrame with cell type distribution by drug class
    """
    query = (
        session.query(
            Patient.responder,
            Specimen.drug_class,
            func.avg(CellPopulation.percentage).label('avg_percentage'),
            func.count(distinct(Patient.patient_id)).label('patient_count')
        )
        .join(Specimen, Patient.patient_id == Specimen.patient_id)
        .join(CellPopulation, Specimen.specimen_id == CellPopulation.specimen_id)
        .filter(
            Patient.cohort_id == cohort_id,
            CellPopulation.cell_type == cell_type,
            Specimen.drug_class != None
        )
        .group_by(
            Patient.responder,
            Specimen.drug_class
        )
        .order_by(
            Specimen.drug_class,
            Patient.responder
        )
    )
    
    # Execute the query and convert to DataFrame
    result = query.all()
    columns = ['responder', 'drug_class', 'avg_percentage', 'patient_count']
    df = pd.DataFrame(result, columns=columns)
    
    if not df.empty and 'responder' in df.columns:
        df["responder_status"] = df["responder"].map({True: "Responder", False: "Non-Responder"})
    
    return df

def calculate_response_prediction_metrics(session: Session, cohort_id: int, 
                                        cell_types: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate prediction metrics for how well cell types predict response.
    
    Args:
        session: SQLAlchemy session
        cohort_id: ID of the cohort to analyze
        cell_types: Optional list of cell types to include (defaults to all)
        
    Returns:
        DataFrame with prediction metrics
    """
    # Get all cell types if not specified
    if not cell_types:
        cell_types_query = (
            session.query(distinct(CellPopulation.cell_type))
            .join(Specimen, CellPopulation.specimen_id == Specimen.specimen_id)
            .join(Patient, Specimen.patient_id == Patient.patient_id)
            .filter(Patient.cohort_id == cohort_id)
        )
        cell_types = [row[0] for row in cell_types_query.all()]
    
    results = []
    
    for cell_type in cell_types:
        # First, create a CTE equivalent using a subquery
        avg_percentages = (
            session.query(
                Patient.patient_id,
                Patient.responder,
                func.avg(CellPopulation.percentage).label('avg_percentage')
            )
            .join(Specimen, Patient.patient_id == Specimen.patient_id)
            .join(CellPopulation, Specimen.specimen_id == CellPopulation.specimen_id)
            .filter(
                Patient.cohort_id == cohort_id,
                CellPopulation.cell_type == cell_type
            )
            .group_by(
                Patient.patient_id,
                Patient.responder
            )
            .subquery()
        )
        
        # Now query the metrics from this subquery
        metrics_query = session.query(
            # Cell type name
            func.literal(cell_type).label('cell_type'),
            
            # Average for responders
            func.avg(
                case(
                    [(avg_percentages.c.responder == True, avg_percentages.c.avg_percentage)],
                    else_=None
                )
            ).label('avg_responder'),
            
            # Average for non-responders
            func.avg(
                case(
                    [(avg_percentages.c.responder == False, avg_percentages.c.avg_percentage)],
                    else_=None
                )
            ).label('avg_non_responder'),
            
            # Difference
            (
                func.avg(
                    case(
                        [(avg_percentages.c.responder == True, avg_percentages.c.avg_percentage)],
                        else_=None
                    )
                ) -
                func.avg(
                    case(
                        [(avg_percentages.c.responder == False, avg_percentages.c.avg_percentage)],
                        else_=None
                    )
                )
            ).label('difference'),
            
            # Count metrics
            func.count(distinct(avg_percentages.c.patient_id)).label('patient_count'),
            func.sum(
                case(
                    [(avg_percentages.c.responder == True, 1)],
                    else_=0
                )
            ).label('responder_count'),
            func.sum(
                case(
                    [(avg_percentages.c.responder == False, 1)],
                    else_=0
                )
            ).label('non_responder_count')
        )
        
        # Calculate correlation
        # Note: This is complex in pure SQLAlchemy ORM, so we'll calculate it in Python
        
        # Execute the query and add to results
        result = metrics_query.one()
        result_dict = {
            'cell_type': result.cell_type,
            'avg_responder': result.avg_responder,
            'avg_non_responder': result.avg_non_responder,
            'difference': result.difference,
            'patient_count': result.patient_count,
            'responder_count': result.responder_count,
            'non_responder_count': result.non_responder_count
        }
        
        # Calculate correlation in Python
        percentages_query = (
            session.query(
                avg_percentages.c.avg_percentage,
                avg_percentages.c.responder
            )
        )
        percentages_data = [(row.avg_percentage, 1 if row.responder else 0) 
                           for row in percentages_query.all()]
        
        if percentages_data:
            df = pd.DataFrame(percentages_data, columns=['avg_percentage', 'responder'])
            result_dict['correlation'] = df['avg_percentage'].corr(df['responder'])
        else:
            result_dict['correlation'] = None
        
        results.append(result_dict)
    
    if results:
        return pd.DataFrame(results)
    else:
        return pd.DataFrame()

def get_patient_specimens(patient_id):
    specimens = session.query(Specimen).filter(Specimen.patient_id == patient_id).all()
    print(f"Query debug: SELECT * FROM specimens WHERE patient_id = {patient_id}")
    print(f"Got {len(specimens)} results")
    
    # Check if any specimens exist at all
    total_specimens = session.query(Specimen).count()
    print(f"Total specimens in database: {total_specimens}")
    
    # Check some sample patient_ids that have specimens
    if total_specimens > 0:
        sample_specimens = session.query(Specimen).limit(5).all()
        print("Sample specimens patient_ids:", [s.patient_id for s in sample_specimens])
    
    return specimens