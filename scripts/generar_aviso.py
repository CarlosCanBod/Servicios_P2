"""Genera un aviso propio: dos tonos breves separados por silencio, sin grabación."""
from array import array
import math
from pathlib import Path
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
SAMPLE_RATE=44100       # Muestras por segundo; WAV PCM mono de 16 bits.
FREQUENCY_HZ=880
TONE_S=0.18
GAP_S=0.12
FADE_S=0.005            # Entrada/salida suaves para evitar clics en los extremos.
AMPLITUDE=0.20          # Fracción del máximo digital; el volumen final es el del sistema.


def create_warning(path):
    length=round(TONE_S*SAMPLE_RATE); fade=round(FADE_S*SAMPLE_RATE)
    tone=array('h')
    for n in range(length):
        envelope=min(1.,n/fade,(length-1-n)/fade)
        value=32767*AMPLITUDE*envelope*math.sin(2*math.pi*FREQUENCY_HZ*n/SAMPLE_RATE)
        tone.append(round(value))
    samples=tone+array('h',[0])*round(GAP_S*SAMPLE_RATE)+tone
    if sys.byteorder!='little': samples.byteswap()
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(SAMPLE_RATE)
        output.writeframes(samples.tobytes())
    return path

if __name__=='__main__':
    print(create_warning(ROOT/'assets/aviso.wav'))
