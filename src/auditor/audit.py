"""Запуск аудита и формирование отчётов JSON/HTML."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from .checks import ALL_CHECKS, result
from .rules import SEVERITIES, load_rules

COLORS = {"critical": "#b00020", "high": "#e65100", "medium": "#f9a825", "low": "#558b2f"}


def run_audit(project: str | Path, rules_path: str | Path | None = None) -> dict:
    root = Path(project)
    rules, warnings = load_rules(rules_path)
    results: list[dict] = []
    if not root.is_dir():
        results.append(result("project", "files", "critical", False, f"Каталог проекта не найден: {root}"))
    else:
        for check in ALL_CHECKS:
            try:
                results.extend(check(root, rules))
            except Exception as exc:  # noqa: BLE001 - аудитор не должен аварийно завершаться
                results.append(result(check.__name__, "internal", "high", False,
                                      f"Ошибка выполнения проверки: {exc}"))
    for w in warnings:
        results.append(result("rules", "config", "high", False, w))
    failed = [r for r in results if not r["passed"]]
    return {
        "project": str(root),
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "compliant": not failed,
        "summary": {s: sum(r["severity"] == s for r in failed) for s in SEVERITIES},
        "results": results,
        "disclaimer": "Результат аудита не является сертификацией по ISO/IEC/IEEE 828.",
    }


def write_json(report: dict, out: str | Path) -> None:
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_html(report: dict, out: str | Path) -> None:
    rows = "".join(
        f"<tr><td>{'✅' if r['passed'] else '❌'}</td>"
        f"<td style='color:{COLORS[r['severity']]};font-weight:bold'>{r['severity']}</td>"
        f"<td>{html.escape(r['category'])}</td><td>{html.escape(r['rule'])}</td>"
        f"<td>{html.escape(r['message'])}</td></tr>" for r in report["results"])
    verdict = "соответствует" if report["compliant"] else "есть нарушения"
    summ = ", ".join(f"{k}: {v}" for k, v in report["summary"].items())
    Path(out).write_text(
        "<!doctype html><html lang='ru'><meta charset='utf-8'><title>Отчёт аудита</title>"
        "<style>body{font-family:sans-serif;margin:2em}table{border-collapse:collapse}"
        "td,th{border:1px solid #ccc;padding:4px 10px;text-align:left}</style>"
        f"<h1>Аудит конфигурации: {html.escape(report['project'])}</h1>"
        f"<p>Дата: {report['audited_at']}. Итог: <b>{verdict}</b>. Нарушения — {summ}.</p>"
        "<table><tr><th></th><th>Критичность</th><th>Категория</th><th>Правило</th><th>Сообщение</th></tr>"
        f"{rows}</table><p><i>{html.escape(report['disclaimer'])}</i></p></html>",
        encoding="utf-8")
