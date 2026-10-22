"""Mensajes según señales simuladas; no evalúan precisión del reconocimiento visual."""
from types import SimpleNamespace
import unittest
from tutor.attention import AttentionFilter
from tutor.config import Config
from tutor.dialogue import Dialogue,State,MESSAGES
from tutor.feedback import SIGNAL_MESSAGES,signal_guidance,tutor_message
from tutor.signals import Attention,Observation

A=Attention.ATTENTIVE; U=Attention.UNKNOWN; B=Attention.AWAY


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.dialogue=Dialogue(Config(),['Primera frase de la lección.'])

    def test_excessive_tilt_requests_a_posture_correction(self):
        obs=Observation(0.,face=True,head_front=None,reason='inclinacion_excesiva')
        text=tutor_message(obs,U,obs.reason,self.dialogue)
        self.assertEqual(text,'Endereza un poco la cabeza para que pueda evaluar tu mirada.')
        self.assertNotIn('no evaluable',text)

    def test_missing_face_small_eyes_and_unknown_gaze_have_different_actions(self):
        for reason,action in (('sin_cara_fiable','encuadre'),('ojos_pequenos','Acerca'),
                              ('iris_no_fiable','iris'),('usuario_principal_perdido','cara seleccionada')):
            with self.subTest(reason=reason):
                self.assertIn(action,tutor_message(Observation(0.),U,reason,self.dialogue))

    def test_unknown_eye_aperture_does_not_claim_closed_eyes_or_fatigue(self):
        text=signal_guidance('guino_o_apertura_ambigua')
        self.assertIn('No distingo',text)
        self.assertNotIn('cerrados',text); self.assertNotIn('cansancio',text)

    def test_tolerated_blink_keeps_lesson_and_lasting_tilt_shows_guidance(self):
        f=AttentionFilter(Config())
        def obs(t,**changes):
            return Observation(t,face=True,head_front=True,eyes_open=True,gaze_front=True,**changes)
        f.update(obs(0.),0.)
        self.assertEqual(f.update(obs(.2),.2)[0],A)
        blink=Observation(.3,face=True,head_front=True,eyes_open=None,reason='guino_o_apertura_ambigua')
        status,reason=f.update(blink,.3)
        self.assertEqual(tutor_message(blink,status,reason,self.dialogue),self.dialogue.message)
        tilt=Observation(.8,face=True,head_front=None,reason='inclinacion_excesiva')
        status,reason=f.update(tilt,.8)
        self.assertEqual(status,U)
        self.assertIn('Endereza',tutor_message(tilt,status,reason,self.dialogue))

    def test_first_and_second_warning_keep_text_and_add_specific_correction(self):
        for state in (State.MILD,State.CLEAR):
            with self.subTest(state=state):
                self.dialogue.transition(state,0.,'desatencion_persistente')
                before=(self.dialogue.state,self.dialogue.bad_s,self.dialogue.lesson_s,list(self.dialogue.events))
                message=tutor_message(Observation(0.),B,'ojos_cerrados',self.dialogue)
                self.assertTrue(message.startswith(MESSAGES[state]))
                self.assertIn('Ábrelos',message)
                self.assertEqual(before,(self.dialogue.state,self.dialogue.bad_s,self.dialogue.lesson_s,self.dialogue.events))

    def test_unreliable_signal_shows_guidance_instead_of_a_new_attention_warning(self):
        self.dialogue.transition(State.MILD,0.,'desatencion_persistente')
        text=tutor_message(Observation(0.),U,'inclinacion_excesiva',self.dialogue)
        self.assertIn('Endereza',text); self.assertNotIn(MESSAGES[State.MILD],text)
        self.assertEqual(self.dialogue.state,State.MILD)

    def test_break_and_both_endings_keep_their_message(self):
        for state in (State.BREAK,State.GOOD,State.BAD):
            with self.subTest(state=state):
                self.dialogue.transition(state,0.,'prueba')
                self.assertEqual(tutor_message(None,U,'percepcion_caducada',self.dialogue),MESSAGES[state])

    def test_head_direction_takes_priority_over_unknown_eyes(self):
        obs=Observation(0.,face=True,head_front=False,eyes_open=None,reason='sin_malla_correspondiente')
        self.assertIn('Orienta la cabeza',signal_guidance('confirmando_desatencion',obs))

    def test_technical_failure_does_not_request_a_posture_correction(self):
        text=signal_guidance('error_vision: RuntimeError: fallo')
        self.assertIn('análisis de imagen',text); self.assertNotIn('Endereza',text)
        self.assertIn('cámara',signal_guidance('percepcion_caducada',Observation(0.)))
        self.assertIn('preparando',signal_guidance('percepcion_caducada'))

    def test_unrecognized_reason_uses_a_useful_fallback(self):
        self.assertIn('Revisa el encuadre',signal_guidance('motivo_futuro'))

    def test_all_guidance_fits_in_the_main_message_area(self):
        # Tres líneas de 90 caracteres caben antes del rótulo de expresión.
        # Incluimos el aviso más largo para detectar futuras instrucciones excesivas.
        import textwrap
        d=SimpleNamespace(state=State.CLEAR,message=MESSAGES[State.CLEAR])
        for reason in SIGNAL_MESSAGES:
            with self.subTest(reason=reason):
                text=tutor_message(Observation(0.),B,reason,d)
                self.assertLessEqual(len(textwrap.wrap(text,width=90)),3)


if __name__=='__main__': unittest.main()
