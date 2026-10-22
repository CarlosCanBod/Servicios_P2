"""Máquina del enunciado: estados, paciencia por niveles, descanso y reacción visible."""
from enum import Enum
import math
from .signals import Attention

class State(str, Enum):
    INITIAL='inicial'
    MILD='ligeramente_molesto'
    CLEAR='claramente_molesto'
    EMOTION='analisis_expresion'
    BREAK='descanso'
    GOOD='final_bueno'
    BAD='final_malo'

MESSAGES={State.INITIAL:'Como iba diciendo...',State.MILD:'¿Qué? ¿Continuamos?',
          State.CLEAR:'¿Esto te aburre? Vamos a intentarlo un poco más.',
          State.BREAK:'¿Quieres un descanso? Baja la mano un segundo con tu cara visible y vuelve a levantarla para continuar.',
          State.GOOD:'Hemos terminado la lección. Gracias por seguirla.',
          State.BAD:'Pues lo dejamos aquí. Ya continuaremos en otro momento.',
          State.EMOTION:'¿Por qué los robots no tienen miedo? Porque tienen nervios de acero.'}

class Dialogue:
    def __init__(self, config, phrases):
        if not phrases: raise ValueError('La lección no contiene frases')
        self.c=config; self.phrases=phrases; self.state=State.INITIAL
        self.lesson_s=0.; self.bad_s=0.; self.recovery_s=0.; self.joke_s=0.
        self.last_time=None; self.previous_attention=Attention.UNKNOWN
        self.message=phrases[0]; self.message_until=0.; self.events=[]
        self.joke_done=False; self.joke_started=None; self.baseline_happy=None
        self.resume_state=State.INITIAL; self.paused_bad_s=0.
        self.smile_since=None; self.last_expression_time=None; self.latest_post_expression=None
        self.first_post_time=None; self.post_samples=0
        self.reaction_after=None

    def transition(self, state, now, reason):
        old=self.state; self.state=state; self.bad_s=0.; self.recovery_s=0.
        self.message=MESSAGES[state]; self.message_until=now+self.c.feedback_s
        self.events.append({'time_s':now,'from':old.value,'to':state.value,'reason':reason,'message':self.message})

    @property
    def finished(self): return self.state in (State.GOOD,State.BAD)

    def _begin_reaction(self, now, expression):
        self.joke_s=0.; self.joke_started=now
        self._reset_expression_evidence(now)
        self.baseline_happy=(expression.scores.get('happy') if expression and
            expression.is_fresh(now,self.c.emotion_stale_s) else None)

    def _reset_expression_evidence(self, after_s=None):
        self.smile_since=None; self.last_expression_time=None; self.latest_post_expression=None
        self.first_post_time=None; self.post_samples=0
        if after_s is not None: self.reaction_after=after_s

    def _smile(self, expression, now):
        if (expression is None or not expression.is_fresh(now,self.c.emotion_stale_s)
            or expression.time_s<=max(self.joke_started,self.reaction_after)):
            self.smile_since=None
            return False
        if self.last_expression_time is not None:
            # Repetir en pantalla la misma inferencia no demuestra una sonrisa sostenida.
            if expression.time_s<=self.last_expression_time: return False
            if expression.time_s-self.last_expression_time>self.c.emotion_stale_s: self._reset_expression_evidence()
        self.last_expression_time=expression.time_s; self.latest_post_expression=expression
        self.post_samples+=1
        if self.first_post_time is None: self.first_post_time=expression.time_s
        happy=expression.scores.get('happy')
        if happy is None or happy<self.c.happy_min:
            self.smile_since=None
            return False
        if self.smile_since is None: self.smile_since=expression.time_s
        return expression.time_s-self.smile_since>=self.c.smile_hold_s-1e-9

    def update(self, now, attention, hand_event=False, expression=None):
        if not math.isfinite(now) or self.last_time is not None and now<self.last_time:
            raise ValueError('El reloj debe ser finito y no retroceder')
        dt=0. if self.last_time is None else now-self.last_time
        self.last_time=now
        valid_dt=dt if attention==self.previous_attention and dt<=self.c.stale_s else 0.
        if dt>self.c.stale_s:
            self.recovery_s=0.; self._reset_expression_evidence(now)
        self.previous_attention=attention
        if self.finished: return
        # Prioridad: final fijado > mano > descanso > desconocido > desatención > chiste/lección.
        if hand_event:
            if self.state==State.BREAK:
                self.transition(self.resume_state,now,'segunda_subida_mano')
                self.bad_s=self.paused_bad_s
                # La recuperación tiene que ser continua después de volver del descanso.
                if self.state==State.EMOTION: self._begin_reaction(now,expression)
            else:
                self.resume_state=self.state; self.paused_bad_s=self.bad_s
                self.transition(State.BREAK,now,'primera_subida_mano')
            return
        if self.state==State.BREAK: return
        if attention==Attention.UNKNOWN:
            # No se castiga el tiempo sin datos, pero tampoco se suma como recuperación.
            self.recovery_s=0.; self._reset_expression_evidence(now)
            return
        if attention==Attention.AWAY:
            self.recovery_s=0.; self._reset_expression_evidence(now); self.bad_s+=valid_dt
            # Cerrar los ojos o girarse también tiene prioridad durante el chiste.
            limit={State.INITIAL:self.c.warning_s,State.EMOTION:self.c.warning_s,
                   State.MILD:self.c.escalate_s,State.CLEAR:self.c.finish_s}[self.state]
            if self.bad_s>=limit-1e-9:
                target={State.INITIAL:State.MILD,State.EMOTION:State.MILD,
                        State.MILD:State.CLEAR,State.CLEAR:State.BAD}[self.state]
                self.transition(target,now,'desatencion_persistente')
            return
        self.recovery_s+=valid_dt
        # Un retorno fugaz no borra la paciencia acumulada. Se exige recuperación estable.
        if self.recovery_s>=self.c.recover_s-1e-9:
            self.bad_s=0.
            if self.state in (State.MILD,State.CLEAR):
                self.transition(State.MILD if self.state==State.CLEAR else State.INITIAL,now,'recupera_atencion')
                return
        if self.state in (State.MILD,State.CLEAR): return
        if self.state==State.EMOTION:
            self.joke_s+=valid_dt
            if self._smile(expression,now):
                # El diagrama pide «sonríe», no demostrar un cambio de emoción interna.
                # Una sonrisa ya presente no debe generar un aviso por falta de reacción.
                reason='sonrisa_ya_presente' if self.baseline_happy is not None and self.baseline_happy>=self.c.happy_min else 'sonrisa_visible'
                self.transition(State.INITIAL,now,reason)
                self.events[-1].update(happy_before=self.baseline_happy,happy_after=expression.scores['happy'])
            elif self.joke_s>=self.c.joke_window_s-1e-9:
                post=self.latest_post_expression
                if (post is None or not post.is_fresh(now,self.c.emotion_stale_s)
                    or self.post_samples<2 or post.time_s-self.first_post_time<self.c.smile_hold_s-1e-9):
                    self.transition(State.INITIAL,now,'expresion_no_evaluable')
                elif post.scores.get('happy',0)>=self.c.happy_min:
                    self.transition(State.INITIAL,now,'reaccion_no_confirmada')
                else:
                    self.transition(State.MILD,now,'sin_reaccion_visible')
            return
        # Mientras se muestra «Como iba diciendo...» no se consumen frases ocultas.
        visible_dt=min(valid_dt,max(0.,now-self.message_until))
        if now<self.message_until: return
        self.lesson_s+=visible_dt
        if self.lesson_s>=len(self.phrases)*self.c.phrase_s-1e-9:
            self.transition(State.GOOD,now,'fin_leccion')
        elif not self.joke_done and self.lesson_s>=self.c.joke_after_s-1e-9:
            self.joke_done=True; self._begin_reaction(now,expression)
            self.transition(State.EMOTION,now,'chiste')
        else:
            self.message=self.phrases[min(int(self.lesson_s/self.c.phrase_s),len(self.phrases)-1)]
