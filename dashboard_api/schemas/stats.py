from typing import List
from pydantic import BaseModel, Field

class ProjectVolume(BaseModel):
    id: str = Field(alias="_id")
    count: int

class ConversionRate(BaseModel):
    id: str = Field(alias="_id")
    count: int

class RevenueOverTime(BaseModel):
    id: str = Field(alias="_id")
    revenue: int

class StatsOverviewResponse(BaseModel):
    project_volume: List[ProjectVolume]
    conversion_rates: List[ConversionRate]
    revenue: List[RevenueOverTime]
