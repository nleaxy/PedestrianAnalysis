import os
import json
import logging
from uuid import uuid4
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, filters, ContextTypes,
    CommandHandler, ConversationHandler
)
from main import process_video
from generate_report import generate_report

BOT_TOKEN = 'something was there :P'

UPLOAD_FOLDER = 'uploads'
RESULT_JSON_PATH = 'results/results.json'
OUTPUT_VIDEO_PATH = 'output.mp4'

STATE_WAITING_TIMECODE = 1

user_sessions = {}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне видео с пешеходами, и я его обработаю." \
    "\n\nПомощь по командам - /help")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("Обработка отменена.")
    return ConversationHandler.END


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file = message.video or message.document
    if not file:
        await message.reply_text("Пожалуйста, отправь видеофайл.")
        return ConversationHandler.END

    file_id = file.file_id
    telegram_file = await context.bot.get_file(file_id)
    filename = f"{uuid4().hex}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    await telegram_file.download_to_drive(filepath)

    user_sessions[update.effective_user.id] = {
        "filepath": filepath
    }

    await message.reply_text("Видео получено. Укажи начало и конец в секундах, например: `5 13.5`." \
    "\n\nОбработать видео целиком - /continue" \
    "\n\nОтмена текущей сессии - /cancel")
    return STATE_WAITING_TIMECODE


async def continue_full_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text("Сначала отправь видео.")
        return ConversationHandler.END

    filepath = user_sessions[user_id]["filepath"]
    await update.message.reply_text("Начинаю обработку всего видео...")

    try:
        process_video(filepath, output_video_path=OUTPUT_VIDEO_PATH, start_time=None, end_time=None)
    except Exception as e:
        logging.exception("Ошибка при обработке видео:")
        await update.message.reply_text("Произошла ошибка при обработке.")
        return ConversationHandler.END

    if os.path.exists(RESULT_JSON_PATH):
        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        text = format_result_message(data)
        await update.message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)

    else:
        await update.message.reply_text("Результат не найден.")

    del user_sessions[user_id]
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 <b>Инструкция:</b>\n"
        "1. Отправьте мне видео.\n"
        "2. Укажите интервал в секундах, например: <code>5 13.5</code>\n"
        "3. Или отправьте /continue, чтобы обработать всё видео.\n"
        "4. Используйте /cancel, чтобы отменить текущую сессию.",
        parse_mode='HTML'
    )


async def handle_timecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if user_id not in user_sessions:
        await update.message.reply_text("Сначала отправь видео.")
        return ConversationHandler.END

    try:
        start_time, end_time = map(float, message.split())
        if end_time - start_time < 1.0:
            await update.message.reply_text("Минимальный интервал — 1 секунда.")
            return STATE_WAITING_TIMECODE
    except Exception:
        await update.message.reply_text("Неверный формат. Пример: `5 13.5`")
        return STATE_WAITING_TIMECODE

    filepath = user_sessions[user_id]["filepath"]
    await update.message.reply_text("Начинаю обработку...")

    try:
        process_video(filepath, output_video_path=OUTPUT_VIDEO_PATH, start_time=start_time, end_time=end_time)
    except Exception as e:
        logging.exception("Ошибка при обработке видео:")
        await update.message.reply_text("Произошла ошибка при обработке.")
        return ConversationHandler.END

    if os.path.exists(RESULT_JSON_PATH):
        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        text = format_result_message(data)
        await update.message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)

    else:
        await update.message.reply_text("Результат не найден.")

    del user_sessions[user_id]
    return ConversationHandler.END


def format_result_message(data: dict) -> str:
    lines = []
    lines.append("<b>✅ Обработка успешно завершена.</b>\n")
    lines.append(f"<b>Общее число людей:</b> {data.get('total_unique_people', '?')}\n")

    lines.append("<b>Статистика по направлениям:</b>")
    for direction in ['вверх', 'вниз', 'налево', 'направо']:
        count = data.get('movement_statistics', {}).get(direction, 0)
        lines.append(f"- {direction.capitalize()}: {count}")

    # table of the pedestrians
    person_data = data.get("person_time_data", {})
    directions = data.get("id_directions", {})

    table_lines = []
    table_lines.append("ID  Направление  Время(с)  Вход(с)  Выход(с)")
    for id_str in sorted(person_data.keys(), key=lambda x: int(x)):
        pdata = person_data[id_str]
        dir = directions.get(id_str, "-")
        enter = pdata.get("enter_time", "?")
        exit_ = pdata.get("exit_time", "?")
        duration = pdata.get("time_on_screen", "?")
        row = f"{id_str:<3} {dir:<11} {duration:<9} {enter:<7} {exit_:<7}"
        table_lines.append(row)

    table_block = "\n".join(table_lines)
    lines.append("\n<b>Таблица с пешеходами:</b>")
    lines.append(f"<blockquote expandable>{table_block}</blockquote>")

    return "\n".join(lines)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте видео или напишите /help для помощи по командам.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
        states={
            STATE_WAITING_TIMECODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_timecode)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("continue", continue_full_processing))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_message))  # unknown comamands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))  # text w/o context

    print("Бот запущен.")
    app.run_polling()

generate_report()

if __name__ == '__main__':
    main()


