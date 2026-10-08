"""Fusión conservadora y filtro temporal. La expresión no prueba atención."""
from .signals import Attention

class AttentionFilter:
    def __init__(self, config):
        self.c = config
        self.reset()

    def reset(self):
        self.candidate = None
        self.since = None
        self.last_time = None
        self.last_user = None
        self.stable = Attention.UNKNOWN

    def update(self, obs, now):
        if obs is None or now - obs.time_s > self.c.stale_s or now < obs.time_s:
            self.reset()
            return Attention.UNKNOWN, 'percepcion_caducada'
        if self.last_user is not None and obs.user_id != self.last_user:
            self.reset()
        self.last_user = obs.user_id
        # Fallos de geometría, guiño y ausencia de cara invalidan la decisión.
        if not obs.face or obs.head_front is None or obs.eyes_open is None:
            self.candidate = None; self.since = None; self.stable = Attention.UNKNOWN
            self.last_time = obs.time_s
            return self.stable, obs.reason
        if obs.eyes_open and obs.gaze_front is None and obs.head_front:
            self.candidate = None; self.since = None; self.stable = Attention.UNKNOWN
            self.last_time = obs.time_s
            return self.stable, obs.reason
        raw = Attention.ATTENTIVE if obs.head_front and obs.eyes_open and obs.gaze_front else Attention.AWAY
        cause = 'ojos_cerrados' if obs.eyes_open is False else 'cabeza_o_mirada'
        if self.last_time is not None and obs.time_s-self.last_time > self.c.stale_s:
            self.candidate=None; self.since=None; self.stable=Attention.UNKNOWN
        self.last_time = obs.time_s
        if raw != self.candidate:
            self.candidate=raw; self.since=obs.time_s
        hold = self.c.recover_s if raw == Attention.ATTENTIVE else (self.c.closed_hold_s if cause=='ojos_cerrados' else self.c.away_hold_s)
        if obs.time_s-self.since >= hold-1e-9:
            self.stable=raw
        # Un parpadeo corto conserva el estado anterior; desde UNKNOWN no se inventa atención.
        return self.stable, 'frontal' if self.stable==Attention.ATTENTIVE else cause

class HandEdge:
    """Un evento por subida estable; exige bajada observada antes de rearmar."""
    def __init__(self, config):
        self.c=config; self.armed=True; self.value=None; self.since=None; self.last=None

    def update(self, value, time_s):
        if value is None:
            self.value=None; self.since=None; self.last=time_s
            return False
        if self.last is not None and time_s-self.last>self.c.stale_s:
            self.value=None; self.since=None
        self.last=time_s
        if value != self.value:
            self.value=value; self.since=time_s
        elapsed=time_s-self.since
        if not value and elapsed>=self.c.hand_release_s-1e-9:
            self.armed=True
        if value and self.armed and elapsed>=self.c.hand_hold_s-1e-9:
            self.armed=False
            return True
        return False
