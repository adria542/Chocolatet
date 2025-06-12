from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import Dispatcher
from datetime import datetime, timedelta
import json
import os
import asyncio

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Datos
DATA_FILE = "cita.json"


def guardar_cita(fecha_str):
    with open(DATA_FILE, "w") as f:
        json.dump({"cita": fecha_str}, f)


def cargar_cita():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f).get("cita")
    return None


# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy un bot creado para Valentina y Adrià. Escribe /set para guardar una cita y /falta para ver cuánto falta 🤍"
    )


async def set_cita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa el formato: /set YYYY-MM-DD HH:MM")
        return

    fecha_str = " ".join(context.args)
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        cita_str = dt.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        guardar_cita(cita_str)
        await update.message.reply_text(f"Cita guardada para: {cita_str}")
    except ValueError:
        await update.message.reply_text("Formato incorrecto. Usa: /set 2025-06-15 20:00")


async def cuanto_falta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cita_str = cargar_cita()
    if not cita_str:
        await update.message.reply_text("No hay ninguna cita guardada.")
        return

    cita = datetime.strptime(cita_str, "%Y-%m-%d %H:%M:%S")
    ahora = datetime.now() + timedelta(hours=2)
    diferencia = cita - ahora

    if diferencia.total_seconds() <= 0:
        await update.message.reply_text("¡La cita ya pasó o es ahora mismo! Divertíos")
    else:
        total_segundos = int(diferencia.total_seconds())
        dias = total_segundos // 86400
        horas = (total_segundos % 86400) // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        await update.message.reply_text(
            f"Faltan {dias} días, {horas} horas, {minutos} minutos y {segundos} segundos para la cita. ⏳"
        )

# --- Flask + Webhook ---
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set", set_cita))
application.add_handler(CommandHandler("falta", cuanto_falta))

# Dispatcher para manejar actualizaciones
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot de Valentina y Adrià está vivo 💖", 200

# --- Solo necesario una vez para registrar el webhook ---
@app.route("/set-webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://chocolatet.onrender.com/webhook/{TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return f"Webhook {'creado con éxito' if success else 'falló'}"

