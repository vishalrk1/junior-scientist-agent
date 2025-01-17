from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AdvisorReport:
    """Dataclass for storing advisor reports"""
    task: str
    model_or_algorithm: str
    frameworks: List[str]
    reference: List[str]
    evaluation_metric: List[str]
    training_method: str
    device: str
    suggestion: str

@dataclass
class AnalysisResult:
    """Dataclass for storing analysis results"""
    category: str
    steps: str

@dataclass
class AnalysisReport:
    """Dataclass for storing analysis report"""
    dataset_hash: str
    timestamp: str
    results: List['AnalysisResult']
    metadata: Dict[str, Any]

@dataclass
class MLTask:
    """Dataclass for storing ML development tasks"""
    task: str
    description: str
    dependencies: List[str]

@dataclass
class MLPlan:
    """Dataclass for storing the complete ML development plan"""
    model: str
    tasks: List[MLTask]
    evaluation_metrics: List[str]
    considerations: Dict[str, str]