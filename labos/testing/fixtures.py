"""
Test Fixtures

Factory classes and utilities for generating test data.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import random


@dataclass
class ExperimentFactory:
    """Factory for creating test experiments"""
    
    @staticmethod
    def create(
        exp_id: Optional[str] = None,
        title: str = "Test Experiment",
        status: str = "draft",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a test experiment
        
        Args:
            exp_id: Optional experiment ID (generates UUID if None)
            title: Experiment title
            status: Experiment status
            metadata: Additional metadata
            
        Returns:
            Experiment dictionary
            
        Educational Note:
            Factories simplify test data creation by providing sensible
            defaults while allowing customization of specific fields.
        """
        if exp_id is None:
            exp_id = str(uuid.uuid4())
            
        experiment = {
            "id": exp_id,
            "title": title,
            "status": status,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
        }
        
        return experiment
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Create multiple test experiments
        
        Args:
            count: Number of experiments to create
            **kwargs: Arguments passed to create()
            
        Returns:
            List of experiment dictionaries
        """
        return [ExperimentFactory.create(**kwargs) for _ in range(count)]


@dataclass
class DatasetFactory:
    """Factory for creating test datasets"""
    
    @staticmethod
    def create(
        dataset_id: Optional[str] = None,
        label: str = "Test Dataset",
        kind: str = "experimental",
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a test dataset
        
        Args:
            dataset_id: Optional dataset ID
            label: Dataset label
            kind: Dataset kind/type
            data: Dataset payload
            metadata: Additional metadata
            
        Returns:
            Dataset dictionary
        """
        if dataset_id is None:
            dataset_id = str(uuid.uuid4())
            
        dataset = {
            "id": dataset_id,
            "label": label,
            "kind": kind,
            "data": data or {},
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0"
        }
        
        return dataset
    
    @staticmethod
    def create_with_spectrum(
        n_peaks: int = 10,
        mass_range: tuple = (50, 500),
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create dataset with spectrum data
        
        Args:
            n_peaks: Number of peaks to generate
            mass_range: (min_mass, max_mass) tuple
            **kwargs: Additional arguments for create()
            
        Returns:
            Dataset with spectrum data
        """
        spectrum = generate_test_spectrum(n_peaks, mass_range)
        kwargs["data"] = {"spectrum": spectrum}
        kwargs["kind"] = "spectrum"
        return DatasetFactory.create(**kwargs)


@dataclass
class JobFactory:
    """Factory for creating test jobs"""
    
    @staticmethod
    def create(
        job_id: Optional[str] = None,
        module_key: str = "test.module",
        status: str = "queued",
        params: Optional[Dict[str, Any]] = None,
        experiment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a test job
        
        Args:
            job_id: Optional job ID
            module_key: Module identifier
            status: Job status
            params: Job parameters
            experiment_id: Associated experiment ID
            
        Returns:
            Job dictionary
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
            
        job = {
            "id": job_id,
            "module_key": module_key,
            "status": status,
            "params": params or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "retry_count": 0,
            "max_retries": 3
        }
        
        if experiment_id:
            job["experiment_id"] = experiment_id
            
        return job
    
    @staticmethod
    def create_workflow(
        n_jobs: int = 3,
        experiment_id: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Create a workflow of linked jobs
        
        Args:
            n_jobs: Number of jobs in workflow
            experiment_id: Shared experiment ID
            **kwargs: Arguments passed to create()
            
        Returns:
            List of job dictionaries
        """
        if experiment_id is None:
            experiment_id = str(uuid.uuid4())
            
        return [
            JobFactory.create(experiment_id=experiment_id, **kwargs)
            for _ in range(n_jobs)
        ]


def generate_test_spectrum(
    n_peaks: int = 10,
    mass_range: tuple = (50, 500),
    intensity_range: tuple = (0.1, 100.0),
    seed: Optional[int] = None
) -> List[Dict[str, float]]:
    """
    Generate realistic test spectrum data
    
    Args:
        n_peaks: Number of peaks
        mass_range: (min, max) mass values
        intensity_range: (min, max) intensity values
        seed: Random seed for reproducibility
        
    Returns:
        List of {mz, intensity} dictionaries
        
    Educational Note:
        Seeded random generation ensures reproducible test data,
        critical for debugging and CI/CD reliability.
    """
    if seed is not None:
        random.seed(seed)
        
    min_mass, max_mass = mass_range
    min_int, max_int = intensity_range
    
    # Generate masses
    masses = sorted([
        random.uniform(min_mass, max_mass)
        for _ in range(n_peaks)
    ])
    
    # Generate intensities (base peak = 100)
    intensities = [random.uniform(min_int, max_int) for _ in range(n_peaks)]
    max_intensity = max(intensities)
    normalized = [i / max_intensity * 100.0 for i in intensities]
    
    spectrum = [
        {"mz": round(m, 2), "intensity": round(i, 2)}
        for m, i in zip(masses, normalized)
    ]
    
    return spectrum


def generate_test_dataset(
    kind: str = "experimental",
    n_records: int = 100,
    fields: Optional[List[str]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate test dataset with structured records
    
    Args:
        kind: Dataset kind
        n_records: Number of records
        fields: Field names (defaults to common fields)
        seed: Random seed
        
    Returns:
        Dataset dictionary
        
    Educational Note:
        Structured test data helps verify data pipeline
        correctness across various field types and sizes.
    """
    if seed is not None:
        random.seed(seed)
        
    if fields is None:
        fields = ["id", "measurement", "temperature", "timestamp"]
        
    records = []
    for i in range(n_records):
        record = {
            "id": i + 1,
            "measurement": round(random.uniform(10.0, 100.0), 2),
            "temperature": round(random.uniform(20.0, 30.0), 1),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        records.append(record)
        
    dataset = DatasetFactory.create(
        kind=kind,
        data={"records": records}
    )
    
    return dataset


def create_test_molecule(
    formula: str = "C6H12O6",
    name: str = "Test Molecule",
    mass: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create test molecule dictionary
    
    Args:
        formula: Molecular formula
        name: Molecule name
        mass: Molecular mass (calculated if None)
        
    Returns:
        Molecule dictionary
    """
    if mass is None:
        # Simple mass calculation
        atomic_masses = {"C": 12.01, "H": 1.008, "O": 16.00, "N": 14.01}
        mass = 0.0
        i = 0
        while i < len(formula):
            if formula[i].isupper():
                element = formula[i]
                i += 1
                if i < len(formula) and formula[i].islower():
                    element += formula[i]
                    i += 1
                    
                count_str = ""
                while i < len(formula) and formula[i].isdigit():
                    count_str += formula[i]
                    i += 1
                    
                count = int(count_str) if count_str else 1
                mass += atomic_masses.get(element, 0.0) * count
                
    molecule = {
        "name": name,
        "formula": formula,
        "mass": round(mass, 2),
        "structure": f"SMILES representation for {formula}"
    }
    
    return molecule
