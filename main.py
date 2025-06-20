from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import json
import os
import asyncio
import threading
import requests

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "cita.json"
GOOGLE_SCRIPT_WEBHOOK = "https://script.google.com/macros/s/AKfycbwMrvIWmTHWzGp0UYlu1d0NcSXZT_8Bc3d_ZGbq-h2bLUJ7phsjTwjb7koyCIj56ptD/exec"
LOG_BUFFER_FILE = "log_buffer.json"
lock = threading.Lock()

def añadir_log_buffer(usuario, comando):
    lock.acquire()
    try:
        if os.path.exists(LOG_BUFFER_FILE):
            with open(LOG_BUFFER_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append({"usuario": usuario, "comando": comando, "fecha": datetime.now().isoformat()})

        with open(LOG_BUFFER_FILE, "w") as f:
            json.dump(data, f)
    finally:
        lock.release()

def guardar_cita(fecha_str):
    with open(DATA_FILE, "w") as f:
        json.dump({"cita": fecha_str}, f)

def cargar_cita():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f).get("cita")
    return None

def registrar_evento(usuario, comando):
    try:
        requests.post(GOOGLE_SCRIPT_WEBHOOK,
                      json={"usuario": usuario, "comando": comando},
                      timeout=5)
    except Exception as e:
        print(f"Error enviando log a Google Sheets: {e}", flush=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name if update.effective_user else "Usuario desconocido"
    añadir_log_buffer(user, "/start")
    print(f"[{user}] Inició el bot con /start", flush=True)
    await update.message.reply_text(
        "¡Hola! Soy un bot creado para Valentina y Adrià. Escribe /set para guardar una cita y /falta para ver cuánto falta 🤍"
    )


async def set_cita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name if update.effective_user else "Usuario desconocido"
    añadir_log_buffer(user, "/set")
    if not context.args:
        print(f"[{user}] Usó /set sin argumentos", flush=True)
        await update.message.reply_text("Usa el formato: /set YYYY-MM-DD HH:MM")
        return

    fecha_str = " ".join(context.args)
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        cita_str = dt.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        guardar_cita(cita_str)
        print(f"[{user}] Guardó una cita: {cita_str}", flush=True)
        await update.message.reply_text(f"Cita guardada para: {cita_str}")
    except ValueError:
        print(f"[{user}] Usó /set con formato inválido: {fecha_str}", flush=True)
        await update.message.reply_text("Formato incorrecto. Usa: /set 2025-06-15 20:00")

async def cuanto_falta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name if update.effective_user else "Usuario desconocido"
    añadir_log_buffer(user, "/falta")
    cita_str = cargar_cita()
    if not cita_str:
        print(f"[{user}] Usó /falta pero no hay cita guardada.", flush=True)
        await update.message.reply_text("No hay ninguna cita guardada.")
        return

    cita = datetime.strptime(cita_str, "%Y-%m-%d %H:%M:%S")
    ahora = datetime.now() + timedelta(hours=2)
    diferencia = cita - ahora

    if diferencia.total_seconds() <= 0:
        print(f"[{user}] Usó /falta: la cita ya pasó o es ahora mismo.", flush=True)
        await update.message.reply_text("¡La cita ya pasó o es ahora mismo! Divertíos")
    else:
        total_segundos = int(diferencia.total_seconds())
        dias = total_segundos // 86400
        horas = (total_segundos % 86400) // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        print(f"[{user}] Usó /falta: faltan {dias}d {horas}h {minutos}m {segundos}s", flush=True)
        await update.message.reply_text(
            f"Faltan {dias} días, {horas} horas, {minutos} minutos y {segundos} segundos para la cita. ⏳"
        )

app = Flask(__name__)

# Creamos la aplicación
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set", set_cita))
application.add_handler(CommandHandler("falta", cuanto_falta))

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route("/procesar-logs", methods=["GET"])
def procesar_logs():
    lock.acquire()
    try:
        if not os.path.exists(LOG_BUFFER_FILE):
            return "No logs", 200

        with open(LOG_BUFFER_FILE, "r") as f:
            logs = json.load(f)

        if not logs:
            return "No logs", 200

        # Enviar logs uno a uno (o implementar envío en batch si Google Apps Script lo permite)
        for log in logs:
            try:
                requests.post(GOOGLE_SCRIPT_WEBHOOK,
                              json={"usuario": log["usuario"], "comando": log["comando"]},
                              timeout=5)
            except Exception as e:
                print(f"Error enviando log a Google Sheets: {e}", flush=True)

        # Limpiar buffer
        with open(LOG_BUFFER_FILE, "w") as f:
            json.dump([], f)

        return "Logs procesados", 200
    finally:
        lock.release()

async def start_app():
    await application.initialize()  # Inicializa internamente el bot también
    await application.start()
    # Mantener vivo el loop para que el bot no cierre
    while True:
        await asyncio.sleep(3600)

def run_bot():
    loop.run_until_complete(start_app())

threading.Thread(target=run_bot, daemon=True).start()

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook_handler():
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update, application.bot)  # Usar bot ya inicializado en application
    future = asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
    try:
        future.result(timeout=10)
    except Exception as e:
        print(f"Error procesando update: {e}")
        return "Error", 500
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot de Valentina y Adrià está vivo 🤍", 200

@app.route("/set-webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://tu-dominio.com/webhook/{TOKEN}"
    success = loop.run_until_complete(application.bot.set_webhook(url=webhook_url))
    return f"Webhook {'creado con éxito' if success else 'falló'}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
