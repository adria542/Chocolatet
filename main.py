from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import json
import os

# Archivo donde se guarda la cita
DATA_FILE = "cita.json"


def guardar_cita(fecha_str):
    with open(DATA_FILE, "w") as f:
        json.dump({"cita": fecha_str}, f)


def cargar_cita():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f).get("cita")
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy un bot creado para Valentina y Adrià. Escribe /set para guardar una cita y /falta para ver cuánto falta 🤍"
    )


async def set_cita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa el formato: /set YYYY-MM-DD HH:MM"
                                        )
        return

    fecha_str = " ".join(context.args)
    try:
        # Forzamos los segundos a 0
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        cita_str = dt.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        guardar_cita(cita_str)
        await update.message.reply_text(f"Cita guardada para: {cita_str}")
    except ValueError:
        await update.message.reply_text(
            "Formato incorrecto. Esribe algo similar a: /set 2025-06-15 20:00")


async def cuanto_falta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cita_str = cargar_cita()
    if not cita_str:
        await update.message.reply_text("No hay ninguna cita guardada.")
        return

    cita = datetime.strptime(cita_str, "%Y-%m-%d %H:%M:%S")
    ahora = datetime.now() + timedelta(hours=2)
    diferencia = cita - ahora

    if diferencia.total_seconds() <= 0:
        await update.message.reply_text(
            "¡La cita ya pasó o es ahora mismo! Divertios")
    else:
        total_segundos = int(diferencia.total_seconds())
        dias = total_segundos // 86400
        horas = (total_segundos % 86400) // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60

        await update.message.reply_text(
            f"Faltan {dias} días, {horas} horas, {minutos} minutos y {segundos} segundos para la cita. ⏳"
        )


# Token de tu bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Crea la app del bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Comandos
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_cita))
app.add_handler(CommandHandler("falta", cuanto_falta))

# Ejecutar
app.run_polling()
