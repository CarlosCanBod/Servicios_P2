"""Parámetros explícitos: tiempos en segundos y geometría sin unidades salvo roll."""
from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Config:
    sample_s: float = 0.10
    stale_s: float = 0.8
    away_hold_s: float = 0.6
    closed_hold_s: float = 1.0
    recover_s: float = 1.0
    hand_hold_s: float = 0.5
    hand_release_s: float = 0.5
    warning_s: float = 4.0
    escalate_s: float = 6.0
    finish_s: float = 8.0
    phrase_s: float = 3.0
    joke_after_s: float = 12.0
    joke_window_s: float = 5.0
    emotion_period_s: float = 0.8
    emotion_stale_s: float = 2.5
    happy_min: float = 0.55
    happy_delta: float = 0.15
    ear_closed: float = 0.18
    ear_open: float = 0.22
    gaze_low: float = 0.30
    gaze_high: float = 0.70
    gaze_vertical_low: float = 0.15
    gaze_vertical_high: float = 0.85
    yaw_max: float = 0.23
    pitch_low: float = 0.25
    pitch_high: float = 0.78
    roll_max_deg: float = 35.0
    min_eye_px: float = 10.0
    min_face_px: float = 65.0
    face_confidence: float = 0.60
    track_iou: float = 0.15
    max_faces: int = 3
    width: int = 640

    def validate(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, (float, int)) or isinstance(value,bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{field.name}: debe ser un número positivo y finito')
        for name in ('max_faces','width'):
            if type(getattr(self,name)) is not int: raise ValueError(f'{name}: debe ser entero')
        for lo, hi in (('ear_closed','ear_open'),('gaze_low','gaze_high'),('pitch_low','pitch_high'),('gaze_vertical_low','gaze_vertical_high')):
            if not getattr(self,lo) < getattr(self,hi): raise ValueError(f'{lo} debe ser menor que {hi}')
        for name in ('gaze_high','gaze_vertical_high','happy_min','happy_delta','face_confidence','track_iou'):
            if getattr(self,name)>1: raise ValueError(f'{name}: fuera de [0,1]')
        if self.sample_s >= self.stale_s: raise ValueError('sample_s debe ser menor que stale_s')
        return self

    @classmethod
    def load(cls, path=None):
        data = json.loads(Path(path).read_text()) if path else {}
        return cls(**data).validate()

    def to_dict(self): return asdict(self)
