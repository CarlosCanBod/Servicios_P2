"""Pruebas con señales simuladas: verifican lógica, no precisión de los modelos."""
import unittest
from dataclasses import replace
from tutor.config import Config
from tutor.signals import Observation, Attention, Expression
from tutor.attention import AttentionFilter, HandEdge
from tutor.dialogue import Dialogue, State

C=replace(Config(),warning_s=1.,escalate_s=1.,finish_s=1.,recover_s=.3,
          joke_after_s=100.,phrase_s=1.)
A=Attention.ATTENTIVE; B=Attention.AWAY; U=Attention.UNKNOWN

def observation(t, **kwargs):
    defaults=dict(face=True,head_front=True,eyes_open=True,gaze_front=True,hand_up=False,reason='válida')
    defaults.update(kwargs); return Observation(t,**defaults)

class FilterTests(unittest.TestCase):
    def test_initial_unknown_then_reliable(self):
        f=AttentionFilter(C)
        self.assertEqual(f.update(observation(0),0)[0],U)
        self.assertEqual(f.update(observation(.3),.3)[0],A)
    def test_no_face_is_unknown_not_away(self):
        f=AttentionFilter(C)
        self.assertEqual(f.update(observation(10,face=False),10)[0],U)
    def test_stale_and_future(self):
        f=AttentionFilter(C)
        for now in (2.,-.1): self.assertEqual(f.update(observation(0),now)[0],U)
    def test_repeat_output_does_not_build_stability(self):
        f=AttentionFilter(C)
        f.update(observation(0),0)
        self.assertEqual(f.update(observation(0),.4)[0],U)
    def test_blink_short_keeps_attention(self):
        f=AttentionFilter(C); f.update(observation(0),0); f.update(observation(.3),.3)
        self.assertEqual(f.update(observation(.4,eyes_open=False,gaze_front=None),.4)[0],A)
        self.assertEqual(f.update(observation(.7),.7)[0],A)
    def test_closed_long_is_away(self):
        f=AttentionFilter(C)
        for i in range(12): status,_=f.update(observation(i*.1,eyes_open=False,gaze_front=None),i*.1)
        self.assertEqual(status,B)
    def test_wink_and_bad_mesh_are_unknown(self):
        f=AttentionFilter(C)
        self.assertEqual(f.update(observation(0,eyes_open=None),0)[0],U)
        self.assertEqual(f.update(observation(0,gaze_front=None),0)[0],U)
    def test_user_change_resets_history(self):
        f=AttentionFilter(C); f.update(observation(0),0); f.update(observation(.3),.3)
        self.assertEqual(f.update(observation(.4,user_id=1),.4)[0],U)
    def test_inference_gap_does_not_prove_duration(self):
        f=AttentionFilter(C); f.update(observation(0),0)
        self.assertEqual(f.update(observation(20),20)[0],U)

class HandTests(unittest.TestCase):
    def test_single_event_until_lowered(self):
        h=HandEdge(C); events=[]
        for i in range(21): events.append(h.update(True,i*.1))
        self.assertEqual(sum(events),1)
        for i in range(21,28): h.update(False,i*.1)
        self.assertFalse(h.update(True,2.8))
        self.assertTrue(h.update(True,3.3))
    def test_noise_does_not_trigger(self):
        h=HandEdge(C)
        for i in range(20): self.assertFalse(h.update(i%2==0,i*.1))
    def test_unknown_does_not_rearm(self):
        h=HandEdge(C); h.update(True,0); self.assertTrue(h.update(True,.5))
        h.update(None,.6); self.assertFalse(h.update(True,.7)); self.assertFalse(h.update(True,1.2))
    def test_sparse_detections_not_hold(self):
        h=HandEdge(C); h.update(True,0); self.assertFalse(h.update(True,4.))

class DialogueTests(unittest.TestCase):
    def setUp(self): self.d=Dialogue(C,['uno','dos','tres']); self.t=0.
    def run_for(self,duration,status,expression=None):
        for _ in range(round(duration/.1)):
            self.t+=.1; self.d.update(self.t,status,expression=expression)
    def test_normal_completion(self):
        self.run_for(3.3,A); self.assertEqual(self.d.state,State.GOOD)
    def test_progressive_warnings_and_bad_end(self):
        self.run_for(1.2,B); self.assertEqual(self.d.state,State.MILD)
        self.run_for(1.1,B); self.assertEqual(self.d.state,State.CLEAR)
        self.run_for(1.1,B); self.assertEqual(self.d.state,State.BAD)
    def test_recovery_lowers_one_level(self):
        self.run_for(2.3,B); self.assertEqual(self.d.state,State.CLEAR)
        self.run_for(.5,A); self.assertEqual(self.d.state,State.MILD)
        self.run_for(.3,A); self.assertEqual(self.d.state,State.INITIAL)
    def test_unknown_freezes_bad_timer(self):
        self.run_for(.6,B); before=self.d.bad_s
        self.run_for(5.,U); self.assertEqual(self.d.bad_s,before); self.assertEqual(self.d.state,State.INITIAL)
        self.run_for(.1,B); self.assertEqual(self.d.bad_s,before)
    def test_break_freezes_and_resumes(self):
        self.run_for(.5,B); before=self.d.bad_s
        self.d.update(self.t+.1,B,hand_event=True); self.t+=.1
        self.assertEqual(self.d.state,State.BREAK)
        self.run_for(5.,B); self.assertEqual(self.d.state,State.BREAK)
        self.d.update(self.t+.1,B,hand_event=True); self.t+=.1
        self.assertEqual(self.d.state,State.INITIAL); self.assertEqual(self.d.bad_s,before)
    def test_hand_priority_over_warning(self):
        self.run_for(1.,B); self.d.update(self.t+.1,B,hand_event=True)
        self.assertEqual(self.d.state,State.BREAK)
    def test_terminal_ignores_signals(self):
        self.run_for(3.3,A); self.d.update(self.t+.1,B,hand_event=True)
        self.assertEqual(self.d.state,State.GOOD)
    def test_large_gap_does_not_advance(self):
        self.d.update(0,A); self.d.update(100,A); self.assertEqual(self.d.lesson_s,0)
    def test_joke_smile_change_and_no_reaction(self):
        for reaction,target in ((.8,State.INITIAL),(.1,State.MILD)):
            c=replace(C,joke_after_s=.4,joke_window_s=.5)
            d=Dialogue(c,['uno','dos','tres'])
            for i in range(6):
                t=i*.1; d.update(t,A,expression=Expression(t,0,{'happy':.1},'neutral'))
            self.assertEqual(d.state,State.EMOTION)
            for i in range(6,12):
                t=i*.1; d.update(t,A,expression=Expression(t,0,{'happy':reaction},'happy'))
            self.assertEqual(d.state,target)
    def test_already_happy_not_reaction(self):
        c=replace(C,joke_after_s=.3,joke_window_s=.4)
        d=Dialogue(c,['uno','dos','tres'])
        for i in range(10):
            t=i*.1; d.update(t,A,expression=Expression(t,0,{'happy':.9},'happy'))
        self.assertEqual(d.state,State.MILD)
    def test_model_failure_does_not_penalize(self):
        c=replace(C,joke_after_s=.3,joke_window_s=.4)
        d=Dialogue(c,['uno','dos','tres'])
        for i in range(10): d.update(i*.1,A,expression=Expression(i*.1,0,error='modelo roto'))
        self.assertEqual(d.state,State.INITIAL)
    def test_expression_before_joke_not_reaction(self):
        c=replace(C,joke_after_s=.3,joke_window_s=.5)
        d=Dialogue(c,['uno','dos','tres'])
        for i in range(5): d.update(i*.1,A,expression=Expression(i*.1,0,{'happy':.1},'neutral'))
        d.update(.5,A,expression=Expression(.1,0,{'happy':.99},'happy'))
        self.assertEqual(d.state,State.EMOTION)
    def test_monotonic_clock_and_empty_lesson(self):
        with self.assertRaises(ValueError): Dialogue(C,[])
        self.d.update(1,A)
        with self.assertRaises(ValueError): self.d.update(.5,A)
    def test_pause_does_not_reset_lesson(self):
        self.run_for(.6,A); before=self.d.lesson_s
        self.d.update(self.t+.1,A,hand_event=True); self.t+=.1
        self.run_for(1.,A)
        self.d.update(self.t+.1,A,hand_event=True)
        self.assertEqual(self.d.lesson_s,before)

if __name__=='__main__': unittest.main()
