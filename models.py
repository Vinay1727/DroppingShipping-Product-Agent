from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime


class ProductInput(BaseModel):
    product_name: str
    supplier_price: float
    selling_price: float


class EngineResult(BaseModel):
    score: float
    max_score: float
    confidence: float
    details: Dict[str, Any]
    error: Optional[str] = None


class TrendMetrics(BaseModel):
    seven_day_avg: float = 0.0
    thirty_day_avg: float = 0.0
    ninety_day_avg: float = 0.0
    one_eighty_day_avg: float = 0.0
    direction: str = "stable"
    momentum: float = 0.0
    stability: float = 0.0


class ProviderHealth(BaseModel):
    name: str
    priority: int
    status: str
    error: Optional[str] = None


class HealthReport(BaseModel):
    providers: List[ProviderHealth]
    real_data_coverage: float
    trust_level: str


class FinalReport(BaseModel):
    product_name: str
    product_score: float
    confidence_score: float
    survival_probability: float
    decision: str
    engine_scores: Dict[str, EngineResult]
    summary: str
    health: Optional[HealthReport] = None
    generated_at: str = ""


class ProviderResult(BaseModel):
    source: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fetched_at: str = ""
