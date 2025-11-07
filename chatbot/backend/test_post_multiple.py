import requests
import json

url = 'http://127.0.0.1:8000/chat'
messages = [
    (2, 'test-session-1', '¿Cuál es vuestro horario?'),
    (2, 'test-session-1', '¿Tenéis menú sin gluten?'),
    (2, 'test-session-1', '¿Cómo puedo hacer una reserva?'),
    (2, 'test-session-1', '¿Tenéis parking?'),
    (2, 'test-session-1', '¿Aceptáis perros en el local?'),
    (1, 'test-session-2', '¿Cómo me hago socio?'),
    (1, 'test-session-2', '¿Tenéis Wifi?'),
    (1, 'test-session-2', '¿Puedo traer mi propio entrenador?'),
    (999, 'test-session-3', '¿Esto falla?')  # negocio inexistente para probar 404
]

for business_id, session_id, message in messages:
    payload = {'business_id': business_id, 'session_id': session_id, 'message': message}
    print('\n---')
    print(f'Sending to business {business_id}: "{message}"')
    try:
        r = requests.post(url, json=payload, timeout=60)
        print('status_code=', r.status_code)
        try:
            print(json.dumps(r.json(), ensure_ascii=False, indent=2))
        except Exception:
            print('raw_text=', r.text)
    except requests.exceptions.HTTPError as he:
        print('HTTP ERROR', he)
    except Exception as e:
        print('ERROR', e)
