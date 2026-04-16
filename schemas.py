"""
Pydantic schemas for validation.

PropertyFeatures    — what Stage 1 (extraction) produces
LLMExtractionResult — features + completeness metadata
PredictionResponse  — the full combined response from /predict
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class PropertyFeatures(BaseModel):
    
    # the 12 features the trained model actually uses are defined here. All of them are optional where the model's imputers will handle missing values
    
    overall_qual: Optional[int] = Field(None, ge=1, le=10, description="Overall quality 1-10")
    gr_liv_area: Optional[int] = Field(None, description="Above-ground living area sqft")
    year_built: Optional[int] = Field(None, description="Original construction year")
    total_bsmt_sf: Optional[float] = Field(None, description="Total basement sqft")
    first_flr_sf: Optional[float] = Field(None, description="First floor sqft")
    second_flr_sf: Optional[float] = Field(None, description="Second floor sqft")
    bsmtfin_sf_1: Optional[float] = Field(None, description="Finished basement sqft")
    lot_area: Optional[int] = Field(None, description="Lot size in sqft")
    full_bath: Optional[int] = Field(None, description="Full bathrooms above ground")
    garage_cars: Optional[int] = Field(None, description="Garage car capacity")
    bsmt_qual: Optional[str] = Field(None, description="Basement quality: Ex/Gd/TA/Fa/Po/None")
    kitchen_qual: Optional[str] = Field(None, description="Kitchen quality: Ex/Gd/TA/Fa/Po")


class LLMExtractionResult(BaseModel):
    
    # output from Stage 1 (the extraction LLM call), where the LLM notifies us which features were found vs which are still missing
    
    features: PropertyFeatures
    confident_features: List[str] = Field(
        description="Feature names the LLM confidently extracted from the query"
    )
    missing_features: List[str] = Field(
        description="Feature names NOT found in the query"
    )


class PredictionResponse(BaseModel):
    
    # response from /predict: extraction results + ML prediction + LLM interpretation

    query: str
    extracted_features: dict
    confident_features: List[str]
    missing_features: List[str]
    predicted_price: float
    interpretation: str