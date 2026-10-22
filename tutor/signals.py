"""Contrato entre percepción y decisión. None significa no evaluable, nunca False."""
from dataclasses import dataclass, field
from enum import Enum
import math

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
    # False: ejecución válida sin manos; True: hay mano, aunque el gesto sea ambiguo.
    # None: no atribuible (sin cara principal, varias personas o error del modelo).
    hand_present: bool | None = None

@dataclass
class Expression:
    time_s: float
    user_id: int
    scores: dict = field(default_factory=dict)
    label: str | None = None
    error: str | None = None
    latency_ms: float = 0.0

    def is_fresh(self, now, max_age_s, user_id=None):
        """Una salida vieja, futura, errónea o de otra sesión no permite valorar reacción."""
        return (not self.error and bool(self.scores) and math.isfinite(self.time_s)
                and math.isfinite(now) and 0<=now-self.time_s<=max_age_s
                and (user_id is None or self.user_id==user_id)
                and all(isinstance(v,(float,int)) and math.isfinite(v) and 0<=v<=1.001
                        for v in self.scores.values()))
