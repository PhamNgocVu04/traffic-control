from typing import Literal
from pydantic import BaseModel, ConfigDict


class CameraIn(BaseModel):
    name: str
    stream_url: str
    direction: Literal["North", "South", "East", "West"]
    roi_config: dict | None = None


class CameraOut(CameraIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str


class ModeIn(BaseModel):
    mode: Literal["AUTO", "MANUAL"]
    user_id: int | None = None


class ForcePhaseIn(BaseModel):
    direction_pair: Literal["North-South", "East-West"]
    user_id: int | None = None
