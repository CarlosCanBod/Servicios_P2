"""Orquestación con cámara, reloj y visión sustituidos. Sin dispositivo ni inferencias reales."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from tutor.app import main
from tutor.config import ROOT
from tutor.signals import Observation

class Clock:
    def __init__(self): self.now=0.
    def monotonic(self): return self.now
    def sleep(self,seconds): self.now+=seconds

class AppIntegrationTests(unittest.TestCase):
    def run_scenario(self,hand_signal,end=1.,late_only=False,window_closed=False,hand_present=None,
                     reason_signal=None,visible=False):
        clock=Clock()
        class Capture:
            def __init__(self,*args):
                self.started=clock.now; self.done=False; self.error=None; self.next=0.
            def read_latest(self):
                if clock.now+1e-8>=self.next and self.next<=end+1e-8:
                    t=self.next; self.next=round(self.next+.1,6)
                    return np.zeros((20,20,3),dtype=np.uint8),t,clock.now
                if clock.now>end+.1: self.done=True
                return None
            def close(self): pass
        class Vision:
            def __init__(self,*args): self.ready=True; self.error=None; self.pending=None
            def submit(self,packet):
                frame,t,user=packet
                reason=reason_signal(t) if reason_signal else 'sin_malla_correspondiente'
                observation=Observation(t,user_id=user,face=not reason.startswith('error_vision'),head_front=True,
                    eyes_open=None,gaze_front=None,hand_up=hand_signal(t),reason=reason,
                    hand_present=hand_present(t) if hand_present else None)
                self.pending=(observation,None)
            def receive(self):
                if late_only and clock.now<end+.25: return None
                result=self.pending; self.pending=None; return result
            def close(self): pass
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'result.json'
            with patch('tutor.app.Capture',Capture),patch('tutor.app.Worker',Vision),\
                 patch('tutor.app.time.monotonic',clock.monotonic),\
                 patch('tutor.app.time.perf_counter',clock.monotonic),\
                 patch('tutor.app.time.sleep',clock.sleep),\
                 patch('tutor.app.render',return_value=np.zeros((20,20,3),dtype=np.uint8)) as render_mock,\
                 patch('tutor.app.cv2.imshow'),patch('tutor.app.cv2.waitKey',return_value=-1),\
                 patch('tutor.app.cv2.getWindowProperty',return_value=0 if window_closed else 1),\
                 patch('tutor.app.cv2.destroyAllWindows'),patch.dict('os.environ',{'DISPLAY':':prueba'}),\
                 redirect_stdout(io.StringIO()):
                args=['--input',str(ROOT/'video.mp4'),'--no-emotion','--no-sound','--log',str(path)]
                if not window_closed and not visible: args.append('--headless')
                code=main(args)
            self.assertEqual(code,0)
            result=json.loads(path.read_text())
            if visible: result['_render_errors']=[call.args[6] for call in render_mock.call_args_list]
            return result

    def test_hand_can_pause_with_unknown_eyes_between_ui_frames(self):
        r=self.run_scenario(lambda t:True)
        self.assertEqual([e['to'] for e in r['events']],['descanso'])
        self.assertEqual(r['summary']['state'],'descanso')

    def test_hand_loss_does_not_resume_break(self):
        r=self.run_scenario(lambda t:None if .7<=t<=1.4 else True,end=2.2)
        self.assertEqual([e['to'] for e in r['events']],['descanso'])

    def test_visible_lower_and_new_raise_resume_break(self):
        r=self.run_scenario(lambda t:False if .7<=t<=1.3 else True,end=2.2)
        self.assertEqual([e['to'] for e in r['events']],['descanso','inicial'])
        self.assertEqual(r['events'][1]['reason'],'segunda_subida_mano')

    def test_open_hand_with_lower_palm_can_pause_and_resume(self):
        from tutor.geometry import raised_hand
        from test_temporal_revision import PerceptionRevisionTests
        raised=PerceptionRevisionTests().hand(); raised[:,1]+=100
        lower=raised.copy(); lower[:,1]+=50
        box=(0,120,100,220)
        r=self.run_scenario(lambda t:raised_hand(lower if .7<=t<=1.3 else raised,box),end=2.2)
        self.assertEqual([e['to'] for e in r['events']],['descanso','inicial'])

    def test_lower_out_of_frame_and_raise_resumes_break(self):
        absent=lambda t:.7<=t<=2.1
        r=self.run_scenario(lambda t:None if absent(t) else True,end=3.4,
                            hand_present=lambda t:not absent(t))
        self.assertEqual([e['to'] for e in r['events']],['descanso','inicial'])
        self.assertEqual(r['events'][1]['reason'],'segunda_subida_mano')

    def test_brief_hand_dropout_does_not_resume_break(self):
        absent=lambda t:.7<=t<=1.1
        r=self.run_scenario(lambda t:None if absent(t) else True,end=2.2,
                            hand_present=lambda t:not absent(t))
        self.assertEqual([e['to'] for e in r['events']],['descanso'])

    def test_absence_alone_never_resumes_break(self):
        r=self.run_scenario(lambda t:None if t>=.7 else True,end=3.4,
                            hand_present=lambda t:t<.7)
        self.assertEqual([e['to'] for e in r['events']],['descanso'])

    def test_eof_waits_for_final_inference(self):
        r=self.run_scenario(lambda t:None,end=.5,late_only=True)
        self.assertEqual(r['summary']['stop_reason'],'fin_video')
        self.assertEqual(len(r['observations']),1)
        self.assertAlmostEqual(r['observations'][0]['time_s'],.5)
        self.assertAlmostEqual(r['summary']['lesson_s'],0.)

    def test_window_close_stops_application(self):
        r=self.run_scenario(lambda t:None,window_closed=True)
        self.assertEqual(r['summary']['stop_reason'],'ventana_cerrada')

    def test_transient_vision_error_does_not_remain_visible(self):
        r=self.run_scenario(lambda t:None,end=1.,visible=True,
            reason_signal=lambda t:'error_vision: fallo temporal' if .2<=t<.4 else 'sin_malla_correspondiente')
        self.assertIn('error_vision: fallo temporal',r['_render_errors'])
        self.assertIsNone(r['_render_errors'][-1])
        self.assertIn('error_vision: fallo temporal',r['summary']['errors'])

if __name__=='__main__': unittest.main()
