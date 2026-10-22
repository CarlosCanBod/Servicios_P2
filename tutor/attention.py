"""Fusión de señales con tolerancia breve. Los fallos persistentes siguen siendo desconocidos."""
import math
from .signals import Attention

class AttentionFilter:
    def __init__(self, config):
        self.c=config
        self.reset()

    def reset(self):
        self.candidate=None; self.since=None; self.loss_since=None
        self.last_time=None; self.last_user=None; self.stable=Attention.UNKNOWN

    @staticmethod
    def classify(obs):
        if not obs.face: return Attention.UNKNOWN,obs.reason
        if obs.head_front is False:
            # Una cabeza desviada fiable basta aunque la malla de ojos falle al girar.
            return Attention.AWAY,'cabeza_desviada'
        if obs.head_front is None: return Attention.UNKNOWN,obs.reason
        if obs.eyes_open is False: return Attention.AWAY,'ojos_cerrados'
        if obs.eyes_open is None: return Attention.UNKNOWN,obs.reason
        if obs.gaze_front is None: return Attention.UNKNOWN,obs.reason
        if not obs.gaze_front: return Attention.AWAY,'mirada_desviada'
        return Attention.ATTENTIVE,'frontal'

    def update(self, obs, now):
        if (obs is None or not math.isfinite(now) or not math.isfinite(obs.time_s)
            or not 0<=now-obs.time_s<=self.c.stale_s):
            self.reset()
            return Attention.UNKNOWN,'percepcion_caducada'
        if self.last_user is not None and obs.user_id!=self.last_user: self.reset()
        self.last_user=obs.user_id
        if self.last_time is not None:
            if obs.time_s<self.last_time:
                self.reset()
                return Attention.UNKNOWN,'observacion_desordenada'
            if obs.time_s-self.last_time>self.c.stale_s: self.reset(); self.last_user=obs.user_id
        self.last_time=obs.time_s
        if obs.reason.startswith('error_vision'):
            # La tolerancia es para fluctuaciones visuales; no oculta averías del modelo.
            self.reset()
            return Attention.UNKNOWN,obs.reason
        raw,cause=self.classify(obs)
        if raw!=self.candidate:
            self.candidate=raw; self.since=obs.time_s
        duration=obs.time_s-self.since
        if raw==Attention.ATTENTIVE:
            # Si el parpadeo terminó antes de 0,5 s, no hay pausa ni nueva espera de recuperación.
            if self.stable==Attention.ATTENTIVE or duration>=self.c.attention_recover_s-1e-9:
                # Un único fotograma positivo no renueva indefinidamente la tolerancia
                # entre pérdidas repetidas. El retorno estable sí limpia el episodio.
                if duration>=self.c.attention_recover_s-1e-9: self.loss_since=None
                self.stable=Attention.ATTENTIVE
                return self.stable,'frontal'
            # No acumular paciencia negativa mientras se está confirmando la recuperación.
            self.stable=Attention.UNKNOWN
            return self.stable,'confirmando_atencion'
        if self.loss_since is None: self.loss_since=obs.time_s
        hold=self.c.closed_hold_s if cause=='ojos_cerrados' else self.c.away_hold_s
        grace=min(self.c.unknown_hold_s,hold) if raw==Attention.AWAY else self.c.unknown_hold_s
        if self.stable==Attention.ATTENTIVE and now-self.loss_since<grace-1e-9:
            reason='tolerancia_parpadeo' if cause in ('ojos_cerrados','guino_o_apertura_ambigua') else 'tolerancia_perdida_breve'
            return self.stable,reason
        # Cambiar entre «cerrados», «iris inválido» y «sin malla» no renueva la tolerancia.
        if raw==Attention.AWAY and duration>=hold-1e-9:
            self.stable=Attention.AWAY
            return self.stable,cause
        self.stable=Attention.UNKNOWN
        return self.stable,cause if raw==Attention.UNKNOWN else 'confirmando_desatencion'

class HandEdge:
    """Una subida por evento; rearme por bajada visible o ausencia prolongada válida."""
    def __init__(self, config):
        self.c=config; self.armed=True
        self.invalidate()

    def invalidate(self):
        # Un fallo o un salto de tiempo rompe la continuidad, pero no rearma el gesto.
        self.value=None; self.since=None; self.last=None

    def update(self, value, time_s, hand_present=None):
        if not math.isfinite(time_s):
            self.invalidate()
            return False
        if self.last is not None:
            if time_s<=self.last: return False
            if time_s-self.last>self.c.stale_s: self.invalidate()
        self.last=time_s
        # «Ausente» solo llega de inferencias válidas con una única cara principal.
        # Es una convención de interacción: tampoco prueba una bajada física, por
        # eso exige más tiempo que una bajada visible y nunca dispara por sí sola.
        candidate=('arriba' if value is True else 'abajo' if value is False
                   else 'ausente' if hand_present is False else None)
        if candidate is None:
            self.value=None; self.since=None
            return False
        if candidate!=self.value: self.value=candidate; self.since=time_s
        elapsed=time_s-self.since
        release_s=self.c.hand_absent_release_s if candidate=='ausente' else self.c.hand_release_s
        if candidate in ('abajo','ausente') and elapsed>=release_s-1e-9: self.armed=True
        if candidate=='arriba' and self.armed and elapsed>=self.c.hand_hold_s-1e-9:
            self.armed=False
            return True
        return False
