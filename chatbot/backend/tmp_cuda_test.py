import os
import traceback
from gpt4all import GPT4All

print('Instanciando modelo de prueba...')

# Intentar dispositivo preferido (si se define) y, si falla, hacer fallback a CPU
preferred = os.getenv('GPT4ALL_DEVICE', 'cuda')
devices = [preferred]
if preferred.lower() != 'cpu':
    devices.append('cpu')

for device in devices:
    try:
        print(f"Intentando inicializar en dispositivo: {device}...")
        m = GPT4All('orca-mini-3b-gguf2-q4_0.gguf', device=device, allow_download=False)
        print('backend:', getattr(m, 'backend', 'N/A'))
        print('device:', getattr(m, 'device', 'N/A'))
        m.close()
        print('Instancia cerrada')
        break
    except Exception as e:
        print(f'ERROR instanciando con {device}:', e)
        traceback.print_exc()
else:
    print('No se pudo inicializar el modelo en ninguno de los dispositivos probados.')
