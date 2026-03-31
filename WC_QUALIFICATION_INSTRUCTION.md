# ⚽ Квалификация ЧМ 2026 в боте - ИНСТРУКЦИЯ

## ✅ Что сделано

Бот обновлён до версии **v1.1.0** с полной поддержкой квалификации Чемпионата Мира 2026!

### Изменения:
1. ✅ Добавлены 7 лиг квалификации ЧМ
2. ✅ Исправлена логика определения сезона для квалификаций
3. ✅ Обновлена загрузка формы национальных сборных
4. ✅ Квалификации добавлены в меню выбора дат и лиг
5. ✅ Изменения закоммичены и запушены в git

---

## 🚀 КАК ЗАПУСТИТЬ

### Вариант 1: Быстрый запуск (рекомендуется)

```bash
cd /Users/ilyailyx/Desktop/sports-analytics-bot
./run_bot.sh
```

### Вариант 2: Ручной запуск

```bash
# 1. Перейдите в директорию бота
cd /Users/ilyailyx/Desktop/sports-analytics-bot

# 2. Активируйте виртуальное окружение
source venv/bin/activate

# 3. Очистите кэш (если нужно)
python -c "from api_football_parser import APIFootballParser; p = APIFootballParser('08c6e6aeaf97abc445440c686ac50fab'); p._season_cache.clear()"

# 4. Проверьте, что квалификации работают
python verify_wc_qualification.py

# 5. Запустите бота
python main.py
```

---

## 📱 КАК ИСПОЛЬЗОВАТЬ В TELEGRAM

1. **Откройте бота** в Telegram

2. **Нажмите** "📅 Анализ матча"

3. **Выберите** "⚽ Футбол"

4. **Выберите дату:**
   - Вы увидите **"Сегодня (4)"** ← 4 матча квалификации!
   - Нажмите на эту кнопку

5. **Выберите лигу:**
   - Прокрутите вниз до секции "World Cup Qualifications 2026"
   - Выберите **"🌍 Квалификация ЧМ (Европа) (4)"**

6. **Выберите матч:**
   - Sweden vs Poland
   - Czech Republic vs Denmark
   - Kosovo vs Türkiye
   - Bosnia & Herzegovina vs Italy

7. **Получите анализ** с прогнозом и статистикой!

---

## 📊 Матчи на сегодня (31.03.2026)

| Время | Матч | Статус |
|-------|------|--------|
| 18:45 | 🇸🇪 Sweden vs Poland 🇵🇱 | NS |
| 18:45 | 🇨🇿 Czech Republic vs Denmark 🇩🇰 | NS |
| 18:45 | 🇽🇰 Kosovo vs Türkiye 🇹🇷 | NS |
| 18:45 | 🇧🇦 Bosnia & Herzegovina vs Italy 🇮🇹 | NS |

---

## 🔧 Если что-то не работает

### Проблема: "Сегодня (0)" вместо "Сегодня (4)"

**Решение:**
```bash
# Очистите кэш и перезапустите бота
cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate
python -c "from api_football_parser import APIFootballParser; p = APIFootballParser('08c6e6aeaf97abc445440c686ac50fab'); p._season_cache.clear(); print('Кэш очищен')"
python main.py
```

### Проблема: Не вижу квалификации в списке лиг

**Решение:**
- Убедитесь, что выбрали дату "Сегодня (4)"
- Прокрутите список лиг вниз до секции "World Cup Qualifications 2026"
- Если не видно, перезапустите бота

### Проблема: Бот не запускается

**Решение:**
```bash
# Проверьте, что все зависимости установлены
cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate
pip install -r requirements.txt

# Проверьте переменные окружения
cat .env | grep -E "TELEGRAM|API_FOOTBALL|ANTHROPIC"

# Запустите бота
python main.py
```

---

## 📝 Файлы для удаления (тестовые скрипты)

После проверки можно удалить тестовые файлы:

```bash
cd /Users/ilyailyx/Desktop/sports-analytics-bot
rm -f check_*.py debug_*.py test_*.py verify_*.py clear_cache.py final_*.py
rm -f WC_QUALIFICATION_FIX.md RELEASE_NOTES.md
```

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи бота
2. Запустите `python verify_wc_qualification.py` для проверки
3. Убедитесь, что API ключ действителен

---

**Версия бота:** v1.1.0  
**Дата обновления:** 2026-03-31  
**Статус:** ✅ Готово к production
