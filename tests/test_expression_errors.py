"""Errores simulados del adaptador; estas pruebas no cargan ni evalúan la red."""
import unittest
import numpy as np
from tutor.expression import ExpressionDetector

class BrokenModel:
    def analyze(self,*args,**kwargs): raise RuntimeError('fallo controlado')

class InvalidScores:
    def analyze(self,*args,**kwargs): return [{'emotion':{'happy':float('nan')},'dominant_emotion':'happy'}]

class ExpressionErrorTests(unittest.TestCase):
    def detector(self,backend):
        detector=ExpressionDetector.__new__(ExpressionDetector); detector.deepface=backend
        return detector
    def test_model_error_is_explicit(self):
        result=self.detector(BrokenModel()).analyze(np.zeros((20,20,3),dtype=np.uint8),1.,4)
        self.assertIsNone(result.label); self.assertIn('fallo controlado',result.error); self.assertEqual(result.user_id,4)
    def test_empty_crop(self):
        result=self.detector(BrokenModel()).analyze(None,1.,4)
        self.assertIn('Recorte vacío',result.error)
    def test_invalid_output_does_not_create_smile(self):
        result=self.detector(InvalidScores()).analyze(np.zeros((20,20,3),dtype=np.uint8),1.,4)
        self.assertEqual(result.scores,{}); self.assertIsNone(result.label); self.assertIsNotNone(result.error)

if __name__=='__main__': unittest.main()
