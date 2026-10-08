"""Contrato entre percepción y decisión. None significa no evaluable, nunca False."""
from dataclasses import dataclass, field
from enum import Enum

class Attention(str, Enum):
    ATTENTIVE = 'atiende'
    AWAY = 'no_atiende'
    UNKNOWN = 'desconocida'

@dataclass
class Observation:
    time_s: float
    user_id: int = 0
    face: bool = False
    head_front: bool | None = None
    eyes_open: bool | None = None
    gaze_front: bool | None = None
    hand_up: bool | None = None
    reason: str = 'sin_cara'
    metrics: dict = field(default_factory=dict)
    bbox: tuple | None = None
    latency_ms: float = 0.0

@dataclass
class Expression:
    time_s: float
    user_id: int
    scores: dict = field(default_factory=dict)
    label: str | None = None
    error: str | None = None
    latency_ms: float = 0.0
