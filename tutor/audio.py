"""Avisos sonoros por evento: un reproductor externo evita esperar en el bucle de visión."""
import shutil
import subprocess
import time
from .config import ROOT

WARNING_PATH=ROOT/'assets/aviso.wav'
PLAYBACK_TIMEOUT_S=3.0


def is_attention_warning(event):
    # Volver de claramente a ligeramente molesto es una recuperación, no un aviso.
    # Tampoco se repite el sonido al volver de un descanso al estado molesto anterior.
    return (event.get('to') in ('ligeramente_molesto','claramente_molesto')
            and event.get('reason') in ('desatencion_persistente','sin_reaccion_visible'))


class WarningSound:
    def __init__(self, enabled=True):
        self.enabled=enabled; self.error=None; self.player=None
        self.requested=0; self.completed=0; self.process=None; self.started=0.; self.pending=False
        self.command=None
        if enabled:
            # Preferir la salida de escritorio; aplay utiliza el dispositivo ALSA por defecto.
            for name in ('pw-play','paplay','aplay'):
                executable=shutil.which(name)
                if executable:
                    self.player=name; self.command=[executable]
                    if name=='aplay': self.command.append('-q')
                    break
            if self.command is None:
                self.error='Audio: no se encuentra pw-play, paplay ni aplay. Puedes usar --no-sound.'

    def poll(self):
        """Comprueba el proceso sin esperar; un error de audio no detiene la lección."""
        if self.process is None: return
        code=self.process.poll()
        if code is None:
            if not self.error and time.monotonic()-self.started>PLAYBACK_TIMEOUT_S:
                self.error='Audio: el reproductor no terminó en 3 segundos'
                self.process.terminate()
            return
        # Con el proceso ya terminado, communicate recoge stderr sin esperar al sonido.
        _,stderr=self.process.communicate(); self.process=None
        if code==0: self.completed+=1
        elif not self.error: self.error=f'Audio: {self.player} terminó con código {code}: {stderr.strip()[:500]}'
        if self.pending and not self.error:
            self.pending=False
            self._start()

    def _start(self):
        if not WARNING_PATH.is_file():
            self.error=f'Audio: no se encuentra {WARNING_PATH.name}'
            return False
        try:
            self.process=subprocess.Popen([*self.command,str(WARNING_PATH)],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            self.started=time.monotonic()
            return True
        except OSError as exc:
            self.error=f'Audio: {exc}'
            return False

    def play(self):
        self.poll()
        if not self.enabled or self.error: return False
        if self.process is not None:
            # Una sola petición pendiente conserva el segundo aviso sin crear
            # una cola de sonidos atrasados si la salida de audio es lenta.
            if self.pending: return False
            self.pending=True; self.requested+=1
            return True
        if self._start():
            self.requested+=1
            return True
        return False

    def on_event(self, event):
        """La aplicación llama una vez por transición, nunca por fotograma o texto visible."""
        return self.play() if is_attention_warning(event) else False

    def close(self):
        self.pending=False
        self.poll()
        if self.process is not None:
            self.process.terminate()
            try: self.process.communicate(timeout=.5)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.communicate(timeout=.5)
            self.process=None

    def summary(self):
        return {'enabled':self.enabled,'player':self.player,'requested':self.requested,
                'completed':self.completed,'error':self.error}


def test_sound():
    """Prueba manual del altavoz sin iniciar la cámara ni los modelos de percepción."""
    sound=WarningSound()
    try:
        if sound.play():
            while sound.process is not None and not sound.error:
                sound.poll(); time.sleep(.02)
        if sound.error:
            print(sound.error)
            return 2
        print('Reproducción completada. Comprueba que hayas oído dos pitidos.')
        return 0
    finally:
        sound.close()
