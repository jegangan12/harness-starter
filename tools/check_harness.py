#!/usr/bin/env python3
"""Проверка целостности harness. Единственная проверка стартера.

Падает (код 1), если:
  - нет одного из трёх файлов контракта
  - feature_list.json невалиден или без обязательных полей
  - статус вне разрешённых
  - больше одной фичи in_progress
  - у фичи passing пустое evidence или файл доказательства отсутствует
  - в AGENTS.md остались незаполненные <плейсхолдеры> в блоке команд

Запуск из корня проекта: python3 tools/check_harness.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []

def need(path):
    if not os.path.exists(os.path.join(ROOT, path)):
        errors.append(f"нет файла контракта: {path}")

for f in ("AGENTS.md", "CURRENT_STATE.md", "plans/feature_list.json"):
    need(f)

fl_path = os.path.join(ROOT, "plans/feature_list.json")
if os.path.exists(fl_path):
    try:
        data = json.load(open(fl_path, encoding="utf-8"))
    except Exception as e:
        errors.append(f"feature_list.json невалиден: {e}")
        data = None
    if data:
        allowed = set(data.get("statuses", []))
        if not allowed:
            errors.append("в feature_list.json нет списка statuses")
        feats = data.get("features", [])
        in_progress = [x.get("id") for x in feats if x.get("status") == "in_progress"]
        if len(in_progress) > 1:
            errors.append(f"больше одной фичи in_progress: {in_progress}")
        for x in feats:
            fid = x.get("id", "?")
            for k in ("id", "title", "behavior", "verify", "status"):
                if not x.get(k):
                    errors.append(f"{fid}: пустое обязательное поле {k}")
            if allowed and x.get("status") not in allowed:
                errors.append(f"{fid}: статус {x.get('status')!r} вне разрешённых {sorted(allowed)}")
            if x.get("status") == "passing":
                ev = (x.get("evidence") or "").strip()
                if not ev:
                    errors.append(f"{fid}: passing без evidence - запрещено")
                elif not ev.startswith("http") and not os.path.exists(os.path.join(ROOT, ev)):
                    errors.append(f"{fid}: файл доказательства не найден: {ev}")

ag_path = os.path.join(ROOT, "AGENTS.md")
if os.path.exists(ag_path):
    text = open(ag_path, encoding="utf-8").read()
    m = re.search(r"```bash\n(.*?)```", text, re.S)
    if m and re.search(r"<[^>\n]+>", m.group(1)):
        # Допускаем плейсхолдеры только в нетронутом шаблоне (F-001 not_started и название в скобках)
        untouched = os.path.exists(fl_path) and data and data.get("project", "").startswith("<")
        if not untouched:
            errors.append("в AGENTS.md в блоке команд остались <плейсхолдеры> - замени на реальные команды")

if errors:
    print("HARNESS FAIL")
    for e in errors:
        print("  -", e)
    sys.exit(1)

print("HARNESS OK")
sys.exit(0)
