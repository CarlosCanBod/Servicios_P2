"""Comprueba avisos por transición, ausencia de bloqueo y fallos de salida de audio."""
from array import array
from dataclasses import replace
import unittest
from unittest.mock import Mock,patch
import wave
from tutor.audio import WarningSound,WARNING_PATH
from tutor.config import Config
from tutor.dialogue import Dialogue
from tutor.signals import Attention

WARNING={'to':'ligeramente_molesto','reason':'desatencion_persistente'}

class AudioTests(unittest.TestCase):
    def setUp(self):
        self.which=patch('tutor.audio.shutil.which',side_effect=lambda name:'/usr/bin/pw-play' if name=='pw-play' else None)
        self.which.start(); self.addCleanup(self.which.stop)
        self.popen=patch('tutor.audio.subprocess.Popen'); self.spawn=self.popen.start(); self.addCleanup(self.popen.stop)
        self.process=Mock(); self.process.poll.return_value=0; self.process.communicate.return_value=(None,'')
        self.spawn.return_value=self.process

    def test_real_dialogue_beeps_once_per_warning_not_per_frame_or_final(self):
        c=replace(Config(),warning_s=1.,escalate_s=1.,finish_s=1.,joke_after_s=100.)
        dialogue=Dialogue(c,['uno']); sound=WarningSound()
        for i in range(40):
            dialogue.update(i*.1,Attention.AWAY)
            for event in dialogue.events: sound.on_event(event)
            dialogue.events.clear(); sound.poll()
        self.assertEqual(self.spawn.call_count,2)
        self.assertEqual(sound.summary()['completed'],2)

    def test_recovery_break_and_normal_finish_do_not_beep(self):
        sound=WarningSound()
        for event in ({'to':'ligeramente_molesto','reason':'recupera_atencion'},
                      {'to':'ligeramente_molesto','reason':'segunda_subida_mano'},
                      {'to':'descanso','reason':'primera_subida_mano'},
                      {'to':'final_bueno','reason':'fin_leccion'}):
            self.assertFalse(sound.on_event(event))
        self.spawn.assert_not_called()

    def test_warning_after_joke_beeps(self):
        sound=WarningSound()
        self.assertTrue(sound.on_event({'to':'ligeramente_molesto','reason':'sin_reaccion_visible'}))

    def test_busy_playback_does_not_overlap_or_wait(self):
        self.process.poll.return_value=None
        sound=WarningSound(); self.assertTrue(sound.play()); self.assertTrue(sound.play()); self.assertFalse(sound.play())
        self.spawn.assert_called_once(); self.process.wait.assert_not_called(); self.process.communicate.assert_not_called()
        sound.close()

    def test_second_warning_waits_for_first_sound(self):
        first=Mock(); first.poll.return_value=None; first.communicate.return_value=(None,'')
        second=Mock(); second.poll.return_value=0; second.communicate.return_value=(None,'')
        self.spawn.side_effect=[first,second]
        sound=WarningSound(); sound.on_event(WARNING); sound.on_event(WARNING)
        self.assertEqual(self.spawn.call_count,1)
        first.poll.return_value=0; sound.poll()
        self.assertEqual(self.spawn.call_count,2)
        sound.poll(); self.assertEqual(sound.requested,2); self.assertEqual(sound.completed,2)

    def test_muted_is_silent(self):
        sound=WarningSound(enabled=False)
        self.assertFalse(sound.on_event(WARNING)); self.spawn.assert_not_called()

    def test_missing_player_is_explicit(self):
        with patch('tutor.audio.shutil.which',return_value=None): sound=WarningSound()
        self.assertFalse(sound.play()); self.assertIn('no se encuentra',sound.error)
        self.spawn.assert_not_called()

    def test_output_failure_does_not_retry_each_frame(self):
        self.process.poll.return_value=1; self.process.communicate.return_value=(None,'Dispositivo no disponible')
        sound=WarningSound(); sound.play(); sound.poll()
        self.assertIn('Dispositivo no disponible',sound.error)
        self.assertFalse(sound.on_event(WARNING)); self.spawn.assert_called_once()

    def test_start_failure_is_explicit(self):
        self.spawn.side_effect=OSError('No se puede ejecutar reproductor')
        sound=WarningSound(); self.assertFalse(sound.play()); self.assertIn('No se puede ejecutar',sound.error)

    def test_hung_player_is_terminated_without_waiting_in_ui(self):
        self.process.poll.return_value=None
        with patch('tutor.audio.time.monotonic',return_value=0):
            sound=WarningSound(); sound.play()
        with patch('tutor.audio.time.monotonic',return_value=4): sound.poll()
        self.process.terminate.assert_called_once(); self.process.wait.assert_not_called()
        self.assertIn('3 segundos',sound.error); sound.close()

    def test_sound_contains_two_tones_separated_by_silence(self):
        with wave.open(str(WARNING_PATH),'rb') as audio:
            self.assertEqual(audio.getnchannels(),1); self.assertEqual(audio.getsampwidth(),2)
            self.assertEqual(audio.getframerate(),44100)
            samples=array('h',audio.readframes(audio.getnframes()))
        tone=round(.18*44100); gap=round(.12*44100)
        self.assertEqual(len(samples),2*tone+gap)
        self.assertTrue(any(samples[:tone])); self.assertFalse(any(samples[tone:tone+gap]))
        self.assertEqual(samples[:tone],samples[tone+gap:])
        self.assertLessEqual(max(map(abs,samples)),round(.2*32767))

if __name__=='__main__': unittest.main()
