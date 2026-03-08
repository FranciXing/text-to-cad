"""
Pydantic models for CAD JSON Schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Union, Literal, Any
from enum import Enum


class DesignUnits(str, Enum):
    MM = "mm"
    CM = "cm"
    M = "m"
    INCH = "inch"


class Metadata(BaseModel):
    design_name: str = Field(..., description="Design name")
    description: Optional[str] = Field(None, description="Design description")
    units: DesignUnits = Field(default=DesignUnits.MM)


class ParameterDef(BaseModel):
    value: float
    description: Optional[str] = None


class PlaneDefinition(BaseModel):
    origin: List[float] = Field(..., min_length=3, max_length=3)
    normal: List[float] = Field(..., min_length=3, max_length=3)


class RectangleEntity(BaseModel):
    type: Literal["rectangle"] = "rectangle"
    width: Union[float, str]
    height: Union[float, str]
    centered: bool = True


class CircleEntity(BaseModel):
    type: Literal["circle"] = "circle"
    center: List[float] = Field(..., min_length=2, max_length=2)
    radius: Union[float, str]


SketchEntity = Union[RectangleEntity, CircleEntity]


class SketchStep(BaseModel):
    type: Literal["sketch"] = "sketch"
    id: str
    plane: Union[Literal["XY", "YZ", "XZ"], PlaneDefinition] = "XY"
    entities: List[SketchEntity]


class ExtrudeStep(BaseModel):
    type: Literal["extrude"] = "extrude"
    sketch_id: str
    distance: Union[float, str]
    operation: Literal["new", "add", "cut"] = "new"


class HoleStep(BaseModel):
    type: Literal["hole"] = "hole"
    position: List[float] = Field(..., min_length=3, max_length=3)
    diameter: Union[float, str]
    depth: Optional[float] = None
    through_all: bool = False


class FilletStep(BaseModel):
    type: Literal["fillet"] = "fillet"
    edges: Literal["all"] = "all"
    radius: float


ModelingStep = Union[SketchStep, ExtrudeStep, HoleStep, FilletStep]


class CADModelPlan(BaseModel):
    version: Literal["1.0"] = "1.0"
    metadata: Metadata
    parameters: Optional[Dict[str, ParameterDef]] = {}
    steps: List[ModelingStep]
    
    @field_validator('steps')
    @classmethod
    def validate_steps_not_empty(cls, v):
        if not v:
            raise ValueError('Steps list cannot be empty')
        return v


def resolve_parameter(value: Union[float, str], parameters: Dict[str, ParameterDef]) -> float:
    """Resolve a parameter reference to its actual value"""
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str) and value.startswith('$'):
        param_name = value[1:]
        if param_name in parameters:
            return parameters[param_name].value
        raise ValueError(f"Unknown parameter: {param_name}")
    
    raise ValueError(f"Invalid parameter value: {value}")
