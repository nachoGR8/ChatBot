"""Mide la latencia del chat contra un servidor en marcha (solo librería estándar).

Uso:
    python scripts/bench.py --business 1 "¿Quién es Ignacio?" "¿Qué tecnologías usa?"

Cada pregunta se envía dos veces con sesiones nuevas: la 2.ª muestra el efecto de la caché.
Mide el tiempo hasta el primer trozo de texto (lo que el usuario espera mirando la pantalla) y el total.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
import uuid

DEFAULT_QUESTIONS = ["¿Quién es?", "¿Qué estudios tiene?", "¿Qué tecnologías usa?"]


def ask(url: str, business_id: int, question: str) -> dict:
    body = json.dumps(
        {"business_id": business_id, "session_id": f"bench-{uuid.uuid4().hex[:8]}", "message": question}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/chat/stream", data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    start = time.perf_counter()
    first = None
    final = ""
    with urllib.request.urlopen(req, timeout=600) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            event = json.loads(line[5:])
            if first is None and (event.get("delta") or event.get("final")):
                first = time.perf_counter() - start
            if "final" in event:
                final = event["final"]
    return {"first": first or 0.0, "total": time.perf_counter() - start, "answer": final}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("questions", nargs="*", default=DEFAULT_QUESTIONS)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--business", type=int, default=1)
    args = parser.parse_args()

    print(f"{'pregunta':<40} {'intento':>7} {'1ª palabra':>11} {'total':>8}")
    rows = []
    for question in args.questions:
        for attempt in (1, 2):
            r = ask(args.url, args.business, question)
            rows.append(r)
            print(f"{question[:40]:<40} {attempt:>7} {r['first']:>10.1f}s {r['total']:>7.1f}s")
        print(f"    → {r['answer'][:110]}")

    firsts = [r["first"] for r in rows[::2]]
    print(f"\nMedia 1ª palabra (sin caché): {sum(firsts) / len(firsts):.1f}s")


if __name__ == "__main__":
    main()
