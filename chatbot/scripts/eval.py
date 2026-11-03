"""Evaluación automática del chatbot contra un servidor en marcha (solo librería estándar).

Uso:
    python scripts/eval.py --business 1 --out eval/results.md

Cada caso de eval/cases.json se envía a /chat/stream y se comprueba:
  - respuesta no vacía y de longitud razonable
  - sin texto prohibido (restos de plantilla, filtraciones del prompt...)
  - tercera persona (sin "yo/mi/mis" tomados del CV)
  - al menos una palabra esperada (si el caso la define)
Genera una tabla Markdown con aciertos y latencias, y termina con código 1 si algún caso falla.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import ask  # noqa: E402

FIRST_PERSON = re.compile(r"\b(yo|mi|mis|soy|tengo|trabajo|estudié)\b", re.IGNORECASE)


def check(case: dict, defaults: dict, answer: str) -> list[str]:
    problems = []
    if not answer.strip():
        return ["respuesta vacía"]
    if len(answer.split()) > case.get("max_words", defaults["max_words"]):
        problems.append("demasiado larga")
    lowered = answer.lower()
    for bad in defaults["forbid"] + case.get("forbid_extra", []):
        if bad.lower() in lowered:
            problems.append(f"contiene «{bad}»")
    if defaults.get("third_person") and FIRST_PERSON.search(answer):
        problems.append("primera persona")
    expected = case.get("expect_any") or []
    if expected and not any(word.lower() in lowered for word in expected):
        problems.append(f"falta alguna de {expected}")
    return problems


def server_model(url: str) -> str:
    try:
        with urllib.request.urlopen(f"{url}/status", timeout=10) as resp:
            data = json.load(resp)
        return str(data.get("model_name") or data.get("model") or data.get("backend") or "desconocido")
    except Exception:
        return "desconocido"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--business", type=int, default=1)
    parser.add_argument("--cases", default=str(Path(__file__).resolve().parents[1] / "eval" / "cases.json"))
    parser.add_argument("--out", help="Guarda el informe Markdown en este fichero")
    args = parser.parse_args()

    spec = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    defaults = spec["defaults"]
    rows, passed = [], 0
    for case in spec["cases"]:
        result = ask(args.url, args.business, case["question"])
        problems = check(case, defaults, result["answer"])
        passed += not problems
        rows.append((case, result, problems))
        print(f"{'OK ' if not problems else 'FAIL'} {case['id']:<16} {result['first']:>5.1f}s {result['total']:>5.1f}s {'; '.join(problems)}")

    total = len(rows)
    avg_first = sum(r[1]["first"] for r in rows) / total
    avg_total = sum(r[1]["total"] for r in rows) / total
    lines = [
        "# Resultados de evaluación",
        "",
        f"- Modelo: `{server_model(args.url)}`",
        f"- Aciertos: **{passed}/{total}** ({passed / total:.0%})",
        f"- Latencia media: 1.ª palabra {avg_first:.1f}s · total {avg_total:.1f}s",
        "",
        "| Caso | Resultado | 1.ª palabra | Total | Detalle |",
        "|---|---|---|---|---|",
    ]
    for case, result, problems in rows:
        detail = "; ".join(problems) or result["answer"].replace("|", "/").replace("\n", " ")[:90]
        lines.append(f"| {case['id']} | {'✅' if not problems else '❌'} | {result['first']:.1f}s | {result['total']:.1f}s | {detail} |")
    report = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
    print(f"\n{passed}/{total} correctos")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
