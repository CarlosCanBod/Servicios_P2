"""Errores simulados del adaptador; estas pruebas no cargan ni evalúan la red."""
import unittest
import numpy as np
from tutor.expression import ExpressionDetector

class BrokenModel:
    def analyze(self,*args,**kwargs): raise RuntimeError('fallo controlado')

class InvalidScores:
    def analyze(self,*args,**kwargs): return [{'emotion':{'happy':float('nan')},'dominant_emotion':'happy'}]

class MissingHappy:
    def analyze(self,*args,**kwargs): return [{'emotion':{'neutral':100.},'dominant_emotion':'neutral'}]

class MissingAnotherClass:
    def analyze(self,*args,**kwargs):
        return [{'emotion':{'happy':30.,'neutral':70.},'dominant_emotion':'neutral'}]

class InvalidSum:
    def analyze(self,*args,**kwargs):
        return [{'emotion':{key:0. for key in ('angry','disgust','fear','happy','sad','surprise','neutral')},
                 'dominant_emotion':'neutral'}]

class ValidScores:
    def analyze(self,*args,**kwargs):
        return [{'emotion':{'angry':0.,'disgust':0.,'fear':0.,'happy':30.,'sad':0.,'surprise':0.,'neutral':70.},
                 'dominant_emotion':'neutral'}]

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
    def test_output_without_happiness_is_reported_as_error(self):
        result=self.detector(MissingHappy()).analyze(np.zeros((20,20,3),dtype=np.uint8),1.,4)
        self.assertEqual(result.scores,{}); self.assertIsNotNone(result.error)
    def test_output_with_missing_class_or_invalid_sum_is_error(self):
        for model in (MissingAnotherClass(),InvalidSum()):
            with self.subTest(model=type(model).__name__):
                result=self.detector(model).analyze(np.zeros((20,20,3),dtype=np.uint8),1.,4)
                self.assertEqual(result.scores,{}); self.assertIsNotNone(result.error)
    def test_valid_distribution_is_returned(self):
        result=self.detector(ValidScores()).analyze(np.zeros((20,20,3),dtype=np.uint8),1.,4)
        self.assertIsNone(result.error); self.assertEqual(result.label,'neutral'); self.assertAlmostEqual(result.scores['happy'],.3)

if __name__=='__main__': unittest.main()
