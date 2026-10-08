"""Invariantes geométricas y selección. Las coordenadas aquí son artificiales."""
import unittest
from dataclasses import replace
import numpy as np
from tutor.config import Config
from tutor.geometry import head_geometry,eye_geometry,raised_hand,iou
from tutor.vision import PrimaryUser

C=Config()

class HeadTests(unittest.TestCase):
    def setUp(self): self.p=np.array([[0,0],[100,0],[50,40],[50,80],[-20,20],[120,20]],float)
    def test_front_and_scale_translation(self):
        for p in (self.p,self.p*2+300):
            front,m=head_geometry(p,C); self.assertTrue(front); self.assertAlmostEqual(m['pitch_ratio'],.5)
    def test_compensate_roll(self):
        angle=np.deg2rad(25); matrix=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        front,m=head_geometry(self.p@matrix.T,C); self.assertTrue(front); self.assertAlmostEqual(m['roll_deg'],25)
    def test_excessive_roll_unknown(self):
        a=np.deg2rad(50); mat=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
        self.assertIsNone(head_geometry(self.p@mat.T,C)[0])
    def test_turn_and_down_away(self):
        self.p[2]=[90,40]; self.assertFalse(head_geometry(self.p,C)[0])
        self.p[2]=[50,75]; self.assertFalse(head_geometry(self.p,C)[0])
    def test_degenerate_unknown(self):
        self.p[1]=self.p[0]; self.assertIsNone(head_geometry(self.p,C)[0])
        self.assertIsNone(head_geometry(np.full((6,2),np.nan),C)[0])

class EyeTests(unittest.TestCase):
    def mesh(self,height=6,iris=.5):
        p=np.zeros((478,2))
        for start,ids,center,top,bottom in ((10,(33,160,158,133,153,144),468,159,145),(80,(362,385,387,263,373,380),473,386,374)):
            p[list(ids)]=[(start,50),(start+12,50-height),(start+28,50-height),(start+40,50),(start+28,50+height),(start+12,50+height)]
            p[center]=(start+40*iris,50); p[top]=(start+20,50-height); p[bottom]=(start+20,50+height)
        return p
    def test_open_center(self):
        opened,gaze,m=eye_geometry(self.mesh(),C); self.assertTrue(opened); self.assertTrue(gaze); self.assertAlmostEqual(m['ear_right'],.3)
    def test_closed_without_gaze(self):
        opened,gaze,m=eye_geometry(self.mesh(1),C); self.assertFalse(opened); self.assertIsNone(gaze)
    def test_look_side(self):
        opened,gaze,_=eye_geometry(self.mesh(iris=.15),C); self.assertTrue(opened); self.assertFalse(gaze)
    def test_wink_unknown(self):
        p=self.mesh(); small=self.mesh(1); ids=[33,160,158,133,153,144,159,145]; p[ids]=small[ids]
        self.assertIsNone(eye_geometry(p,C)[0])
    def test_iris_outside_unknown(self):
        p=self.mesh(); p[468]=[1000,50]; self.assertIsNone(eye_geometry(p,C)[1])
    def test_scale_rotation_invariant(self):
        p=self.mesh(); a=np.deg2rad(20); matrix=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
        opened,gaze,m=eye_geometry((p@matrix.T)*2,C); self.assertTrue(opened); self.assertTrue(gaze); self.assertAlmostEqual(m['ear_right'],.3)

class PrimaryTests(unittest.TestCase):
    def test_largest_then_lock_even_when_other_grows(self):
        user=PrimaryUser(C); a=(0,0,100,100); b=(200,0,250,50)
        self.assertEqual(user.select([a,b]),0)
        self.assertEqual(user.select([(190,0,400,200),a]),1)
        self.assertIsNone(user.select([b]))
        self.assertEqual(user.select([a]),0)
    def test_empty_and_iou(self):
        self.assertIsNone(PrimaryUser(C).select([])); self.assertEqual(iou((0,0,10,10),(20,20,30,30)),0.)
    def test_invalid_hand(self): self.assertIsNone(raised_hand(np.zeros((2,2)),(0,0,100,100)))

class ConfigTests(unittest.TestCase):
    def test_invalid_values(self):
        for kwargs in ({'sample_s':0},{'width':640.5},{'ear_open':.1},{'gaze_high':1.5},{'warning_s':float('nan')}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError): replace(C,**kwargs).validate()

if __name__=='__main__': unittest.main()
