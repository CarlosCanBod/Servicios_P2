"""Transporte binario interno entre procesos propios; no acepta archivos externos."""
import pickle
import struct

def read_exact(stream, size):
    parts=[]
    while size:
        part=stream.read(size)
        if not part: raise EOFError('Proceso cerrado durante la lectura')
        parts.append(part); size-=len(part)
    return b''.join(parts)

def read_packet(stream):
    size=struct.unpack('!I',read_exact(stream,4))[0]
    if size>16*1024*1024: raise ValueError('Paquete interno demasiado grande')
    return pickle.loads(read_exact(stream,size))

def write_packet(stream, value):
    payload=pickle.dumps(value,protocol=5)
    stream.write(struct.pack('!I',len(payload))); stream.write(payload); stream.flush()
