"""Procesos con buzones de capacidad 1. Un modelo lento no acumula fotogramas."""
import multiprocessing as mp
from pathlib import Path
from queue import Empty, Full
from .signals import Observation


def latest(queue):
    result=None
    while True:
        try: result=queue.get_nowait()
        except Empty: return result


def offer(queue, value):
    """Sustituye el elemento pendiente. Nunca espera a que termine la inferencia."""
    try: queue.put_nowait(value)
    except Full:
        try: queue.get_nowait()
        except Empty: return False
        try: queue.put_nowait(value)
        except Full: return False
    return True


def vision_worker(config, inbox, outbox):
    from .vision import Perception
    perception=None
    try:
        perception=Perception(config)
        outbox.put(('ready',None))
        while True:
            packet=inbox.get()
            if packet is None: break
            frame,t,user=packet
            try:
                obs,crop=perception.process(frame,t,user)
            except Exception as exc:
                obs=Observation(t,user_id=user,reason=f'error_vision: {type(exc).__name__}: {exc}'); crop=None
            offer(outbox,('result',(obs,crop)))
    except Exception as exc:
        offer(outbox,('error',f'{type(exc).__name__}: {exc}'))
    finally:
        if perception: perception.close()


class Worker:
    def __init__(self, target, args=()):
        ctx=mp.get_context('spawn')
        self.inbox=ctx.Queue(maxsize=1); self.outbox=ctx.Queue(maxsize=1)
        self.process=ctx.Process(target=target,args=(*args,self.inbox,self.outbox),daemon=True)
        self.process.start()
        self.ready=False; self.error=None

    def receive(self):
        packet=latest(self.outbox)
        if packet:
            kind,data=packet
            if kind=='ready': self.ready=True
            elif kind=='error': self.error=data
            else: return data
        if not self.process.is_alive() and self.error is None:
            self.error=f'Proceso detenido (código {self.process.exitcode})'
        return None

    def submit(self, value): return offer(self.inbox,value)

    def close(self):
        offer(self.inbox,None)
        self.process.join(timeout=0.5)
        if self.process.is_alive():
            self.process.terminate(); self.process.join(timeout=1.)
        # No esperar al feeder de una cola cuyo receptor acaba de terminar.
        for queue in (self.inbox,self.outbox):
            queue.cancel_join_thread(); queue.close()


class ExpressionWorker:
    """Subproceso con intérprete propio y dos hilos para que las tuberías no bloqueen UI."""
    def __init__(self, executable):
        import subprocess
        from threading import Thread
        from queue import Queue
        from .config import ROOT
        if not Path(executable).is_file(): raise FileNotFoundError(f'Intérprete no encontrado: {executable}')
        self.inbox=Queue(maxsize=1); self.outbox=Queue(maxsize=1)
        self.process=subprocess.Popen([str(executable),'-m','tutor.expression_service'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,cwd=ROOT)
        self.ready=False; self.error=None; self.closed=False
        self.sender=Thread(target=self._send,daemon=True); self.reader=Thread(target=self._read,daemon=True)
        self.sender.start(); self.reader.start()

    def _send(self):
        from .protocol import write_packet
        try:
            while True:
                packet=self.inbox.get(); write_packet(self.process.stdin,packet)
                if packet is None: return
        except (OSError,ValueError):
            if not self.closed: offer(self.outbox,('error','El proceso de expresión cerró su entrada'))

    def _read(self):
        from .protocol import read_packet
        try:
            while True: offer(self.outbox,read_packet(self.process.stdout))
        except (EOFError,OSError,ValueError):
            if not self.closed: offer(self.outbox,('error','El proceso de expresión cerró su salida'))

    def receive(self):
        packet=latest(self.outbox)
        if packet:
            kind,data=packet
            if kind=='ready': self.ready=True
            elif kind=='error': self.error=data
            else: return data
        if self.process.poll() is not None and not self.closed and self.error is None:
            self.error=f'Proceso de expresión detenido ({self.process.returncode})'
        return None

    def submit(self, value): return offer(self.inbox,value)

    def close(self):
        import subprocess
        self.closed=True; offer(self.inbox,None)
        try: self.process.wait(timeout=.5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try: self.process.wait(timeout=1.)
            except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(timeout=1.)
        self.sender.join(timeout=.2); self.reader.join(timeout=.2)
        for stream in (self.process.stdin,self.process.stdout):
            stream.close()
