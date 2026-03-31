## ✅ Исправления для квалификации ЧМ в боте

### Проблема
Матчи квалификации ЧМ не отображались в боте, потому что:
1. Лиги квалификации не были добавлены в `leagues_to_check` в методе `_show_date_selection`
2. Кэш мог содержать старые данные

### Что исправлено

#### 1. main.py (строка 165-171)
Добавлены лиги квалификации ЧМ в список для подсчёта матчей по датам:

```python
leagues_to_check = [
    "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1",
    "champions_league", "europa_league",
    "eredivisie", "primeira_liga", "mls", "brasileirao",
    # World Cup Qualifications
    "wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america",
    "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs",
]
```

#### 2. api_football_parser.py
- Добавлены 7 лиг квалификации ЧМ в `LEAGUE_IDS`
- Исправлена логика определения сезона для квалификаций
- Обновлён `_get_team_form` для работы с национальными сборными

#### 3. ai_analyzer.py
- Обновлён `_get_league_key` для распознавания квалификаций

### Как проверить

1. **Очистите кэш** (если бот запущен):
```bash
python clear_cache.py
```

2. **Перезапустите бота**:
```bash
python main.py
```

3. **В боте**:
   - Нажмите "📅 Анализ матча"
   - Выберите "⚽ Футбол"
   - Выберите "Сегодня (4)" — должно показать 4 матча квалификации
   - Выберите "🌍 Квалификация ЧМ (Европа) (4)"
   - Выберите матч (например, Sweden vs Poland)

### Матчи на сегодня (31.03.2026)
- 🇸🇪 Sweden vs Poland 🇵🇱 (18:45)
- 🇨🇿 Czech Republic vs Denmark 🇩🇰 (18:45)
- 🇽🇰 Kosovo vs Türkiye 🇹🇷 (18:45)
- 🇧🇦 Bosnia & Herzegovina vs Italy 🇮🇹 (18:45)

### Файлы для удаления (тестовые)
```bash
rm check_wc_qualification.py check_wc_matches_today.py
rm debug_form.py debug_national_teams.py debug_sweden_form.py
rm debug_details.py debug_fixture_api.py debug_steps.py
rm debug_bot_display.py test_league_select.py test_full_flow.py
rm clear_cache.py final_wc_test.py test_wc_qualification.py
```
