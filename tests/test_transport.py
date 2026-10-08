"""Verifica el canal de expresión con un recorte artificial (sin inferir)."""
from io import BytesIO
import unittest
import numpy as np
from tutor.protocol import read_packet,write_packet
from tutor.signals import Expression

class FragmentedStream(BytesIO):
    def read(self,size=-1): return super().read(min(size,3))

class TransportTests(unittest.TestCase):
    def test_fragmented_image_packet(self):
        stream=FragmentedStream(); crop=np.arange(300,dtype=np.uint8).reshape(10,10,3)
        write_packet(stream,(crop,1.25,4)); stream.seek(0)
        received,t,user=read_packet(stream)
        np.testing.assert_array_equal(crop,received); self.assertEqual((t,user),(1.25,4))
    def test_expression_and_shutdown(self):
        stream=BytesIO(); write_packet(stream,Expression(2.,3,{'happy':.4},'neutral')); write_packet(stream,None); stream.seek(0)
        expression=read_packet(stream); self.assertEqual(expression.user_id,3); self.assertIsNone(read_packet(stream))
    def test_truncated_packet(self):
        with self.assertRaises(EOFError): read_packet(BytesIO(b'\x00\x00'))

if __name__=='__main__': unittest.main()
