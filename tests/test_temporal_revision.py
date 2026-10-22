"""Regresiones de la revisión: señales y coordenadas artificiales, nunca exactitud de visión."""
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import numpy as np
from tutor.config import Config
from tutor.signals import Attention,Observation,Expression
from tutor.attention import AttentionFilter,HandEdge
from tutor.dialogue import Dialogue,State
from tutor.geometry import eye_geometry,raised_hand
from tutor.vision import Perception,PrimaryUser

A=Attention.ATTENTIVE; B=Attention.AWAY; U=Attention.UNKNOWN
C=Config()

def obs(t,**kwargs):
    fields=dict(face=True,head_front=True,eyes_open=True,gaze_front=True,hand_up=None,reason='medicion_valida')
    fields.update(kwargs); return Observation(t,**fields)

def attentive_filter():
    f=AttentionFilter(C); f.update(obs(0),0); f.update(obs(.2),.2)
    return f

class TemporalRevisionTests(unittest.TestCase):
    def test_ambiguous_blink_does_not_pause_or_require_recovery(self):
        f=attentive_filter()
        for t in (.3,.4,.6,.79):
            self.assertEqual(f.update(obs(t,eyes_open=None,gaze_front=None,reason='guino_o_apertura_ambigua'),t)[0],A)
        self.assertEqual(f.update(obs(.8),.8)[0],A)

    def test_exact_half_second_closed_eyes_boundary(self):
        f=attentive_filter()
        for t in (.3,.5,.79):
            self.assertEqual(f.update(obs(t,eyes_open=False,gaze_front=None),t)[0],A)
        self.assertEqual(f.update(obs(.8,eyes_open=False,gaze_front=None),.8)[0],B)

    def test_half_second_unknown_boundary_does_not_become_away(self):
        f=attentive_filter()
        for t in (.3,.5,.79): self.assertEqual(f.update(obs(t,face=False),t)[0],A)
        self.assertEqual(f.update(obs(.8,face=False),.8)[0],U)

    def test_unknown_away_alternation_cannot_refresh_grace(self):
        f=attentive_filter()
        self.assertEqual(f.update(obs(.3,eyes_open=False,gaze_front=None),.3)[0],A)
        self.assertEqual(f.update(obs(.5,eyes_open=None,gaze_front=None),.5)[0],A)
        self.assertEqual(f.update(obs(.7,eyes_open=False,gaze_front=None),.7)[0],A)
        self.assertEqual(f.update(obs(.8,eyes_open=None,gaze_front=None),.8)[0],U)

    def test_look_aside_has_same_grace(self):
        f=attentive_filter()
        self.assertEqual(f.update(obs(.3,gaze_front=False),.3)[0],A)
        self.assertEqual(f.update(obs(.8,gaze_front=False),.8)[0],B)

    def test_one_positive_frame_cannot_renew_grace_forever(self):
        f=attentive_filter()
        for i in range(3,10):
            t=i*.1
            status,_=f.update(obs(t,gaze_front=i%2==0),t)
        self.assertNotEqual(status,A)

    def test_stale_data_never_get_extra_grace(self):
        f=attentive_filter()
        self.assertEqual(f.update(obs(.2),1.01)[0],U)

    def test_errors_bypass_visual_grace(self):
        f=attentive_filter()
        self.assertEqual(f.update(obs(.3,face=False,reason='error_vision: fallo'),.3)[0],U)

    def test_initial_unknown_is_not_assumed_attentive(self):
        f=AttentionFilter(C)
        for t in (0,.3,.6): self.assertEqual(f.update(obs(t,eyes_open=None),t)[0],U)

    def test_sustained_wink_is_unknown_after_grace(self):
        f=attentive_filter()
        f.update(obs(.3,eyes_open=None),.3)
        self.assertEqual(f.update(obs(.8,eyes_open=None),.8)[0],U)

    def test_reliable_head_turn_works_without_eye_mesh(self):
        f=AttentionFilter(C)
        f.update(obs(0,head_front=False,eyes_open=None,gaze_front=None),0)
        self.assertEqual(f.update(obs(.5,head_front=False,eyes_open=None,gaze_front=None),.5)[0],B)

    def test_recovery_confirmation_freezes_negative_patience(self):
        f=AttentionFilter(C)
        f.update(obs(0,head_front=False),0); f.update(obs(.5,head_front=False),.5)
        self.assertEqual(f.update(obs(.6),.6)[0],U)
        self.assertEqual(f.update(obs(.8),.8)[0],A)

    def test_bad_clock_is_unknown(self):
        f=attentive_filter()
        self.assertEqual(f.update(obs(float('nan')),1)[0],U)
        self.assertEqual(f.update(obs(0),float('nan'))[0],U)

    def test_lesson_advances_during_short_blink(self):
        f=AttentionFilter(C); d=Dialogue(replace(C,joke_after_s=100.),['frase']*20)
        for i in range(21):
            t=i*.1
            eye=None if 8<=i<=11 else True
            status,_=f.update(obs(t,eyes_open=eye,gaze_front=True if eye else None),t)
            d.update(t,status)
        self.assertAlmostEqual(d.lesson_s,1.8)
        self.assertFalse(d.events)

class DialogueRevisionTests(unittest.TestCase):
    def test_brief_return_does_not_reset_accumulated_patience(self):
        c=replace(C,warning_s=1.,recover_s=.5,joke_after_s=100.)
        d=Dialogue(c,['frase']*10)
        for i in range(8): d.update(i*.1,B)
        before=d.bad_s
        d.update(.8,A); d.update(.9,A)
        self.assertAlmostEqual(d.bad_s,before)
        for t in (1.,1.1,1.2,1.3): d.update(t,B)
        self.assertEqual(d.state,State.MILD)

    def test_unknown_interrupts_continuous_recovery(self):
        d=Dialogue(replace(C,recover_s=.3),['frase']*10)
        d.transition(State.MILD,0,'prueba')
        for t,s in ((0,A),(.2,A),(.3,U),(.4,A),(.6,A)): d.update(t,s)
        self.assertEqual(d.state,State.MILD)
        d.update(.7,A); self.assertEqual(d.state,State.INITIAL)

    def test_feedback_does_not_consume_hidden_lesson_text(self):
        d=Dialogue(replace(C,joke_after_s=100.),['frase']*10)
        d.transition(State.INITIAL,0,'recupera_atencion')
        for i in range(21): d.update(i*.1,A)
        self.assertAlmostEqual(d.lesson_s,0.)
        d.update(2.1,A); self.assertAlmostEqual(d.lesson_s,.1)

    def joke(self, **kwargs):
        c=replace(C,joke_after_s=.2,joke_window_s=1.,smile_hold_s=.2,feedback_s=.1,**kwargs)
        d=Dialogue(c,['frase']*20)
        for i in range(3): d.update(i*.1,A,expression=Expression(i*.1,0,{'happy':.1},'neutral'))
        self.assertEqual(d.state,State.EMOTION)
        return d

    def test_single_repeated_smile_result_is_not_sustained_smile(self):
        d=self.joke(); exp=Expression(.3,0,{'happy':.9},'happy')
        for i in range(3,10): d.update(i*.1,A,expression=exp)
        self.assertEqual(d.state,State.EMOTION)
        for i in range(10,14): d.update(i*.1,A,expression=exp)
        self.assertEqual(d.state,State.INITIAL)
        self.assertEqual(d.events[-1]['reason'],'expresion_no_evaluable')

    def test_future_expression_is_not_reaction(self):
        d=self.joke()
        for i in range(3,14): d.update(i*.1,A,expression=Expression(100.,0,{'happy':1.},'happy'))
        self.assertEqual(d.state,State.INITIAL)
        self.assertEqual(d.events[-1]['reason'],'expresion_no_evaluable')

    def test_only_pre_joke_expression_does_not_trigger_warning(self):
        d=self.joke(); exp=Expression(.1,0,{'happy':.1},'neutral')
        for i in range(3,14): d.update(i*.1,A,expression=exp)
        self.assertEqual(d.state,State.INITIAL)
        self.assertEqual(d.events[-1]['reason'],'expresion_no_evaluable')

    def test_smile_is_confirmed_by_two_distinct_measurements(self):
        d=self.joke()
        d.update(.3,A,expression=Expression(.3,0,{'happy':.9},'happy'))
        self.assertEqual(d.state,State.EMOTION)
        d.update(.5,A,expression=Expression(.5,0,{'happy':.9},'happy'))
        self.assertEqual(d.state,State.INITIAL)
        self.assertEqual(d.events[-1]['reason'],'sonrisa_visible')

    def test_old_smile_does_not_bridge_unknown_interval(self):
        d=self.joke(); old=Expression(.3,0,{'happy':.9},'happy')
        d.update(.3,A,expression=old); d.update(.4,U,expression=old)
        d.update(.5,A,expression=old)
        d.update(.7,A,expression=Expression(.7,0,{'happy':.9},'happy'))
        self.assertEqual(d.state,State.EMOTION)
        d.update(.9,A,expression=Expression(.9,0,{'happy':.9},'happy'))
        self.assertEqual(d.state,State.INITIAL)

    def test_eyes_away_have_priority_over_happy_during_joke(self):
        d=self.joke(warning_s=.4)
        for i in range(3,9): d.update(i*.1,B,expression=Expression(i*.1,0,{'happy':1.},'happy'))
        self.assertEqual(d.state,State.MILD)
        self.assertEqual(d.events[-1]['reason'],'desatencion_persistente')

    def test_break_near_deadline_starts_new_reaction_window(self):
        d=self.joke()
        for i in range(3,11): d.update(i*.1,A,expression=Expression(i*.1,0,{'happy':.1},'neutral'))
        d.update(1.1,A,hand_event=True)
        d.update(1.5,B); d.update(2.,B)
        d.update(2.1,A,hand_event=True)
        self.assertEqual(d.state,State.EMOTION); self.assertAlmostEqual(d.joke_s,0.)
        for i in range(22,27): d.update(i*.1,A,expression=Expression(i*.1,0,{'happy':.1},'neutral'))
        self.assertEqual(d.state,State.EMOTION)

    def test_nan_clock_is_rejected(self):
        with self.assertRaises(ValueError): Dialogue(C,['frase']).update(float('nan'),A)

class PerceptionRevisionTests(unittest.TestCase):
    def fake_perception(self):
        p=Perception.__new__(Perception); p.c=C; p.primary=PrimaryUser(C)
        p.user_id=0; p.last_ms=-1; p.last_time_s=None; p.previous_eyes_open=None
        p.mp=Mock()
        detection=SimpleNamespace(bounding_box=SimpleNamespace(origin_x=50,origin_y=50,width=200,height=200),
            categories=[SimpleNamespace(score=.9)],
            keypoints=[SimpleNamespace(x=x,y=y) for x,y in ((.25,.25),(.5,.25),(.375,.35),(.375,.5),(.2,.375),(.55,.375))])
        p.detector=Mock(); p.detector.detect_for_video.return_value=SimpleNamespace(detections=[detection])
        p.face=Mock(); p.face.detect_for_video.return_value=SimpleNamespace(face_landmarks=[])
        p.hands=Mock(); p.hands.detect_for_video.return_value=SimpleNamespace(hand_landmarks=[])
        return p

    def test_head_error_is_preserved_when_eye_mesh_is_missing(self):
        p=self.fake_perception()
        with patch('tutor.vision.head_geometry',return_value=(None,{'error':'inclinacion_excesiva','roll_deg':50.})):
            observation,_=p.process(np.zeros((300,400,3),dtype=np.uint8),0.)
        self.assertEqual(observation.reason,'inclinacion_excesiva')
        self.assertEqual(observation.metrics['head_error'],'inclinacion_excesiva')
        self.assertEqual(observation.metrics['eye_error'],'sin_malla_correspondiente')

    def test_missing_hand_is_unknown_not_a_release(self):
        p=self.fake_perception(); observation,_=p.process(np.zeros((300,400,3),dtype=np.uint8),0.)
        self.assertTrue(observation.face); self.assertIsNone(observation.hand_up)
        self.assertIs(observation.hand_present,False)

    def test_missing_face_does_not_authorize_hand_absence_release(self):
        p=self.fake_perception(); p.detector.detect_for_video.return_value.detections=[]
        observation,_=p.process(np.zeros((300,400,3),dtype=np.uint8),0.)
        self.assertFalse(observation.face); self.assertIsNone(observation.hand_present)

    def test_multiple_faces_do_not_authorize_hand_absence_release(self):
        p=self.fake_perception()
        p.detector.detect_for_video.return_value.detections*=2
        observation,_=p.process(np.zeros((300,400,3),dtype=np.uint8),0.)
        self.assertTrue(observation.face); self.assertIsNone(observation.hand_present)

    def test_present_but_ambiguous_hand_is_not_absent(self):
        p=self.fake_perception()
        p.hands.detect_for_video.return_value.hand_landmarks=[[SimpleNamespace(x=.5,y=.5)]*21]
        observation,_=p.process(np.zeros((300,400,3),dtype=np.uint8),0.)
        self.assertIs(observation.hand_present,True); self.assertIsNone(observation.hand_up)

    def hand(self,curled=False,lowered=False):
        p=np.full((21,2),50.,float); p[0]=(50,130)
        for mcp,pip,tip in ((5,6,8),(9,10,12),(13,14,16),(17,18,20)):
            x=20+mcp*2; p[mcp]=(x,100); p[pip]=(x,80)
            p[tip]=(x+45,95) if curled else (x,50)
        if lowered: p[:,1]+=200
        return p

    def test_curled_fingers_do_not_request_break(self):
        self.assertIsNone(raised_hand(self.hand(curled=True),(0,120,100,220)))
        self.assertTrue(raised_hand(self.hand(),(0,120,100,220)))
        self.assertFalse(raised_hand(self.hand(lowered=True),(0,120,100,220)))

    def test_narrow_open_eyes_and_hysteresis(self):
        from test_geometry import EyeTests
        mesh=EyeTests().mesh(height=3.8)  # EAR=0,19: ahora abierto; antes era ambiguo.
        self.assertTrue(eye_geometry(mesh,C)[0])
        band=EyeTests().mesh(height=3.)  # EAR=0,15, entre 0,13 y 0,18.
        self.assertIsNone(eye_geometry(band,C)[0])
        self.assertTrue(eye_geometry(band,C,previous_open=True)[0])
        # Al reabrir, una apertura ambigua no se acusa de cierre sostenido.
        self.assertIsNone(eye_geometry(band,C,previous_open=False)[0])
        closed=EyeTests().mesh(height=1.)
        self.assertFalse(eye_geometry(closed,C,previous_open=True)[0])

    def test_malformed_mesh_is_unknown(self):
        self.assertIsNone(eye_geometry(np.zeros(478),C)[0])

    def test_degenerate_hand_is_not_a_visible_lower(self):
        self.assertIsNone(raised_hand(np.zeros((21,2)),(0,120,100,220)))

    def test_expression_requires_correct_session_and_nonfuture_timestamp(self):
        exp=Expression(1.,2,{'happy':.9},'happy')
        self.assertTrue(exp.is_fresh(1.1,2.,2))
        self.assertFalse(exp.is_fresh(1.1,2.,1)); self.assertFalse(exp.is_fresh(.9,2.,2))
        self.assertFalse(Expression(1.,2,{'happy':float('nan')},'happy').is_fresh(1.1,2.,2))

if __name__=='__main__': unittest.main()
