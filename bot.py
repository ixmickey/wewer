
import telebot
import sqlite3
from config import TELEGRAM_TOKEN

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    data = call.data

    if data.startswith("approve_"):
        request_id = data.split("_")[1]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE requests SET status='Approved' WHERE id=?", (request_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "Approved")
        bot.edit_message_text(
            "✅ Request Approved",
            call.message.chat.id,
            call.message.message_id
        )

    elif data.startswith("reject_"):
        request_id = data.split("_")[1]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE requests SET status='Rejected' WHERE id=?", (request_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "Rejected")
        bot.edit_message_text(
            "❌ Request Rejected",
            call.message.chat.id,
            call.message.message_id
        )

bot.infinity_polling()
