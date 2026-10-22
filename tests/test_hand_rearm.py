"""Secuencias controladas: verifican el rearme, no la precisión del detector visual."""
import unittest
from tutor.attention import HandEdge
from tutor.config import Config
from tutor.interface import hand_description
from tutor.signals import Observation


class HandRearmTests(unittest.TestCase):
    def paused(self):
        hand=HandEdge(Config())
        self.assertFalse(hand.update(True,0.))
        self.assertTrue(hand.update(True,.5))
        return hand

    def test_valid_absence_arms_without_producing_event(self):
        hand=self.paused()
        for i in range(6,17):
            self.assertFalse(hand.update(None,i/10,hand_present=False))
        self.assertTrue(hand.armed)
        self.assertFalse(hand.update(True,1.7,hand_present=True))
        self.assertTrue(hand.update(True,2.2,hand_present=True))
        self.assertFalse(hand.update(True,2.8,hand_present=True))

    def test_short_absence_does_not_arm(self):
        hand=self.paused()
        for i in range(6,16): hand.update(None,i/10,hand_present=False)
        self.assertFalse(hand.armed)
        self.assertFalse(hand.update(True,1.6))
        self.assertFalse(hand.update(True,2.1))

    def test_ambiguous_hand_or_unknown_signal_breaks_absence_continuity(self):
        for present in (True,None):
            with self.subTest(hand_present=present):
                hand=self.paused()
                for i in range(6,14): hand.update(None,i/10,hand_present=False)
                hand.update(None,1.4,hand_present=present)
                for i in range(15,23): hand.update(None,i/10,hand_present=False)
                self.assertFalse(hand.armed)

    def test_invalidated_or_sparse_observations_do_not_arm(self):
        for invalidate in (False,True):
            with self.subTest(invalidate=invalidate):
                hand=self.paused()
                hand.update(None,.6,hand_present=False)
                if invalidate: hand.invalidate()
                hand.update(None,2.,hand_present=False)
                self.assertFalse(hand.armed)

    def test_repeated_or_older_results_do_not_complete_absence(self):
        hand=self.paused(); hand.update(None,.6,hand_present=False)
        for t in (.6,.6,.5,.4,.6):
            self.assertFalse(hand.update(None,t,hand_present=False))
        self.assertFalse(hand.armed)

    def test_visible_lower_and_absence_have_separate_timers(self):
        hand=self.paused()
        for i in range(6,10): hand.update(False,i/10,hand_present=True)
        for i in range(10,19): hand.update(None,i/10,hand_present=False)
        self.assertFalse(hand.armed)
        for i in range(19,21): hand.update(None,i/10,hand_present=False)
        self.assertTrue(hand.armed)

    def test_display_distinguishes_absence_ambiguity_and_unavailable(self):
        self.assertEqual(hand_description(Observation(0.,hand_present=False)),'no detectada')
        self.assertEqual(hand_description(Observation(0.,hand_present=True)),'gesto no claro')
        self.assertEqual(hand_description(Observation(0.)),'no evaluable')
        self.assertEqual(hand_description(Observation(0.,hand_present=True,hand_up=True)),'elevada')
        self.assertEqual(hand_description(Observation(0.,hand_present=True,hand_up=False)),'bajada visible')


if __name__=='__main__': unittest.main()
