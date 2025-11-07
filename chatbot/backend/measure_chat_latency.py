import requests, time, json

url = 'http://127.0.0.1:8000/chat'
msgs = [
    '¿Cuál es vuestro horario?',
    '¿Cómo puedo hacer una reserva para mañana?',
    '¿Tenéis menú sin gluten?',
    '¿Hay parking?',
    '¿Qué tipo de membresías tenéis?',
    '¿Cuál es la dirección?'
]

for m in msgs:
    payload = {'business_id': 2, 'session_id': 'latency-test', 'message': m}
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, timeout=60)
        elapsed = time.time() - t0
        status = r.status_code
        try:
            data = r.json()
            resp = data.get('response', '')
        except Exception:
            resp = r.text
        print(f"msg={m!r} status={status} time={elapsed:.2f}s response_preview={resp[:120]!r}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"msg={m!r} ERROR time={elapsed:.2f}s error={e}")
