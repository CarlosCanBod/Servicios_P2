"""Traducir motivos técnicos a indicaciones; este módulo no decide atención ni estados."""
from .signals import Attention
from .dialogue import State


# Describimos lo observado y una acción posible, sin atribuir una causa que el
# detector no mide (por ejemplo, poca luz, gafas o cansancio).
SIGNAL_MESSAGES={
    'inclinacion_excesiva':'Endereza un poco la cabeza para que pueda evaluar tu mirada.',
    'ojos_pequenos':'Acerca un poco el rostro a la cámara para que pueda distinguir los ojos.',
    'puntos_invalidos':'No consigo medir bien tu rostro. Colócate de frente y evita taparte la cara.',
    'geometria_degenerada':'No consigo medir la orientación de tu cabeza. Colócate de frente a la cámara.',
    'sin_cara':'Colócate frente a la cámara, con la cara completa dentro del encuadre.',
    'sin_cara_fiable':'No detecto bien tu cara. Revisa el encuadre y la iluminación.',
    'usuario_principal_perdido':'No localizo la cara seleccionada. Vuelve al encuadre; pulsa r si cambias de persona.',
    'sin_malla_correspondiente':'Veo tu cara, pero no localizo bien los ojos. Mira de frente y evita taparlos.',
    'malla_invalida':'No consigo medir bien tus ojos. Mira de frente y evita cubrirlos.',
    'guino_o_apertura_ambigua':'No distingo bien la apertura de tus ojos. Mantén el rostro visible frente a la cámara.',
    'iris_no_fiable':'No localizo bien tus iris. Mira de frente y evita cubrirte los ojos.',
    'cabeza_desviada':'Orienta la cabeza hacia la cámara para continuar con la lección.',
    'ojos_cerrados':'Detecto los ojos cerrados. Ábrelos y mira al frente para continuar.',
    'mirada_desviada':'Dirige la mirada hacia la cámara para continuar con la lección.',
    'confirmando_atencion':'Mantén la mirada al frente un momento para confirmar la señal.',
    'confirmando_desatencion':'Mantén el rostro y la mirada hacia la cámara mientras compruebo la señal.',
    'percepcion_caducada':'No llegan mediciones recientes. Comprueba que la cámara sigue entregando imágenes.',
    'observacion_desordenada':'Las mediciones han llegado fuera de orden. Espera a que se actualice la imagen.',
    'inicializando':'Estoy preparando los detectores. Espera un momento.',
}
FALLBACK_MESSAGE='No puedo evaluar tu rostro con esta imagen. Revisa el encuadre y la iluminación.'


def signal_guidance(reason, obs=None):
    if reason.startswith('error_vision'):
        return 'Ha fallado el análisis de imagen. Revisa el diagnóstico técnico y reinicia el tutor si persiste.'
    if obs is None and reason=='percepcion_caducada':
        return SIGNAL_MESSAGES['inicializando']
    if reason=='confirmando_desatencion' and obs is not None:
        # La confirmación temporal aún no es una desatención estable. Podemos
        # orientar al alumno según la medida actual sin adelantar ningún aviso.
        if obs.head_front is False: reason='cabeza_desviada'
        elif obs.eyes_open is False: reason='ojos_cerrados'
        elif obs.gaze_front is False: reason='mirada_desviada'
    return SIGNAL_MESSAGES.get(reason,FALLBACK_MESSAGE)


def tutor_message(obs, attention, reason, dialogue):
    """Prioridad visual: descanso/final > contenido tolerado > ayuda según el motivo.

    La tolerancia de 0,5 s ya está aplicada por AttentionFilter: mientras conserve
    atención no sustituimos la lección por instrucciones durante un parpadeo.
    Los avisos por desatención fiable conservan su texto y añaden la corrección.
    """
    if dialogue.state in (State.BREAK,State.GOOD,State.BAD) or attention==Attention.ATTENTIVE:
        return dialogue.message
    guidance=signal_guidance(reason,obs)
    if attention==Attention.AWAY and dialogue.state in (State.MILD,State.CLEAR):
        return f'{dialogue.message} {guidance}'
    return guidance
