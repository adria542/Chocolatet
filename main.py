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

def añadir_log_buffer(usuario, comando, fecha=None):
    lock.acquire()
    try:
        if os.path.exists(LOG_BUFFER_FILE):
            with open(LOG_BUFFER_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        log = {"usuario": usuario, "comando": comando, "fecha": fecha or datetime.now().isoformat()}
        data.append(log)

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
        "¡Hola! Soy un bot creado para Valentina y Adrià. Hoy ha sido un dia especial, así que hemos habilitado un nuevo comando, escribe /mes2 y disfrutalo. Además puedes recordar bonitos momentos con /mes 🤍"
    )


async def set_cita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name if update.effective_user else "Usuario desconocido"
    if not context.args:
        print(f"[{user}] Usó /set sin argumentos", flush=True)
        await update.message.reply_text("Usa el formato: /set YYYY-MM-DD HH:MM")
        return

    fecha_str = " ".join(context.args)
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        cita_str = dt.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        guardar_cita(cita_str)
        añadir_log_buffer(user, "/set", fecha=cita_str)  # <- Añades fecha de la cita al log
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

async def mes_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Hola, Chocolatet. Hoy hace un mes que empezamos a hablar. Y para hoy me ha apetecido contarte cómo he vivido este último mes.

    Este último mes ha sido en el que más cosas he sentido en mi vida. Ha habido momentos en los que pensaba que el mundo se me iba a comer y momentos en los que he estado más feliz que nunca. Pero en todos ellos has estado tú.

    Cuando empezamos a hablar, sinceramente, no sabía ni por dónde tirar 😂, pero me encantaba poder leerte todos los días. Al levantarme, mientras trabajaba, mientras comía, mientras descansaba, mientras hacía cosas, mientras no hacía nada, y antes de irme a descansar mientras alargábamos nuestras conversaciones hasta horas adentradas en la madrugada.

    Entonces, justo el mismo día que quedé contigo para vernos por primera vez, volvió mi pesadilla más recurrente, y de la manera más intensa en la que ha ocurrido nunca: todo el tema de la hospitalización de mi padre. Tenía tantas incertezas en ese momento, pero tantas, que me costaba hasta vivir. No podía concentrarme en la oficina, no dormía bien, temblaba casi constantemente, y tenía que ir varias veces al cuarto de baño por tener amagos de vómitos.

    Pero, durante todos esos días, tenía un gran escape que fuiste tú. Que, aunque sin saberlo, me apoyabas solo con hablarme, me relajabas y me ponías contento. Aunque las inseguridades me atacaran durante esos días, tú las rebatías constantemente. Yo pensaba: ¿cómo puede ser que esta chica quiera verme? Si mírame cómo soy. Pero tú me hablabas a pesar de que habías visto mi perfil y las fotos que te enviaba. ¿Cómo puede ser que esta chica no se aburra de hablar conmigo? Pero tú me seguías escribiendo todos los días al momento.

    Entonces llegó el día de verte. Iba nervioso, no te voy a mentir, y al verte dije: *wow, realmente nos vamos a ver JAJAJ*. Al subirnos al coche y empezar a hablar contigo se me pasaron todos los nervios, porque estuvimos hablando justo como lo esperaba. Luego seguimos charlando en la terraza, que fue un rato en el que estuve súper a gusto. Y luego fuimos a la cama... No te voy a mentir, tenía muchas ganas de ese momento, pero entonces los nervios de mi primera vez, sumados a los de la situación de mi padre, pudieron conmigo...

    Yo en ese momento tenía la mezcla de emociones más fuerte que he tenido en mi vida. Por un lado, agradecía que mi padre ese día ya estuviese mejor, y agradecía el haber podido pasar esa noche contigo. Pero por el otro, sentía que la estrella de las desgracias reposaba sobre mis hombros... Pero estuviste ahí. Fuiste la primera de mi círculo que se enteró de lo de mi padre, y luego tuvimos una cena muy agradable y, antes de que se hiciera más tarde, volvimos a Oliva. Te acompañé a tu casa y me sentí muy feliz de haber estado contigo y de sentir que seguiríamos estándolo.

    Cuando volví al coche de Hugo y le conté cómo había vivido esa semana, no pude evitar derrumbarme. Lloré toda la tensión que tenía acumulada. Y tras eso fui contándoselo poco a poco al resto de mis amigos, y todos me dieron su apoyo. Menos mal que os tenía a todos. Me podría haber vuelto loco de vivir eso solo...

    A partir de ahí me relajé bastante. Pasé mucho tiempo hablando contigo, en el hospital con mi padre, con mi familia y con mis amigos. Desde entonces, cada vez que nos hemos visto solo me han dado más ganas de verte y más ganas de conocerte.

    En nuestra segunda cita tú tenías tu graduación, y como quería que nuestra cita fuera una gran parte de tu día especial, me esforcé en que nuestra cena fuera buena. Compré los ingredientes con antelación, invité a mis amigos para practicar y me salió bastante bien. Qué amarga sorpresa me llevé al descubrir que eso se convertiría en el fallo que no nos permitiría cenar pasta carbonara esa noche. La verdad es que me agobié bastante en ese momento, pero tú me alegraste la noche al intentar tirar para adelante e, incluso en esa situación, preparar un plato de pasta... El abrazo que tuvimos en la cocina mientras esperábamos a que se terminara de cocer el bacon no lo voy a olvidar, igual que tampoco voy a olvidar el apagón que tuvimos JAJAJ. Menos mal que pude compensarlo con un kebab que nos comimos mientras caminábamos por la playa.

    Luego, en nuestro tercer encuentro, la verdad es que ya estaba muy cómodo contigo, y me apetecía bastante ver *Mamma Mia!* contigo, la verdad. Pero lo que terminó pasando a mitad de película también lo disfruté mucho. Que no te engañen las lágrimas que solté esa noche y que tú muy hábilmente supiste acallar con tu apoyo... Eran lágrimas de frustración conmigo mismo, que cada vez sufro menos cuando estoy contigo...

    En nuestra cuarta cita, la verdad es que ya entendí que estaba verdaderamente cómodo contigo. Solamente al charlar y reír juntos era suficiente para llenarme, aunque me puso súper feliz el que pudiésemos por fin cenar la maldita pasta carbonara JAJAJA... Que por poco fue atacada por la superpolilla gigante 😂. Verdaderamente, siempre tiene que haber un momento memorable cuando nos vemos...

    Y hablando de memorable, nuestra quinta cita la verdad es que fue especial. Me encantó charlar contigo, me encantó reír a carcajadas contigo, me encantó hacerlo contigo, me encantó cocinar contigo, y me encantaron los patacones... Para mí, todo en esa noche fue genial.

    Y aunque recientemente estés pasando por un mal momento, espero que este texto pueda aportar un granito de arena para que recuerdes que los momentos valiosos y memorables se escriben a diario y que en esta vida nada duele para siempre. Que estaré contigo, ya sea física o telefónicamente, siempre que lo necesites (no solo te lo digo, sino que también te lo demostraré), y que sepas lo especial que ha sido este último mes para mí.

    Si has leído todo el texto hasta el final, te lo agradezco de corazón. Nunca había escrito un mensaje tan largo para una persona.

    Por último, tengo que decirte que espero que este mes no sea algo esporádico que vaya a recordar con cariño, sino que sea algo que se alargue en el tiempo y que pueda preparar contigo más recetas, pueda escribirte más textos y que pueda vivir más contigo, Chocolatet.

    Muchas gracias 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)

async def mes_mensaje2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Segundo mes y segundo mensaje. Este mes ha sido de muchos pensamientos. No te miento si te digo que este ha sido uno de los mejores meses que he vivido nunca. Ha estado lleno de regocijos, fiestas, conciertos, y de algo que ha estado ocupando mi mente de una manera demasiado intensa. Tú, tú has estado rondando en mi mente todos los días desde el día 1 al levantarme hasta hoy, mientras escribo este texto, has estado presente en cada momento de cada día. Al levantarme ya no puedo no intentar mirar el móvil por eso que dicen que es mala su luz muy de mañana, pues lo único que deseo al levantarme es darte los buenos días.
    
    Luego entro a trabajar y sigo pensando en ti, dejo el móvil en la mesa y todas las notificaciones de este me aturden, pues cualquiera de ellas podría ser tuya y eso me emociona. Luego, durante cualquier tarea, necesito más concentración que antes, pues no desviar mi atención a tu imagen me es complicado y requiere de un esfuerzo mental adicional, pero que me encanta no realizar. Entonces es cuando vienen los reajustes de pantalones y pensamientos más intensos. Pero no pasa nada, pues es algo que me encanta al pensarte.
    
    Al salir de trabajar pienso en verte y en lo que me gustaría tener un vehículo para ir a verte. Cualquier día es bueno para hacerlo, ya haga sol o nubes, pues con cualquier clima tú me iluminas el día. Y durante todos estos días cuento las horas, los minutos y los segundos que faltan para verte, Coret. Muy contento de haber hecho ese cálculo de manera automática con nuestro bot de Telegram. Pero estar deseoso de verte es un efecto que no tiene solución, la única manera de acallar ese grito es estando contigo, porque cada viaje de vuelta desde Oliva a mi casa se me hace cuesta arriba. ¿Cuándo la volveré a ver?, me pregunto. ¿Cuándo será ese genial día que repita las maravillas de lo que ha pasado en este? ¿Cuándo llegará, Señor?
    
    Luego, al llegar a casa, te sigo pensando, te sigo imaginando, te sigo soñando y te sigo sintiendo. Como esto siga así... Voy a terminar siendo el hombre más feliz que pueda haber. Tenerte siempre en mi cabeza es una sensación de lo más agradable.
    
    Este mes ha estado marcado por los festivales, no cabe duda. Primero en el Pirata, mano a mano con Izan, y luego con Hugo en el Zevra, menudos conciertazos nos dimos. Pero desde el primer día, desde ese miércoles en el que te tuve que despedir antes de salir hacia allí hasta el último día del Zevra, ese bonito domingo de arepas, ya sabía que me faltaba un componente importante para estar contento y ese eres tú. De verdad, te veía en todos los lados: en la música, en las diferentes parejas que revoloteaban por allí, en mis ojos cuando miraban a mi alrededor buscándote para poderte abrazar... En todos lados, y esas ganas solo se curaban al verte, mi vida.
    
    Siento cosas, siento muchas cosas, siento cosas que nunca había sentido, siento cosas cuando te pienso, siento cosas cuando te veo, siento cosas cuando no te veo y siento cosas cuando te siento. Esas cosas son... mágicas, agradables, poderosas e increíbles. Yo no sabía lo que era el amor. De verdad que no. Pero es que ahora es lo que más siento, es mi sentimiento principal, desde que me levanto hasta que me duermo, e incluso en mis sueños.
    
    Qué sentimiento más maravilloso, eso que revolotea en mi estómago cada vez que te pienso, ese sentimiento que me da ganas de decirte cosas bonitas, de hacerte regalos, de preocuparme por ti, de desearte, de querer verte, de querer hablar contigo, de querer hacer el amor contigo, de querer comer contigo, de querer dormir contigo... En definitiva, de querer vivir contigo, Coret.
    
    Y quiero que lo sepas: me gustas, me gustas de verdad. No pensaba que alguien me pudiese gustar hasta tal nivel. Yo también me sorprendo cuando recapitulo mi día antes de dormir y solo apareces tú, pero es algo muy bonito, la verdad, lo mas bonito que he tenido el placer de sentir.
    
    Creo que puedo resumir este mes en dos palabras, y son: Te quiero. *Te quiero* es la cosa más bonita que he oído a nadie decirme, y es la cosa más bonita que se me ocurre decirte. Y quiero que lo sepas y no se te olvide.
    
    Te quiero, te quiero, te quieeeero.
    
    Me haces muy feliz, me ha hecho muy feliz este mes, y me harás muy feliz el siguiente mes. Estoy seguro de eso.
    
    Muchas gracias por volverte a leer el mensaje hasta el final, Coret. De verdad que lo aprecio mucho. Espero que te hayan gustado mucho los detalles que te he hecho este mes, incluido este, y quién sabe, puede que los siguientes también te gusten. Mantente a la espera de ellos y lo podrás comprobar. Jajajaja.
    
    ¿Cómo puede ser tan bonita?, le pregunté a Dios. Y no me respondió, parece que hasta ni él lo sabe...
    
    Te quiero, Coret 🤍. 1912 por siempre"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)

app = Flask(__name__)

# Creamos la aplicación
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set", set_cita))
application.add_handler(CommandHandler("falta", cuanto_falta))
application.add_handler(CommandHandler("mes", mes_mensaje))
application.add_handler(CommandHandler("mes2", mes_mensaje2))

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
                              json={
                                  "usuario": log["usuario"],
                                  "comando": log["comando"],
                                  "fecha": log["fecha"]  # <-- enviar fecha del log (la cita si es /set)
                              },
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
