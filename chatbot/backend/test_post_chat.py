import requests
import json

url = 'http://127.0.0.1:8000/chat'
payload = {
    'business_id': 2,
    'session_id': 'test-session-1',
    'message': '¿Cuál es vuestro horario?'
}

try:
    r = requests.post(url, json=payload, timeout=60)
    print('status_code=', r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    except Exception:
        print('raw_text=', r.text)
except Exception as e:
    print('ERROR', e)
