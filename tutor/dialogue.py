"""Máquina del enunciado: paciencia por niveles, chiste, descanso y dos finales."""
from enum import Enum
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
          State.BREAK:'¿Quieres un descanso? Baja la mano y vuelve a levantarla para continuar.',
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
        self.resume_state=State.INITIAL; self.paused_timers=(0.,0.)

    def transition(self, state, now, reason):
        old=self.state; self.state=state; self.bad_s=0.; self.recovery_s=0.
        self.message=MESSAGES[state]; self.message_until=now+2.
        self.events.append({'time_s':now,'from':old.value,'to':state.value,'reason':reason,'message':self.message})

    @property
    def finished(self): return self.state in (State.GOOD,State.BAD)

    def update(self, now, attention, hand_event=False, expression=None):
        if self.last_time is not None and now < self.last_time: raise ValueError('El reloj retrocede')
        dt=0. if self.last_time is None else now-self.last_time
        self.last_time=now
        # No atribuir el intervalo anterior a una señal recién llegada. Desconocido congela todo.
        valid_dt=dt if attention==self.previous_attention and dt<=self.c.stale_s else 0.
        self.previous_attention=attention
        if self.finished: return
        # Prioridad: finales ya fijados > mano > descanso > desconocido > avisos > chiste/lección.
        if hand_event:
            if self.state==State.BREAK:
                self.transition(self.resume_state,now,'segunda_subida_mano')
                self.bad_s,self.recovery_s=self.paused_timers
                if self.state==State.EMOTION:
                    self.joke_started=now
                    self.baseline_happy=expression.scores.get('happy') if expression and not expression.error else None
            else:
                self.resume_state=self.state
                self.paused_timers=(self.bad_s,self.recovery_s)
                self.transition(State.BREAK,now,'primera_subida_mano')
            return
        if self.state==State.BREAK or attention==Attention.UNKNOWN: return
        if self.state==State.EMOTION:
            self.joke_s += valid_dt
            if (expression and not expression.error and self.joke_started is not None
                and expression.time_s>=self.joke_started and now-expression.time_s<=self.c.emotion_stale_s
                and self.baseline_happy is not None
                and expression.scores.get('happy',0)>=self.c.happy_min
                and expression.scores.get('happy',0)-self.baseline_happy>=self.c.happy_delta):
                self.transition(State.INITIAL,now,'aumento_expresion_happy')
            elif self.joke_s>=self.c.joke_window_s:
                if expression is None or expression.error or now-expression.time_s>self.c.emotion_stale_s or self.baseline_happy is None:
                    self.transition(State.INITIAL,now,'expresion_no_evaluable')
                else:
                    self.transition(State.MILD,now,'sin_reaccion_visible')
            return
        if attention==Attention.AWAY:
            self.recovery_s=0.; self.bad_s+=valid_dt
            limit={State.INITIAL:self.c.warning_s,State.MILD:self.c.escalate_s,State.CLEAR:self.c.finish_s}[self.state]
            if self.bad_s>=limit-1e-9:
                self.transition({State.INITIAL:State.MILD,State.MILD:State.CLEAR,State.CLEAR:State.BAD}[self.state],now,'desatencion_persistente')
            return
        self.bad_s=0.
        if self.state in (State.MILD,State.CLEAR):
            self.recovery_s+=valid_dt
            if self.recovery_s>=self.c.recover_s-1e-9:
                self.transition(State.MILD if self.state==State.CLEAR else State.INITIAL,now,'recupera_atencion')
            return
        self.lesson_s+=valid_dt
        if self.lesson_s>=len(self.phrases)*self.c.phrase_s:
            self.transition(State.GOOD,now,'fin_leccion')
        elif not self.joke_done and self.lesson_s>=self.c.joke_after_s:
            self.joke_done=True; self.joke_s=0.; self.joke_started=now
            self.baseline_happy=(expression.scores.get('happy') if expression and not expression.error and now-expression.time_s<=self.c.emotion_stale_s else None)
            self.transition(State.EMOTION,now,'chiste')
        elif now>=self.message_until:
            self.message=self.phrases[min(int(self.lesson_s/self.c.phrase_s),len(self.phrases)-1)]
