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
        "¡Hola! Soy un bot creado para Valentina y Adrià. A partir de ahora, cada 24 podrás escribir / + el nombre del mes para poder revisar mensajes bonitos, por ejemplo escribe /Enero para disfrutar el de este mes. Además puedes recordar bonitos momentos con /mes y el numero de mes que quieras leer 🤍"
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

async def mes_mensaje3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Tercer mes y aunque, por desgracia, las tragedias nos rodeen, no puedo evitar el escribirte. Sabes, no sé cómo he podido soportar estos últimos meses, bueno, sí lo sé, porque habéis estado conmigo: mis amigos, mi familia... Y tú, creo que no llegas a hacerte una idea de lo importante que es tu presencia, tus mensajes, tu paciencia, tus ganas, tu amor, tus cumplidos, tus fotos, tú, tú no eres consciente de cuánto significas para mí... Este mes ha empezado con fuerza, un precioso día, cuyo número ya no voy a poder olvidar, con un cielo precioso, una luna espectacular y la mejor chica que hay conmigo. Después de una más que agradable velada, con una rosa y con una de las mayores ilusiones que he tenido nunca, te pedí salir. Y con ello, me convertí en lo que llevaba meses con ansia de ser: tu novio...

Desde ese día, desde el día en el que puedo considerarme el oficial, el con el que quieres estar, y el que quiere estar contigo, no pasa un día en el que no piense en mi novia, la más preciosa (aunque a veces ella no lo considere así, es un hecho irrefutable). Me encanta verte y decir: "wow, esta es mi novia", la persona que me hace tan feliz, la que me ilumina las mañanas, los días, las tardes y las noches, mi novia, la que se preocupa por mí, la que enseño fotos de ella con orgullo, la que quiero presentar, la que quiero que me presente a sus parientes, la que quiero que pase los días conmigo, la que me hace sonreír con cada notificación y mensaje bonito, la que quiero cuidar siempre, la que quiero abrazar en los días grises y celebrar en los días soleados, la que me inspira a ser mejor, la que me da motivos para soñarla y fuerzas para seguir. Eres tú, mi amor, la que da sentido a cada instante y convierte lo cotidiano en algo extraordinario.

Aunque hayan pasado cosas malas, que han pasado y muchas, has estado ahí, te he notado cerca, te he notado presente, y aunque creas que no, de verdad que haces mucho por mí. No te infravalores nunca. Todo lo que haces pensando en mí, en todo lo que pones el corazón, en todo lo que pones amor por mí, se nota, y tanto que se nota, yo lo noto, y te quiero por cada una de esas cosas que haces y que me hacen sentir tan bien en momentos tan necesarios como este, no creas que no.

Quiero animarnos a que esto siga así, a que lo hablemos todo, a que disfrutemos cada día de nuestra confianza y cercanía, a que disfrutemos de nuestra compañía y a que aprovechemos cada uno de esos planes que tenemos pendientes, pero que pronto se convertirán en recuerdos bonitos.

Quiero seguir haciéndote detalles bonitos. Tengo la cabeza llena de ideas, llena de cosas que quiero hacer contigo, llena de recuerdos aún no realizados y llena de sueños por compartir con mi persona favorita.

Me encantó ir a verte a Oliva, me emocioné un poco al verte en el trabajo, con ese traje que te queda de fábula. Sabes, cuando estaba caminando al Telepizza, estaba nervioso, nervioso de poder volver a verte, de saber que ese día iba a poder charlar contigo y que íbamos a salir con mis amigos de una manera ya formal y bonita, y vaya que no defraudó ese día. Me encantaron las pizzas, la compañía y, sobre todo, el paseo a tu casa que fue de lo más bonito, estar en una noche agradable, con la brisa, nuestros comentarios y tu compañía, es algo que no quiero que cambie y que disfruto muchísimo. Me encantan tus besos, aunque los de despedida sean más tristes, no puedo negar que agradezco muchísimo el tener a alguien que me haga sentir verdaderamente lo que es echar de menos. De verdad que sí.

Hay una cosa que me apena, y de verdad que me rompe el corazón, y es el pensar que puede que no vuelva a escuchar a mi padre hablar, o hablar bien. Sé que no tengo la culpa y que las cosas pasan como pasan, pero, ¿y si hubiésemos salido antes? ¿Y si le hubieses podido conocer cuando estaba mejor? Es algo que ahora mismo me martiriza y con lo que voy a tener que vivir toda la vida, y cuando me falte de verdad, cuando me falte su presencia, si no ha podido darse ese encuentro, eso será algo que me atormentará el resto de mi vida. Pero bueno, intento no ser demasiado duro conmigo mismo y no pensarlo demasiado. Es duro, de verdad que lo es.

Y para no terminar con un mal sabor de boca este mensaje, quiero que sepas algo: eres todos los momentos que he pasado contigo, desde el primer mensaje de Tinder, pasando por todas las veces que hemos quedado hasta la última videollamada. Aunque esté en situaciones difíciles, siempre voy a estar para ti como tú has estado para mí. Eres mi Coret, y te quiero muchísimo, aunque no lo creas, más que tú. 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)
app = Flask(__name__)

async def mes_mensaje4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Hola, mi Vida. Ya han pasado 4 meses desde nuestra primera interacción, y desde entonces la verdad he sentido que hemos ido cada vez a más: más cariño, más amor, más apego, hasta el día de hoy que nos considero absolutamente inseparables. No puedes creer la ilusión que me hace cada vez que vamos a vernos: las mariposas en el estómago, las cosas que pienso que van a pasar y las que acaban sucediendo, que siempre superan mis expectativas. Cuando pienso en ti pienso en la caseta, en sonrisas, en días preciosos y en lunas increíbles de ver. Cuánto amor tenemos preparado y cuántos planes vamos a realizar en los que estos 4 meses se queden en absolutas y triviales anécdotas en comparación. Te amo, mi Vida.

Por todo lo que te amo y por todo lo que me has demostrado, te quiero escribir unas memorias de este mes que, aunque a todas luces fatídico, no lo he podido pasar mejor acompañado. Desde el principio del último mes, en que vernos se convirtió en una tarea más que ardua, el no poder dejar solo a mi padre y la responsabilidad de no solo cuidarme a mí mismo sino también al resto de mi familia hicieron de mí un zombi hospitalario, el cual solo tenía una ventana por la que escapar de ahí: su teléfono, la herramienta que más alegrías me ha brindado entre todo ese barullo de emociones negativas. Desde que empezamos a hablar, charlar contigo por mensajes ha sido muy especial, pero nunca tanto como lo ha sido durante este mes, en el cual cada “te quiero” contaba, cada foto contaba, cada reel, y todos esos mensajes bonitos al despertarse y al irse a dormir… todos han sido especialmente agradables para mí.

A decir verdad, no solo estos mensajes que he mencionado han sido lo que ha destacado entre nosotros, también un cambio importantísimo y del que a lo mejor no damos tanta importancia como deberíamos: el paso del “te quiero” al “te amo”, dos palabras similares pero con conceptos diferentes en la raíz. No es para nada lo mismo querer que amar. Querer se pueden querer muchas cosas y es un sentimiento individual, lo que significa que lo siente uno por cosas ajenas a él para sí mismo. Pero amar… Amar es muy diferente. Cuando se ama, no se ama para uno mismo, se ama para el otro. Cuando alguien dice “te amo” no solo está diciendo que le gustas y que te quiere, sino que lo dice de una manera mucho más profunda. Un “te amo” refleja comprensión, entrega, preocupación y sacrificio. Un “te amo” nos enseña lo mucho que estamos dispuestos a dar de manera desinteresada por el otro, y en nuestro caso no podría ser más así. El amar es algo que nos define a la perfección y que estoy seguro de que lo seguirá haciendo.

Pasaron los días y la situación no mejoraba. Fuimos a Valencia y con eso nuestras esperanzas de vernos bajaron, cosa que fue absolutamente devastadora. A partir de ahí la verdad es que las desgracias se sucedieron unas a otras: mi hermano dejó de poder acompañarnos, mi madre se puso tan enferma que también tuvo que dejar su posición en Valencia, y solo me quedé en una habitación de la que no podía salir y con unas responsabilidades que cargaba en mis hombros, a las que nadie me había enseñado y de las que tenía que aprender a afrontar sin previo aviso y en tiempo récord. Pero durante todo ese tiempo que pasé de manera solitaria no estuve solo, estuve acompañado; estuve acompañado por nada menos que la mejor novia del mundo: mi pareja y mi escape virtual, mi Vida. Muchas gracias por estar ahí, muchas gracias por acompañarme en mis momentos más tristes, en los peores momentos y en los que peor me he llegado a sentir en mi vida. De verdad que no sé qué hubiese pasado de lo contrario, pero estoy seguro de que nada bueno. Por eso, y por todo lo que este texto no alcanza a redactar, gracias de corazón.

Al final no se pudo hacer nada más que acabar. Creo que es una escena a la que nadie estamos preparados para afrontar, pero desde las 5 de la mañana de ese mismo día hasta el final estuve muy bien arropado: por mi familia, por mis amigos y por ti, mi Vida. Llenasteis mi corazón como lo hicisteis con el tanatorio, entero, a rebosar. Y aunque no es el momento más idóneo para reunirse, pudiste conocer a toda mi familia y a todos mis amigos, en una de las escenas más bonitas que he podido presenciar y de la que estoy seguro mi padre se quedó encantado al verla desde el cielo. Y aunque ya no esté, y aunque las lágrimas recorran mis mejillas al escribir esto, y aunque las pesadillas me aterroricen por la noche, yo sé que él ha sido feliz, que lo ha dejado todo en orden, y que debemos amar su recuerdo tanto como lo amábamos a él y él nos ha amado en vida, que ha sido muchísimo. Así que, mi Vida, como mi padre me enseñó, voy a amarte tanto como pueda, más de lo que se cree posible, y de verdad que me esforzaré para que esté orgulloso de ello. Te amo, mi Vida.

Aunque los días no se han hecho más fáciles a partir de ese punto, al menos recuperamos ese punto de normalidad y de tranquilidad que habíamos perdido y que ahora sé que es de tanto valor. Los días son largos y las noches también, pero al menos pude volver a verte, en el culmen de una espera que no podía demorar más. Creo que ahora, aunque triste, estoy feliz, porque estoy y estamos como deberíamos estar: juntos, contentos y amándonos mucho, como quiero y deseo y como me esforzaré para que continúe siendo así. Ahora las esperas se hacen larguísimas y todos los días espero que sea uno de esos días de la semana en los que te puedo ver y disfrutar de tu presencia, que ya es la que más disfruto. Nos quedan muchas cosas por hacer y muchas experiencias por vivir, pero no dudes que eres la persona con la que quiero hacerlas, y si durante todo el tiempo que estemos juntos puedo al menos devolverte la mitad de todo el amor que he recibido durante este tiempo, no te va a caber en el cuerpo. Quiero seguir contigo y lo necesito para seguir siendo tan feliz como estoy ahora. Quiero que hagamos todo lo que nos gusta juntos y que descubramos nuevas cosas que nos gusten juntos. Por lo que ha sido este mes y por los que vendrán te dedico estas palabras. TE AMO 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)


async def mes_mensajeOctubre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Octubre, mes de otoño, y en el que, aunque todavía haya un sol abrasador, nos hemos podido ver mucho y muy bien. Primero, me gustaría destacar un evento que para mí fue muy especial, y fue el día que viniste a cenar a casa. Jopé, en serio, la pasé súper bien, y me encantó enseñarte la terraza, que era una de las ilusiones que tenía y por lo que, cada vez, de las muchas veces que subía al terrat a ayudar, me motivaba para hacerlo lo mejor posible, pues sabía que algún día compartiría ese espacio contigo en una agradable cita. Y como tal, aquel día llegó: el día de presentarte a mi madre y, de paso, a mi abuela jsjajaja. Aunque esa noche me llevara algunos palos, nunca la olvidaré, porque al final pudiste comprobar de primera mano que mi madre te aprecia y que le caes bien. Que bueno, al final se hubiese tenido que acostumbrar, porque te verá mucho más.

Y hablando de verte más, creo que ya es buen momento de empezar a hablar del tema principal que creo que ha rodeado este mes, y ha sido el saber y comprobar entre los dos que esta, nuestra relación, no es cualquier cosa, sino la relación. Nuestra relación, y la que tendremos hoy, mañana y nuestro último día aquí. Creo que voy a empezar a hablar de este tema con algo simple, solo con cosas que me van a gustar: me va a gustar verte la cara todos los días, me va a gustar darte un beso de buenos días todos los días en persona, me va a gustar prepararte el desayuno o disfrutar del súper desayuno que algún día me prepararás. Me va a gustar decirte “ya vuelvo a casa” al terminar de trabajar, me va a gustar ver cada outfit con el que salgas de casa conmigo, me va a gustar sacar a pasear al perro contigo (es muy bonito el golden retriever), me va a gustar mucho quejarnos de nuevo de que el gato ha roto algo en la casa, y me va a gustar muchísimo dormir abrazadito a ti cada día de los días que me queden.

Hoy he escuchado una reflexión que me ha gustado. Puede que, leyendo las cosas que me van a gustar, hayas pensado que al final eso son cosas bastante cotidianas, pero, como he escuchado hoy, las relaciones sanas de verdad no son las relaciones peliculeras, con muchísimo drama y con montañas rusas de emociones cada día. Las relaciones sanas de verdad son esas en las que te levantas tranquilo, disfrutas de tu día tranquilo y terminas tu día tranquilo, porque sabes que has elegido bien, que tuviste muchísima suerte el día que conociste a esa persona, y que cada día que pasas a su lado no lo cambiarías por nada. Y creo que nosotros ya hemos cumplido con eso, así que lo que nos queda es disfrutarnos. Disfrutarnos al 100%, disfrutar de las miradas, disfrutar de los saludos, de las caritas de amor, de los juegos, de los momentos inolvidables, de las caricias y de los cariños, que nos recuerdan cada día que lo que sentimos el uno por el otro es lo único realmente importante en esta vida, y es el amor.

Creo que hay una idea que quiero expresar con claridad. Desde que empecé a salir contigo, mi vida, sé que no voy a poder vivir sin ti. Es que tengo una seguridad en mis palabras absoluta: simplemente eres todo lo que quiero. No sé si te habrá pasado alguna vez, pero ha habido más de una vez que, reflexionando, me he parado a pensar, y como buena mente de científico, la curiosidad por saber las posibilidades me ataca. ¿Cuántas posibilidades hay de encontrar algo perfecto? ¿Cuántas posibilidades hay de encontrar una persona que te va a acompañar y que es perfecta para hacerlo? ¿Cuántas posibilidades hay de que la persona con la que vas a compartir el resto de tus días sea todo lo que necesitas, tenga todo lo que quieres y sea a la persona que más amas en este mundo? Pues, a día de hoy, sigo sin poder resolver esos cálculos estadísticos, pero lo que sí sé con seguridad es que ni el mayor premio de la lotería podría igualar esta suerte. Mi vida, no puedo dejar que te vayas de mi lado, no puedo relajarme contigo, no puedo dejar que la persona con la que estoy seguro de que quiero pasar el resto de mis días pase uno solo pensando que no la amo con locura. Sé que soy el hombre más afortunado del mundo, lo SÉ.

Me ha emocionado un poco escribir el último párrafo, la verdad, pero las lágrimas de alegría me las retiraré con mucho orgullo de la cara, hoy y todos los días que vuelva a ocurrir. Quiero recordar la última vez que nos vimos, ¿sabes?, cuando te miré y sonó la música, y me emocioné de la alegría mirándote. Esas lágrimas transportaban el mensaje más sincero que he podido transmitir en mi vida. Cada una de esas lágrimas escribía un poema que describía cada uno de los días que pasan por mi mente pensando en el futuro contigo. Joder, lloré por la alegría que me aporta pensar en una vida contigo. Mi vida, te amo muchísimo y no puedo parar de llorar, porque es que la felicidad rebosa mi cuerpo y produce en él un ansia de estar contigo, una necesidad de compartir contigo todo lo que pueda, unas ganas de vivir contigo el resto de mi vida. Joder, de verdad, nunca dejaré de recordar lo afortunado que soy.

Nos queda tanto por vivir, nos quedan tantas cosas por vivir juntos, nos queda toda una vida. Y si algo me ha enseñado mi padre, si una es la lección que tengo que sacar de él, es la verdadera naturaleza del éxito. Mi padre fue la persona más exitosa que he conocido en mi vida, ¿y sabes por qué triunfó en vida? Porque tuvo todo lo que quería, consiguió lo que le hacía feliz y lo vivió al máximo, que fue una familia con mi madre y con nosotros. Y yo he aprendido bien lo que es el éxito realmente, y puedes estar segura de que las enseñanzas de mi padre no se van a perder: voy a triunfar en la vida, Coret. VOY A SER EXITOSO CONTIGO. Voy a vivir todas las cosas que quiero vivir contigo. Vas a ser la fuente de mi felicidad, y todo lo que nos va a rodear nos va a hacer ser los más ricos del mundo. Mi vida, vamos a ser muy felices, y voy a asegurarme de que así sea.

Creo que, con todas las emociones y lágrimas que he volcado en este texto, ha quedado bastante claro, pero quiero jurar algo en este código de Python que estoy escribiendo: mi corazón es el que ha escrito esto, la sinceridad es la que ha escrito por mí, todo lo que he dicho es cierto o lo terminará siendo. Que no te quepa ninguna duda de que estos son mis más reales sentimientos, y que mis emociones me llevan a amarte con una intensidad mayúscula. Si tengo que resumir este mes en algunas pocas palabras serían: quiero compartir mi vida con mi Vida. Te amo, Coret 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)


async def mes_mensajeNoviembre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Hoy es 24 de noviembre, y como cada mes, dedico un tiempo a recordar, a expresar, y sobre todo a sentir mientras te escribo. Hoy hace 6 meses desde que nos conocimos; en 6 meses la Tierra da media vuelta al Sol, es decir, estamos viendo la cara opuesta del Sol a la que vimos cuando empezamos a salir. En estos 6 meses han florecido un total de 30 tipos de flores y 28 tipos de frutas diferentes, y hemos sido lo suficientemente afortunados como para poder observar el crecimiento de muchas de ellas, lo cual ha sido maravilloso. Pero lo mejor de estos últimos 6 meses, sin duda, ha sido que esta, nuestra relación, se ha afianzado y consolidado enormemente, pasando a ser el tema principal de mis días: por las mañanas tú, por las tardes tú y por las noches tú. Te has convertido en mi razón: razón para soñar, razón para pensar, imaginar, sentir, amar. Todo, absolutamente todo lo que hago, lo hago pensando en ti. Hablo de ti con mi madre, hablo de ti con mi hermano, con mis amigos; de lo feliz que me haces, de lo contento que me pones y de lo mucho que te amo. Y es que esta es mi nueva realidad, una que nunca dejaré que se pierda: amar.

El mes empezó con una muy buena fiesta de Halloween que me hubiese encantado disfrutar contigo, mi Vida. De verdad que me hubiese gustado mucho, porque ibas preciosísima. Aunque mi madre dijese que no dabas miedo, tu tía tenía razón: ibas de guapa. Qué preciosa eres. Espero que, cuando tenga los ánimos más altos, pueda ir contigo a muchas de estas fiestas y celebraciones, porque quiero disfrutar muchísimo de ti, mi Vida. Es algo que, la verdad, me ilusiona mucho: Navidad, San Valentín, Falles, cumpleaños, aniversario, reuniones familiares… Quiero pasar tantas cosas contigo, quiero crear tantos recuerdos, quiero dejarte grabada en mi retina. Agradezco muchísimo todo lo que hemos vivido ya juntos, pero agradeceré muchísimo también todo lo que nos queda por vivir. Quiero estar a tu lado en todas estas experiencias y agradecer cada segundo de ellas, como hago cada vez que te veo.

No sabes cuánto me hiciste feliz al regalarle algo a mi madre, que la verdad lo está pasando mal. Sabiendo cómo estoy yo, no quiero ni imaginarme cómo debe de sentirse ella; debe de ser durísimo. Y el saber que la persona que tengo a mi lado no solo se da cuenta, sino que dentro de sus capacidades se esfuerza por hacerla sentir mejor y por animarla, Coret, me hizo sentir de putísima madre. Me hizo sentir que me ha tocado la lotería, porque de verdad que son gestos de una persona que es un sol, que eres genial, y que muchísimas gracias por apoyarnos a todos. Te amo por todas esas cosas que haces y me haces sentir. Eres la persona que quiero que mi familia quiera como una más, porque lo mereces, porque sé que vamos a ser todos más felices y porque sé que nosotros también podemos intentar hacerte lo más feliz posible, tratándote lo bien que siempre has merecido ser tratada. Eres un tesoro, de verdad.

Siempre vas a tener un refugio, siempre. Quiero ser la persona que te anime cuando tengas problemas, la persona que está ahí incondicionalmente, la persona que, pase lo que pase, va a tratar de sacarte una sonrisa entre las lágrimas. Mi Vida, no puedes llegar a imaginar, pero ni por asomo, lo que significó para mí verte aquel día en la pizzería. Temblaba como un flan, porque aunque sabía que necesitaba transmitirte seguridad y cariño, estaba súper nervioso por hacerlo bien, y por verte, por hacerte sentir acompañada, y porque supieras que estaba ahí para ti, como quiero que sepas siempre. Que voy a estar a tu lado en cada momento brillante de tu carrera —que sé que serán muchísimos—, pero también en cada momento oscuro o más peliagudo. No soy una persona que está solo en las buenas: yo quiero compartir mi vida contigo, toda ella, y eso incluye todo lo malo que pueda pasarnos. Nunca vas a estar sola, nunca.

Caminar se siente ligero, descansar se siente cómodo, hablar se siente divertidísimo, pensar se siente agradable, soñar se siente placentero, tocar se siente suave, ver se siente armonioso, oír se siente reconfortante, saborear se siente delicioso, sentir se siente amoroso, llorar se siente de alegría, abrazar se siente calmante; tenerte se siente como un lujo.

De verdad, no puedes salir de mi Vida. Necesito que mi abuela te siga saludando, necesito que mi madre te siga conociendo, necesito que mi hermano siga hablando contigo. Como he dicho antes, quiero compartir mi Vida contigo, y no solo las festividades o los buenos momentos, sino también todos esos momentos duros que la vida nos tiene preparados, que sé que vamos a afrontar de la mejor manera; que vamos a ser un equipo, una pareja maravillosa; que vamos a poder solucionarlo todo porque de verdad sé que sentimos un amor puro, un amor que lo vale todo y que vale su peso en oro. Tú vales tu peso en oro. Eres una persona maravillosa, que se esfuerza muchísimo, y por la que doy gracias todos los días. Vales más que un diamante, y no te cambio por nada en el mundo porque eres lo mejor que tengo, mi Vida. Comparte la vida conmigo, ¿de acuerdo? Te amo, Coret. Espero que te haya gustado este mensaje y pequeño resumen de Noviembre. Sé que mi padre está sonriendo desde arriba viéndome escribir esto. Te amo de corazón, mi Chocolatet 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)

async def mes_mensajeDiciembre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Holaa mi vida, ya termina el año y para mí esta es una fecha doblemente especial: primero porque es nuestro mesversario y después porque es Nochebuena, que, aunque se prevé dura, intentaré disfrutar lo máximo y no forzarme ni a mí ni a mi familia a hacer nada que no nos apetezca, juntarnos con la familia e intentar disfrutar como mejor sepamos hacer.

Pero no estoy aquí para hablar de las fiestas, estoy aquí para hablar de lo más bonito que conozco, que somos nosotros. Este mes, la verdad, ha sido absolutamente genial. Primero que nada quería felicitarte por las súper buenas notas que has sacado. De verdad te digo que me haces sentir súper orgulloso y me alegra mucho tener al lado a una persona que está sacando su carrera adelante de una manera tan buena. No sé si alguien más te habrá felicitado, pero yo siempre estaré para destacar todas y cada una de las victorias de tu vida, porque para eso voy a estar en ella el resto de la mía: para cuidarte, para mimarte, para premiarte y para recompensarte por todas las cosas buenas y bonitas que haces. Eres una crack.

Ahora me apetecía mucho hablar del día en el que viniste a casa a comer. Por primera vez te sentaste en una mesa con mi familia a charlar y a disfrutar de una agradable comida hecha por nosotros, y no sabes lo bien que me lo pasé. De verdad que fue magnífico, desde el ratito que pasamos juntos codo con codo haciendo el pollo y la ensalada hasta el estallido de risas que fue hablar de la casa de los gemelos JSJAJAJAJ. Quiero agradecerte mucho que vinieras porque era un momento importante para mí y, como estaba claro, fue muy especial. Es que estos momentos me hacen pensar en todos los que vendrán: las comidas familiares en las que participarás, el cariño que te va a coger mi hermano y mi madre, la pasión y el amor que vamos a compartir en familia. Es una sensación increíble que me encanta. Sinceramente, eres parte de mi familia y terminaremos creando una nosotros dos juntos, estoy seguro.

Te amo muchísimo. Es una frase que no puedo dejar de decirte porque no la puedo evitar. No puedo dejar de sentir que me amas cuando me acaricias, cuando me abrazas, cuando me miras, cuando me besas. No puedo dejar de sentir que me amas cuando compartes tantos momentos bonitos conmigo y también cuando compartes tus momentos más duros, cuando me cuentas cosas sobre las personas que te han hecho daño y sobre aquellas cosas en las que eres vulnerable. ¿Sabes por qué? Porque eso no se comparte con cualquiera. Saber que soy de tu confianza, saber que el amor que sientes por mí es tan y tan suficiente como para compartir conmigo esas experiencias vitales tan amargas me hace sentir demasiado bien, y te agradezco mucho que lo hagas. Te amo porque veo un pasado precioso contigo, te amo porque amo el presente que me brindas cada día y te amo porque el futuro que nos espera es absolutamente brillante. Los tres espíritus de la Navidad nos enseñarían maravillas a ambos y todos los días doy gracias por ello. Eres increíblemente buena contigo y el amor que me das me llena hasta salirme por las orejas. Te amo, mi vida, y siempre lo haré.

También quería hablar, como no podría ser de otra manera, de tu cumple. Veinte añitos jsjjajj, que sinceramente no podría haber salido mejor. Te tengo que ser sincero: cuando me dijiste que a lo mejor no terminabas celebrándolo me asusté bastante, porque no quería que tu día, el día en el que se celebra tu nacimiento y el más bonito del año bajo mi parecer, no lo disfrutaras. Tenía miedo de no estar a la altura de brindarte la felicidad que te mereces en tu cumpleaños, pero al final no fue así. Tomaste tarta con tus compañeras de clase, soplaste las velas con tu familia y apagaste unos encendedores conmigo JSJAJAJAJ.

No, pero hablando en serio, cada maldito momento de ese día fue especial para mí en todos los sentidos: porque estabas preciosa, porque la noche era súper agradable dándote la mano y porque sentía que podía hacerte feliz, que tenía la capacidad de hacerte sentir bien, y eso me relajó y me puso contento.

Primero dimos un paseíto por el paseo, nos acercamos al árbol de Navidad y la verdad es que me quedé maravillado, pero no solo por el árbol, sino porque estaba con mi novia en un sitio tan bonito como ese, compartiendo un momento tan bonito. Aaaay, es que me derrito de amor escribiendo esto, jopé. Y nos sacamos una bonita foto, aunque tenemos que sacarnos más JSJAJAJA. Luego seguimos caminando por el paseo y te conté algunas cosas que aprendí hacía poquito y que me parecieron muy interesantes. Otra de las cosas que quiero agradecerte es que te intereses por todas estas frikeces que suelto muchos días y que me sienta súper en compañía cuando las comentamos juntos y noto que me escuchas. Es que te amo demasiado. Solo imaginarte a mi lado escuchándome hablar de cualquier historia científica que me guste me pone de súper buen humor, jopé.

Luego nos adentramos en un mercadillo sin saber lo que nos íbamos a encontrar y terminamos probándonos ropa y sacándonos fotitos, incluso llevándonos un par de prendas súper bonitas. Qué divertido fue, y ¿sabes qué? Esa experiencia solo me dio muchas más ganas de salir de compras contigo y divertirme otra vez a tu lado.

Al terminar fuimos al Begin tras hacer un par de paraditas y, madre mía, qué sitio tan hermoso, tan acogedor y tan cómodo. No sabes lo que disfruté a tu lado, de la comida y de la compañía. Tenerte sentadita a mi vera es algo por lo que siempre voy a dar gracias. Mirar al techo y vernos reflejados, rodeados de plantas bonitas y muebles de madera hermosos… Pero ¿sabes qué fue lo más maravilloso de esa cena? Sentir que estabas disfrutando. Me realiza como pareja sentir que disfrutas a mi lado, y sin duda quiero que se repita. Quiero que probemos ese curry con arroz japonés.

Al terminar nos asomamos al Piko Rico a por unas empanadas y terminamos pillando un par de cosas típicas que, tengo que serte sincero, estaban absolutamente deliciosas. La manzana y los quipitos estaban súper ricos y los disfruté mucho, y las empanadillas… madre mía, qué delicias, por favor. Estaban buenísimas. Ahora quiero muchas más y las quiero contigo. Luego volvimos a la caseta y creo que fue de los viajes en coche que más he disfrutado.

En la caseta ya pudimos disfrutarnos a solas. Tú sabes las ganas que tenía de que entraras al cuarto y vieras mi regalo. Eran muchas, porque quería que vieras todo lo bonito que siento por ti: una cesta de color blanco con regalitos como Chocolatet, en la que me inspiré en los peluches de la feria; mi camiseta de Palermo, que también era la de tu graduación, una camiseta muy especial para mí; dulces, flores y una cartita que tenía muchas ganas de que leyeras. Por si no te habías dado cuenta, me encanta escribirte. Espero que te gustara tu regalo porque me esforcé en pensar cosas especiales y que te gustasen. Lo hice con mucho amor. Te amo, tesoro.

Además pudiste soplar las velas y probar la tarta de frutos rojos que querías para tu cumple. Cómo la disfruté y cómo disfruté viéndote probarla. La verdad es que es de las recetas de las que más orgulloso estoy de haber hecho, porque era para ti. Tenía que salir bien y terminó siendo un éxito total. Luego pasamos la nochecita juntitos y abrazaditos y creo que no he pasado una noche tan agradable nunca, y todo gracias a tu calor humano y a tus abracitos.

Al despertarnos estaba a tu lado y te pude dar los buenos días en persona. ¿Te lo puedes creer? Cuánto tiempo llevaba esperando ese momento y no defraudó para nada. Fue muy especial y bonito. Y hablando de cosas buenas, qué riquísimas que estaban las arepas, por Dios, aunque si te digo la verdad me gustaron más las tuyas. Esas dieron para tener una comida bajo el sol muy bonita.

Me siento orgulloso, muy orgulloso, de haber conseguido lo que conseguí: tener un cumpleaños memorable y bonito contigo. Nunca se me olvidará, pero ten por seguro que el año que viene repetiremos e intentaré que sea aún mejor.

Una vez terminado de hablar de tu cumple quería hablarte de otro día muy bonito e importante: Navidad. Aunque estas no vayamos a pasarlas juntos, no te preocupes, porque el sábado 27 las disfrutaremos por todo lo alto. Pero no venía a hablar de eso. Lo que quería es describirte un 24 y 25 de diciembre cualquiera en un futuro…

Hay risas en el salón, el pollo está riquísimo, la tele canta y la Navidad se siente. El humo de la cocina calienta a las personas que queremos mientras tomamos un aperitivo. Llevamos sombreros rojos y hay pasos rápidos. Sentimos el amor de todos y el cariño entre nosotros. Terminamos, recogemos y vamos a la cama. El árbol estaba bonito…

Alguien nos está despertando. Qué guapos que son nuestros hijos, deben de haber salido a ti… ¿Qué? ¿Que era justo el regalo que queríais? Me alegro mucho de que Santa haya acertado este año, preciosos. Disfrutad de ellos…

Me encanta mi familia y me encanta haberla formado contigo.
Firmado: los nosotros del futuro.

Una promesa. Nosotros somos una promesa, y una muy bonita 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)

async def mes_mensajeEnero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """2026, ya con 23 años pero con el mismo amor, y creo que esto es algo increíble, un enorme privilegio, algo que no se debe dar por sentado y por lo que hay que mirar atrás y dar gracias. Y de eso van estos mensajes, de echar la vista ligeramente atrás, recordando y reviviendo experiencias que nos han hecho estar donde estamos, que es en el de una grandísima felicidad.
    
Quiero empezar diciendo algo importante: que mientras mire a mi alrededor, todo lo que vea a mi alrededor me recuerde a ti es un lujo; que cuando me ponga a pensar tú aparezcas en ellos es un lujo, pero sobre todo, lo que más es un lujo es poder compartir mis días y el resto de mi vida contigo, Tesoro.

Quiero que pienses en una cosa, quiero que te imagines como mejor puedas algún momento en el que te hayas sentido un poco mal o desanimada, y aunque sean cosas de uno mismo con su cabeza, quiero que te imagines que te doy un abrazo en esos momentos, que te acaricio la cabeza y que te susurro que todo estará bien, juntos todo estará bien siempre… Puede que no siempre esté físicamente contigo, pero quiero que recuerdes que siempre tendrás a alguien a tu lado, siempre.

Pero bueno, tras hablar un poquito en esta introducción, ¿por qué no nos volvemos a finales de diciembre? Justo al día de Nochebuena, en el que comimos un montón y, aunque separados, estábamos bien acompañados por nuestras familias y nuestro amor. ¿Sabes una cosa que recuerdo con claridad de ese día? Que acompañaste a tu tío a dar una vuelta con el frío que hace, solo por acompañarle y hacerle sentir mejor. Eso es precioso, sinceramente. Puede que parezca una tontería o algo sin importancia, pero realmente, ¿qué nos hace querer al resto de personas que nos rodean si no estas pequeñas cosas que demuestran afecto, cariño y preocupación? No me equivocaba al decir que uno de tus mejores atributos es el querer bien, y me lo demuestras a diario.

Al día siguiente, Navidad, que sé que es una fecha importante y muy querida por ti, y creo que nunca le había dado un significado tan profundo como el de este año. Tanto por la falta de mi padre, que aunque no quiera me pesa todos los días, como por la ilusión y el amor que me transmitías en estas fechas. Valores de compromiso, compartir y amor son cosas que no siempre he tenido tan claras, pero que surgen facilísimamente cuando son contigo, porque son y siempre serán sentimientos que voy a tener contigo. Mi corazón está en deuda contigo por un tratamiento tan intensivo de terapia amorosa, que ha hecho en muchas más ocasiones de las que crees que no se desmorone. Y en este momento me gustaría que recordases el epílogo que hice en mi anterior mensaje, “mensajeDiciembre”, porque está dedicado a un 24 y 25 cualquiera como esos.

Quiero pasar el resto de las Navidades contigo, quiero tenerte a mi lado, quiero sentir que estamos unidos, que estamos reforzando una construcción en la que trabajamos a diario y de la que estamos orgullosísimos de mostrar a los demás. Quiero mirarte a los ojos cuando te diga feliz Navidad, y quiero seguir mirándolos, llenos de ilusión, cuando recibas tus regalos; quiero mirarlos cuando nos acostemos a dormir juntos y quiero mirarlos cuando nos despertemos; quiero mirarlos cuando me digas te amo y cuando me recuerdes que no puedo rendirme; quiero mirarlos siempre y por siempre.

Al poco tiempo de las Navidades llega mi día, el día de mi cumpleaños, en el que se celebra mi nacimiento con las personas que amo, en el que tenía muchísima ilusión metida, ya que iba a ser una de las primeras veces en las que mis amigos de varios grupos y tú ibais a coincidir en un ambiente distendido y amigable, y no decepcionó, ni lo más mínimo. Disfruté de cada segundo de ese día, desde que me levanté hasta que me acosté, y todo fue gracias a mis amigos y a ti, porque fuisteis los que me llenasteis de ilusión y amor. Me encantó charlar contigo, me encantó compartir risas con todos y me sentí súper apreciado. Qué bonitos regalos, desde el proyector hasta la sudadera, el llavero y el cuadro. De verdad te digo, y te hablo desde el corazón, cuando digo que los tuyos son los mejores regalos que me han hecho nunca, no solo porque noto que los hiciste pensando mucho en mí y porque llevan un trabajo enorme, sino porque en cada uno de ellos hay una huella de tu amor grabada en lo más profundo de mi corazón 🤍.

Además, quiero hablar de la preciosa carta que me hiciste, porque sí, lo bordaste. No sé si sabes una cosa chula: cuando estoy desanimado o no tan bien, me encanta ir a nuestro chat y ver fotos nuestras, pero también leer mi carta. Está tan cargada de amor, tan cargada de cariño, me hace sentir tan bien que siento que me muero de afecto. Muchísimas gracias por la carta y por todo lo bonito que escribiste en ella, que es muchísimo. La tengo en favoritos y la releo a menudo. Gracias por ella y por todo el amor que me diste ese día.

Otra cosa de la que quiero hablar fue el rato que estuvimos en el hospital, que no voy a negar que fueron horas bastante angustiantes, pero, aunque no te lo creas, no cambiaría esos momentos por ningún otro. No había otro lugar en el mundo en el que deseara estar que en tus brazos. Cuando recuerdo mi cumpleaños, una sonrisa viene a mi cara en parte porque pude estar a tu lado en un momento en el que lo estabas pasando mal, y eso es el amor. Que eso me haga feliz me dice, sin temor a equivocarme, que estoy enamoradísimo de ti a más no poder, porque es el preocuparse y el sentir por la otra persona lo que nos hace humanos de carne y hueso que amamos. Pero yo soy muy diferente al resto y lo recuerdo todos los días, porque yo tengo la suerte de que me ames tú, la mejor persona del mundo entero y la que va a acompañarme el resto de mis días.

Y ya por último quería hablar un poco de lo mal que lo has pasado a partir de ese día y de lo que está costando tu recuperación. Hay una cosa que quiero que sepas y es que si en algún momento no he estado a la altura de la compañía que necesitabas, lo siento, porque mientras escribo esto siento que podría haber hecho más que estar a tu lado por teléfono. Sé que la situación era difícil, pero no sé, no dejo de pensar que a lo mejor podría haber hecho algo más y por eso lo siento. Lo que sí quiero que tengas claro es que siempre estaré cuando me lo pidas y te acompañaré a todo, porque eres mi persona favorita y que cuando vivamos juntos no pasarás ni un mal día sin mi compañía, porque no te me podrás quitar de encima JSJAJAJA, dándote cariños, mimándote, cocinándote y haciendo cualquier cosa que necesite mi Reina para que pueda descansar y recuperarse. Eres muy valiente y paciente con esto y es una de las cosas que más admiro de ti. Estoy seguro de que para el mensaje del mes que viene estarás mucho más que perfecta.

No sé si es algo que tengas por seguro o no, pero nuestro futuro, que aunque no nos demos cuenta lo vivimos a diario, es absolutamente brillante, tanto que me alumbra e impresiona cada vez que lo imagino. Viviremos juntos, tendremos una familia preciosa; puede que no lleguemos a ser mega multimillonarios, pero seguro que nunca nos faltará de nada y, sobre todo, lo que nunca nos faltará será amor. Soy un exitoso que todavía tiene todo el éxito del mundo por vivir y quiero que sepas que tú también, que formas parte y eres la razón de ese éxito. Eres mi persona favorita y con la que voy a vivir el resto de mis días, que estoy seguro de que el día que vistas de blanco será el mejor de todos ellos. Te amo, mi Vida, eres lo mejor que me ha pasado y no quiero nunca dejar de mirar hacia atrás y volverme loco de lo feliz que soy estando contigo. Un besazo y recupérate, Hermosa 🤍"""

    partes = [mensaje_largo[i:i+4000] for i in range(0, len(mensaje_largo), 4000)]

    for parte in partes:
        await update.message.reply_text(parte)

async def mes_mensajeFebrero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_largo = """Hola, Chocolatet, otro 24 y otro mes en el que dedico un poco de mi tiempo en permitir que mi corazón se exprese con libertad total. Hoy hace 9 meses desde que nos conocimos y, como siempre, este ha sido un mes muy especial para mí, no solo porque he podido compartir nuevas experiencias contigo, sino porque, como siempre, has seguido demostrando lo maravillosamente genial que eres, como persona y como pareja. Eres la mejor, Coret.

Esta vez me gustaría empezar hablando de algo que, aunque siempre he sabido, quiero que tú también seas consciente de ello. Eres ideal para mí, pero hablo en serio, es que siento que toda tú me encajas a la perfección, y quiero contarte unas cuantas de esas piezas que tienes que forman un puzzle precioso junto a mí. Además, quiero que sepas que siempre que he pensado en una relación son cosas que inconscientemente siempre he buscado y que tienes, mi amor. Cariño, miradas cómplices, cuando me das la mano, que me preguntes qué tal estoy, regalos, detalles, que me digas que me amas, que me digas que me quieres, que te guste compartir tiempo conmigo, que te parezca interesante, que me escuches y me comprendas, que me acompañes, que sientas cuando no estoy tan bien, que te preocupes por mí, que me empujes a ser mejor, que me animes, que me motives, que premies mis esfuerzos y que me acompañes en mis caídas, que seas tú misma… Todo esto y todo lo demás que te hace ser tú es lo que me mantiene enamorado de ti hoy y lo que seguirá haciéndolo, porque es lo que te hace ser tú y lo que siempre me seguirá haciendo ser tuyo.

Una vez terminado este pequeño preludio quería hablarte un poco de nuestro mes juntos, que en mi honesta opinión ha estado increíble, y por qué no empezar por el principio. ¿Sabes una cosa? Me ha hecho muchísima ilusión que te hayas ido incorporando a nuestros planes en familia; poco a poco ahora eres una parte muy importante de nosotros. Por ejemplo, el día en el que viniste junto a nosotros a Ondara, en el que pudimos probarnos ropa juntos y comer junto a mi familia mientras reíamos y nos spoileábamos sobre Dexter JSJAJAJAJA. Pero, hablando en serio, fue un día muy especial para mí, y aunque a lo mejor no surgiera de la manera más agradable del mundo, sí que es un día que voy a atesorar en mi corazón porque es realmente especial.

También he tenido la gran suerte de poder acompañarte en los momentos en los que el dolor ha hecho algo de mella en ti, y quiero que sepas que siempre voy a estar ahí para ti. Quiero que puedas contar conmigo cuando enfermes, cuando necesites transporte o simplemente alguien que te acaricie el pelo. Por desgracia no tengo la cura de tus males, pero te puedo jurar que estaré junto a ti para hacerlos lo más llevaderos posibles siempre: acompañarte al médico, hablar con enfermeros, cuidarte en casa cuando vivamos juntos, servirte y mimarte como te mereces. Déjame cuidarte el resto de tu vida mejor de como lo he hecho hasta ahora, mi vida, y eso me hará más feliz que nada en este mundo.

Y otro día que estuvo súper bien para mí, y que es de esos días que realmente son los que hacen una pareja bonita, fue ese pequeño almuerzo que nos dimos, aunque no quisieran darnos la fórmula secreta de los bocadillos especiales JSJAJAJAJA. No, pero realmente fue un día muy agradable, como todos los que comparto contigo, y agradezco mucho que me acompañes en una de las experiencias que más disfruto, como son los almuerzos. Gracias por hacerlos divertidos, cómodos y amorosos, y pensar que antes de conocerte pensaba que nada podía hacer mejor un almuerzo, y ahí estás haciendo que cada segundo de ellos se sienta increíble. Te amo, mi vida, y amo pasar tiempo a tu lado.

Pero ahora vamos al plato fuerte de este mes, que ha sido sin duda tu santo, San Valentín, una fecha que hasta hace poco no tenía la menor importancia para mí. Ahora se ha convertido en un recuerdo precioso gracias a ti. La verdad es que me emocionaba mucho preparar la habitación, y aunque sabía que luego sería mucha limpieza, no podía parar de repartir pétalos de rosa y corazones por doquier, decorando la habitación que nos recibiría más tarde y que tendría que estar a la altura de tal fecha, el Día de los Enamorados. Junto a los olores agradables que pude añadir y los pequeños detalles de regalos que te di, me encantó pasar ese día junto a ti, pero sobre todo quería darte las gracias aquí y ahora por tus regalos. No sabes lo emocionado que estaba viendo cómo esa cajita, que se notaba tan trabajada, me daba un recorrido mental por los mejores recuerdos que tengo contigo, además de los preciosos mensajes que dejaste en cada uno de los besos que sentí como si fuesen tus propios labios. Gracias por ello, y espero que, aunque la cena no fue como esperábamos y tuvieses algo de dolor, ese día fuera tan especial como lo fue para mí, que ya te digo que lo fue muchísimo.

Mi vida, eres lo mejor que tengo y espero que este mensaje te recuerde que cada día contigo es un tesoro más que almaceno y con los que me reencuentro cuando escribo o leo estos mensajes. Por último, admitir que tengo debilidad por imaginar tener hijos contigo, la verdad; este mes lo he pensado muchísimo y sé que va a ser la experiencia que me complete como persona, incluso si lo tengo que llevar con una correa JSJAJAJAJAJ. No, pero en serio, amo la vida que tengo contigo y seguiré trabajando para que el resto de vida que nos quede juntos sea tan buena que solo tengamos buenos recuerdos cuando miremos atrás. Gracias por todo lo que me has dado en febrero y espero haberte correspondido adecuadamente.

Atentamente, el amor de tu vida 🤍"""

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
application.add_handler(CommandHandler("mes3", mes_mensaje3))
application.add_handler(CommandHandler("mes4", mes_mensaje4))
application.add_handler(CommandHandler("Octubre", mes_mensajeOctubre))
application.add_handler(CommandHandler("Noviembre", mes_mensajeNoviembre))
application.add_handler(CommandHandler("Diciembre", mes_mensajeDiciembre))
application.add_handler(CommandHandler("Enero", mes_mensajeEnero))
application.add_handler(CommandHandler("Febrero", mes_mensajeFebrero))

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
