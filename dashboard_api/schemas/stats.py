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

class TopReferrer(BaseModel):
    id: int = Field(alias="_id")
    count: int
    username: str | None = None
    full_name: str | None = None

class StatsOverviewResponse(BaseModel):
    project_volume: List[ProjectVolume]
    conversion_rates: List[ConversionRate]
    revenue: List[RevenueOverTime]
    top_referrers: List[TopReferrer]
