import datetime
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.warnings import PTBUserWarning
import warnings

warnings.filterwarnings("ignore", category=PTBUserWarning)

AWAITING_TASK = 1
AWAITING_WEEK_DAY = 2

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

def get_week_range():
    """Returns the start and end dates of the current week"""
    now = datetime.datetime.now()
    start_of_week = now - datetime.timedelta(days=now.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return start_of_week.strftime("%d.%m.%Y"), end_of_week.strftime("%d.%m.%Y")

def get_tasks_for_week(user_id):
    """Returns tasks for the current week, grouped by day"""
    start_of_week, end_of_week = get_week_range()
    start_date = datetime.datetime.strptime(start_of_week, "%d.%m.%Y")
    end_date = datetime.datetime.strptime(end_of_week, "%d.%m.%Y")

    user_tasks = tasks_by_user.get(user_id, {})
    week_tasks = {}

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%d.%m.%Y")
        if date_str in user_tasks:
            week_tasks[date_str] = user_tasks[date_str]
        current_date += datetime.timedelta(days=1)

    return week_tasks

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
            tasks_text = ""
            keyboard = []
            for i, task in enumerate(tasks):
                status = "✅" if task.get("completed", False) else "❌"
                tasks_text += f"{i + 1}. {task['task']} {status}\n"
                keyboard.append([
                    InlineKeyboardButton(f"{i + 1}. {task['task']}", callback_data=f"toggle_{i}")
                ])
            message = f"{weekday}, {date}\nВаши дела:\n{tasks_text}"
        else:
            message = f"{weekday}, {date}\nНа сегодня дел нет!"
            keyboard = []
        
        keyboard.append([
            InlineKeyboardButton("Создать дело", callback_data='create_task'),
            InlineKeyboardButton("Вернуться назад", callback_data='back_to_start')
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif query.data == 'create_week':
        start_week, end_week = get_week_range()
        keyboard = [
            [
                InlineKeyboardButton("Понедельник", callback_data='monday'),
                InlineKeyboardButton("Вторник", callback_data='tuesday'),
                InlineKeyboardButton("Среда", callback_data='wednesday')
            ],
            [
                InlineKeyboardButton("Четверг", callback_data='thursday'),
                InlineKeyboardButton("Пятница", callback_data='friday'),
                InlineKeyboardButton("Суббота", callback_data='saturday'),
                InlineKeyboardButton("Воскресенье", callback_data='sunday')
            ],
            [
                InlineKeyboardButton("Вернуться назад", callback_data='back_to_start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Текущая неделя: {start_week} - {end_week}",
            reply_markup=reply_markup
        )
        return AWAITING_WEEK_DAY

    elif query.data in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        day = query.data
        now = datetime.datetime.now()
        start_of_week = now - datetime.timedelta(days=now.weekday())
        day_offset = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(day)
        selected_day = start_of_week + datetime.timedelta(days=day_offset)
        selected_day_str = selected_day.strftime("%d.%m.%Y")
        
        context.user_data['selected_day'] = selected_day_str  

        keyboard = [
            [
                InlineKeyboardButton("Создать дело", callback_data='create_task_for_day'),
                InlineKeyboardButton("Вернуться назад", callback_data='back_to_start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Выбранный день: {day.capitalize()}, {selected_day_str}",
            reply_markup=reply_markup
        )
        return AWAITING_TASK

    elif query.data == 'create_task_for_day':
        await query.edit_message_text("Введите ваше дельце и не откладывайте его!")
        return AWAITING_TASK

    elif query.data == 'list_week':
        week_tasks = get_tasks_for_week(user_id)
        if week_tasks:
            tasks_text = ""
            for date, tasks in week_tasks.items():
                tasks_text += f"\n{date}:\n"
                for i, task in enumerate(tasks):
                    status = "✅" if task.get("completed", False) else "❌"
                    tasks_text += f"{i + 1}. {task['task']} {status}\n"
            message = f"Ваши дела на неделю:\n{tasks_text}"
        else:
            message = "На этой неделе дел нет!"

        keyboard = [
            [
                InlineKeyboardButton("Вернуться назад", callback_data='back_to_start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif query.data.startswith("toggle_"):
        task_id = int(query.data.split("_")[1])
        selected_day = context.user_data.get('selected_day', get_current_date_info()[1])
        user_tasks = tasks_by_user.get(user_id, {}).get(selected_day, [])

        if 0 <= task_id < len(user_tasks):
            user_tasks[task_id]["completed"] = not user_tasks[task_id].get("completed", False)
            save_tasks_to_file()

        tasks_text = ""
        keyboard = []
        for i, task in enumerate(user_tasks):
            status = "✅" if task.get("completed", False) else "❌"
            tasks_text += f"{i + 1}. {task['task']} {status}\n"
            keyboard.append([
                InlineKeyboardButton(f"{i + 1}. {task['task']}", callback_data=f"toggle_{i}")
            ])
        message = f"День: {selected_day}\nВаши дела:\n{tasks_text}"

        keyboard.append([
            InlineKeyboardButton("Создать еще дело", callback_data='create_task_for_day'),
            InlineKeyboardButton("Вернуться к началу", callback_data='back_to_start')
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

async def handle_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for task input"""
    task_text = update.message.text
    user_id = str(update.message.from_user.id)  

    if 'selected_day' in context.user_data:
        selected_day = context.user_data['selected_day']
    else:
        selected_day = get_current_date_info()[1]  

    if user_id not in tasks_by_user:
        tasks_by_user[user_id] = {}

    if selected_day not in tasks_by_user[user_id]:
        tasks_by_user[user_id][selected_day] = []
    tasks_by_user[user_id][selected_day].append({"task": task_text, "completed": False})

    save_tasks_to_file()

    tasks = tasks_by_user[user_id][selected_day]
    tasks_text = ""
    keyboard = []
    for i, task in enumerate(tasks):
        status = "✅" if task.get("completed", False) else "❌"
        tasks_text += f"{i + 1}. {task['task']} {status}\n"
        keyboard.append([
            InlineKeyboardButton(f"{i + 1}. {task['task']}", callback_data=f"toggle_{i}")
        ])
    message = f"День: {selected_day}\nВаши дела:\n{tasks_text}"

    keyboard.append([
        InlineKeyboardButton("Создать еще дело", callback_data='create_task_for_day'),
        InlineKeyboardButton("Вернуться к началу", callback_data='back_to_start')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)
    return ConversationHandler.END

def main():
    application = Application.builder().token("7039799375:AAEIx9bc0yfgpjfhzEPsqnoT-f2DzEziyl8").build()
    application.add_handler(CommandHandler('start', start))

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern='^create_task$'),
            CallbackQueryHandler(button_handler, pattern='^create_week$'),
            CallbackQueryHandler(button_handler, pattern='^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$'),
            CallbackQueryHandler(button_handler, pattern='^create_task_for_day$')
        ],
        states={
            AWAITING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_input)],
            AWAITING_WEEK_DAY: [CallbackQueryHandler(button_handler)]
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
