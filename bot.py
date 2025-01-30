import datetime
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.warnings import PTBUserWarning
import warnings

warnings.filterwarnings("ignore", category=PTBUserWarning)

AWAITING_TASK = 1

TASKS_FILE = "tasks.json"

if os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "r", encoding="utf-8") as file:
        tasks_by_user = json.load(file)
else:
    tasks_by_user = {}

def get_current_date_info():
    """Returns current weekday and date in Russian"""
    weekdays = {
        0: 'Понедельник',
        1: 'Вторник',
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
        6: 'Воскресенье'
    }
    now = datetime.datetime.now()
    weekday = weekdays[now.weekday()]
    date = now.strftime("%d.%m.%Y")
    return weekday, date

def save_tasks_to_file():
    """Save tasks to JSON file"""
    with open(TASKS_FILE, "w", encoding="utf-8") as file:
        json.dump(tasks_by_user, file, ensure_ascii=False, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    keyboard = [
        [
            InlineKeyboardButton("Создать на сегодня", callback_data='create_today'),
            InlineKeyboardButton("Список на сегодня", callback_data='list_today')
        ],
        [
            InlineKeyboardButton("Создать на неделю", callback_data='create_week'),
            InlineKeyboardButton("Список на неделю", callback_data='list_week')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Выбери внизу необходимые команды и продуктивного тебе дня <3",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline keyboard buttons"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)  

    if query.data == 'create_today':
        weekday, date = get_current_date_info()
        keyboard = [
            [
                InlineKeyboardButton("Создать дела", callback_data='create_task'),
                InlineKeyboardButton("Вернуться назад", callback_data='back_to_start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"{weekday}, {date}",
            reply_markup=reply_markup
        )
    
    elif query.data == 'create_task':
        await query.edit_message_text("Введите ваше дельце и не откладывайте его!")
        return AWAITING_TASK
    
    elif query.data == 'back_to_start':
        keyboard = [
            [
                InlineKeyboardButton("Создать на сегодня", callback_data='create_today'),
                InlineKeyboardButton("Список на сегодня", callback_data='list_today')
            ],
            [
                InlineKeyboardButton("Создать на неделю", callback_data='create_week'),
                InlineKeyboardButton("Список на неделю", callback_data='list_week')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Привет! Выбери внизу необходимые команды и продуктивного тебе дня <3",
            reply_markup=reply_markup
        )
    
    elif query.data == 'list_today':
        weekday, date = get_current_date_info()
        user_tasks = tasks_by_user.get(user_id, {})  
        tasks = user_tasks.get(date, [])  
        if tasks:
            tasks_text = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))
            message = f"{weekday}, {date}\nВаши дела:\n{tasks_text}"
        else:
            message = f"{weekday}, {date}\nНа сегодня дел нет!"
        
        keyboard = [
            [
                InlineKeyboardButton("Создать дела", callback_data='create_task'),
                InlineKeyboardButton("Вернуться назад", callback_data='back_to_start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

async def handle_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for task input"""
    task_text = update.message.text
    weekday, date = get_current_date_info()
    user_id = str(update.message.from_user.id)  

    if user_id not in tasks_by_user:
        tasks_by_user[user_id] = {}

    if date not in tasks_by_user[user_id]:
        tasks_by_user[user_id][date] = []
    tasks_by_user[user_id][date].append(task_text)

    save_tasks_to_file()

    tasks = tasks_by_user[user_id][date]
    tasks_text = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))
    message = f"{weekday}, {date}\nВаши дела:\n{tasks_text}"

    keyboard = [
        [
            InlineKeyboardButton("Создать еще дела", callback_data='create_task'),
            InlineKeyboardButton("Вернуться к началу", callback_data='back_to_start')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)
    return ConversationHandler.END

def main():
    application = Application.builder().token("7039799375:AAEIx9bc0yfgpjfhzEPsqnoT-f2DzEziyl8").build()
    application.add_handler(CommandHandler('start', start))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^create_task$')],
        states={
            AWAITING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_input)]
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)

    application.add_handler(CallbackQueryHandler(button_handler))

    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("Bot stopped!")

if __name__ == '__main__':
    main()
