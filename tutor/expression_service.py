"""Entrada del proceso independiente. No hereda sys.path del entorno de visión."""
from contextlib import redirect_stdout
import sys
from .protocol import read_packet, write_packet


def main():
    transport=sys.stdout.buffer
    # DeepFace escribe algunos avisos en stdout. Reservamos el canal binario
    # y enviamos los mensajes de biblioteca a stderr para no corromperlo.
    with redirect_stdout(sys.stderr):
        try:
            from .expression import ExpressionDetector
            detector=ExpressionDetector(); write_packet(transport,('ready',None))
            while True:
                packet=read_packet(sys.stdin.buffer)
                if packet is None: break
                crop,t,user=packet
                write_packet(transport,('result',detector.analyze(crop,t,user)))
        except EOFError: return
        except Exception as exc:
            write_packet(transport,('error',f'{type(exc).__name__}: {exc}'))

if __name__=='__main__': main()
