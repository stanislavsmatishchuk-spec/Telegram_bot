# Telegram Reminder Bot

Це Telegram-бот для створення та автоматичного надсилання нагадувань у заданий час.  
Проєкт написаний мовою **Python** та використовує **SQLite** для зберігання даних.

---

## Як запустити проєкт

Після завантаження файлів необхідно встановити залежності та запустити бота.

---

## 1. Перевірити Python

Проєкт працює на **Python 3.10 або новішій версії**.

Перевірка версії:

```bash
python3 --version
2. Створити віртуальне середовище
macOS / Linux
python3 -m venv venv
source venv/bin/activate
Windows
python -m venv venv
venv\Scripts\activate
3. Встановити залежності

У папці проєкту виконати:

pip install -r requirements.txt

Без цього бот не запуститься.

4. Створити файл .env

У корені проєкту створити файл .env і вставити:

BOT_TOKEN=your_telegram_bot_token_here

Токен можна отримати через Telegram-бота @BotFather.

5. Запуск бота

У терміналі, в папці проєкту:

python bot.py

Після запуску написати боту в Telegram:

/start
