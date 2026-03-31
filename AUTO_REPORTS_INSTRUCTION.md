# 🔧 АВТОМАТИЧЕСКИЕ ОТЧЕТЫ ПОСЛЕ МАТЧЕЙ - Инструкция

## Проблема

Бот не отправлял автоматические отчеты после завершения матчей.

### Причины:

1. **`tracked_matches.json` пустой** - матчи не сохранялись при анализе
2. **Бот не запущен** - периодическая проверка не работает
3. **Парсинг прогнозов** - не все вероятности извлекались из AI анализа

---

## ✅ Что исправлено

### 1. Добавлено сохранение прогнозов

**Файл:** `main.py`, метод `_analyze_match()`

Теперь при запросе AI анализа бот:
- Извлекает прогнозы из AI ответа
- Сохраняет в `tracked_matches.json`
- Отслеживает для пост-матч отчета

### 2. Улучшен парсинг прогнозов

**Файл:** `main.py`, метод `_extract_predictions_from_analysis()`

Поддерживаемые форматы:
- `ТБ 2.5: 55%` или `ТБ 2.5 — 55%`
- `Обе забьют: 60%` или `ОЗ: 60%`

### 3. Добавлен явный вывод вероятностей в AI prompt

**Файл:** `ai_analyzer.py`

Теперь AI всегда выводит:
```
📊 ДОП. ВЕРОЯТНОСТИ
ТБ 2.5: XX% | ТМ 2.5: XX%
Обе забьют: XX% | ОЗ нет: XX%
```

---

## 🚀 Как использовать

### Вариант 1: Запустить бота (рекомендуется)

Бот будет автоматически проверять матчи каждые 5 минут:

```bash
cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate
python main.py
```

**Что делает бот:**
1. Пользователь запрашивает анализ матча
2. Бот сохраняет прогноз в `tracked_matches.json`
3. Каждые 5 минут проверяет статус tracked матчей
4. Когда матч завершен (FT/AET/PEN/ET) - отправляет отчет

### Вариант 2: Ручная проверка

Если бот не запущен, можно отправить отчеты вручную:

```bash
cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate
python check_and_send_reports.py
```

**Что делает скрипт:**
1. Проверяет все матчи сегодняшнего дня
2. Для завершенных матчей генерирует отчеты
3. Отправляет отчеты пользователям
4. Обновляет `tracked_matches.json`

---

## 📊 Проверка работы

### 1. Проверить tracked матчи

```bash
python -c "
from match_results_tracker import MatchResultsTracker
tracker = MatchResultsTracker()
print(f'Tracked: {len(tracker.tracked_matches)}')
for mid, m in tracker.tracked_matches.items():
    status = '✅' if m.report_sent else '⏳'
    print(f'{status} {mid}: {m.home_team} vs {m.away_team}')
"
```

### 2. Проверить статус матча

```bash
python -c "
from api_football_parser import APIFootballParser
import os
from dotenv import load_dotenv
load_dotenv()

parser = APIFootballParser(api_key=os.getenv('API_FOOTBALL_KEY'))
params = {'id': '1537581'}  # Sweden vs Poland
data = parser._make_request('/fixtures', params)

if data and data.get('response'):
    f = data['response'][0]
    print(f\"{f['teams']['home']['name']} vs {f['teams']['away']['name']}\")
    print(f\"Status: {f['fixture']['status']['short']}\")
    print(f\"Score: {f['goals']['home']}:{f['goals']['away']}\")
"
```

### 3. Тест парсинга

```bash
python -c "
import re
analysis = '''
📊 ВЕРОЯТНОСТИ
П1: 45% | X: 28% | П2: 27%

📊 ДОП. ВЕРОЯТНОСТИ
ТБ 2.5: 55% | ТМ 2.5: 45%
Обе забьют: 60% | ОЗ нет: 40%
'''

# 1X2
x2 = re.search(r'П1:\s*(\d+)%\s*\|\s*X:\s*(\d+)%\s*\|\s*П2:\s*(\d+)%', analysis)
print('1X2:', x2.groups() if x2 else 'НЕ найдено')

# ТБ/ТМ
tb = re.search(r'ТБ\s*2\.5[:\s—-]\s*(\d+)%', analysis)
tm = re.search(r'ТМ\s*2\.5[:\s—-]\s*(\d+)%', analysis)
print('ТБ:', tb.groups() if tb else 'НЕ найдено')
print('ТМ:', tm.groups() if tm else 'НЕ найдено')

# ОЗ
oz = re.search(r'Обе\s*забьют[:\s—-]\s*(\d+)%', analysis)
print('ОЗ:', oz.groups() if oz else 'НЕ найдено')
"
```

---

## 📁 Файлы

| Файл | Назначение |
|------|------------|
| `main.py` | Бот с авто-проверкой матчей |
| `check_and_send_reports.py` | Ручная отправка отчетов |
| `tracked_matches.json` | База tracked матчей |
| `match_results_tracker.py` | Генерация отчетов |

---

## 🎯 Пример отчета

```
⚽ **РЕЗУЛЬТАТ МАТЧА**
Sweden 3:2 Poland
🏆 World Cup - Qualification Europe

📊 **ИСХОД 1X2:**
✅ **П1** (прогноз: 41%)
   Фактически: П1 (3:2)

⚽ **ТОТАЛ ГОЛОВ:**
✅ **ТБ 2.5** (прогноз: 65%)
   Фактически: 5 голов

🎯 **ОБЕ ЗАБЬЮТ:**
✅ **Да** (прогноз: 66%)
   Фактически: Да

📈 **ИТОГ:**
✅ 1X2: Верно
✅ Тотал: Верно
✅ ОЗ: Верно

✅ Отличный прогноз! Точность: 100% (3/3)

⚠️ _Ставки — это риск. Прошлые результаты не гарантируют будущие._
```

---

## ⚠️ Важно

### Для работы авто-отчетов нужно:

1. ✅ **Бот должен быть запущен** - `python main.py`
2. ✅ **Периодическая проверка активна** - каждые 5 минут
3. ✅ **Internet connection** - для проверки статуса матчей
4. ✅ **TELEGRAM_BOT_TOKEN** - для отправки отчетов

### Если бот не запущен:

- Матчи все равно tracked'ятся (сохраняются в JSON)
- Отчеты не отправляются автоматически
- Можно отправить вручную: `python check_and_send_reports.py`

---

## 🐛 Troubleshooting

### "tracked_matches.json пустой"

**Причина:** Пользователи не запрашивали анализ, или бот не сохраняет

**Решение:**
1. Проверить, что `_analyze_match()` вызывает `track_match()`
2. Запросить анализ любого матча
3. Проверить JSON файл

### "Матч завершен, но отчет не отправлен"

**Причина:** Бот не запущен или не проверяет матчи

**Решение:**
1. Запустить бота: `python main.py`
2. Или вручную: `python check_and_send_reports.py`

### "Парсинг не работает"

**Причина:** AI выводит формат, отличный от ожидаемого

**Решение:**
1. Проверить prompt в `ai_analyzer.py`
2. Убедиться, что AI выводит "ТБ 2.5: XX%" и "Обе забьют: XX%"
3. Обновить regex в `_extract_predictions_from_analysis()`

---

## 📞 Поддержка

Если отчеты не работают:

1. Проверить логи бота
2. Проверить `tracked_matches.json`
3. Запустить `check_and_send_reports.py` для диагностики

---

**Дата:** 2026-03-31
**Версия:** v1.1.2 (Auto-Reports Fix)
**Статус:** ✅ Готово к работе
