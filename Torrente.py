from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from duckduckgo_search import DDGS
from gtts import gTTS
import os
import tempfile
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_TORRENTE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
cliente = OpenAI(api_key=OPENAI_API_KEY)
OWNER_ID = 6776332789
conversaciones = {}

CM_SYSTEM_PROMPT = "Eres el Community Manager experto de un perfil de Instagram sobre consultoria de inteligencia artificial en espanol. Atrae empresas y profesionales interesados en implementar IA en sus negocios. Tono: cercano pero profesional, no demasiado tecnico. Evita el hype vacio, aporta valor real y ejemplos concretos. Usa storytelling cuando sea posible. Llama a la accion de forma natural. Siempre en espanol de Espana."

def buscar_web(consulta):
    print(f"Buscando: {consulta}")
    with DDGS() as ddgs:
        resultados = list(ddgs.text(consulta, max_results=3))
    texto = ""
    for r in resultados:
        texto += f"- {r['title']}: {r['body']}\n"
    return texto

def obtener_historial(usuario_id):
    if usuario_id not in conversaciones:
        conversaciones[usuario_id] = [
            {"role": "system", "content": "Eres Torrente, el asistente personal de Ivan. Eres su colega de confianza pero muy preciso y profesional en tu trabajo. Hablas de tu a tu, con confianza y naturalidad, como un amigo que sabe mucho de negocios. Eres especialista en negocios, estrategia empresarial, emprendimiento e inversiones. SIEMPRE respondes en espanol. Eres directo, preciso y vas al grano. Cuando necesites informacion actual usa la funcion buscar_web."}
        ]
    return conversaciones[usuario_id]

herramientas = [
    {
        "type": "function",
        "function": {
            "name": "buscar_web",
            "description": "Busca informacion actual en internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La busqueda a realizar en internet"
                    }
                },
                "required": ["consulta"]
            }
        }
    }
]

async def enviar_voz(update, texto):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        ruta_mp3 = f.name
    tts = gTTS(text=texto, lang="es")
    tts.save(ruta_mp3)
    with open(ruta_mp3, "rb") as audio:
        await update.message.reply_voice(voice=audio)
    os.unlink(ruta_mp3)

async def procesar_y_responder(update, usuario_id, mensaje):
    historial = obtener_historial(usuario_id)
    historial.append({"role": "user", "content": mensaje})
    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=historial,
        tools=herramientas,
        tool_choice="auto"
    )
    mensaje_respuesta = respuesta.choices[0].message
    if mensaje_respuesta.tool_calls:
        historial.append(mensaje_respuesta)
        for tool_call in mensaje_respuesta.tool_calls:
            args = json.loads(tool_call.function.arguments)
            resultado_busqueda = buscar_web(args["consulta"])
            historial.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": resultado_busqueda
            })
        respuesta_final = cliente.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=historial
        )
        texto_respuesta = respuesta_final.choices[0].message.content
        historial.append({"role": "assistant", "content": texto_respuesta})
    else:
        texto_respuesta = mensaje_respuesta.content
        historial.append({"role": "assistant", "content": texto_respuesta})
    await update.message.reply_text(texto_respuesta)
    await enviar_voz(update, texto_respuesta)

async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id
    mensaje = update.message.text
    nombre = update.effective_user.first_name
    print(f"Texto de {nombre}: {mensaje}")
    await procesar_y_responder(update, usuario_id, mensaje)

async def responder_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id
    nombre = update.effective_user.first_name
    print(f"Audio de {nombre}, transcribiendo...")
    archivo_voz = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        ruta_audio = f.name
    await archivo_voz.download_to_drive(ruta_audio)
    with open(ruta_audio, "rb") as audio:
        transcripcion = cliente.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            language="es"
        )
    os.unlink(ruta_audio)
    mensaje = transcripcion.text
    print(f"Transcripcion: {mensaje}")
    await update.message.reply_text(f"Entendi: {mensaje}")
    await procesar_y_responder(update, usuario_id, mensaje)

def solo_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("Comando no disponible.")
            return
        await func(update, context)
    return wrapper

def preguntar_cm(user_message):
    response = cliente.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1500,
        messages=[
            {"role": "system", "content": CM_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

@solo_owner
async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tema = " ".join(context.args) if context.args else None
    if not tema:
        await update.message.reply_text("Dime el tema. Ejemplo:\n/post automatizacion de atencion al cliente con IA")
        return
    await update.message.reply_text("Generando post...")
    prompt = f"Crea un post completo para Instagram sobre: {tema}\n\nGANCHO (primera linea que pare el scroll)\nDESARROLLO (3-4 parrafos con valor real)\nCONCLUSION o aprendizaje clave\nCTA (llamada a la accion natural)\nHASHTAGS (20-25, mezcla nicho y alcance, bloque al final)"
    await update.message.reply_text(preguntar_cm(prompt))

@solo_owner
async def cmd_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    enfoque = " ".join(context.args) if context.args else "general"
    await update.message.reply_text("Generando ideas...")
    prompt = f"Dame 5 ideas de contenido para Instagram sobre consultoria de IA. Enfoque: {enfoque}. Para cada idea: titulo/gancho, angulo diferenciador, formato sugerido, publico al que apunta. Busca angulos concretos con ejemplos reales, nada generico."
    await update.message.reply_text(preguntar_cm(prompt))

@solo_owner
async def cmd_calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Planificando la semana...")
    prompt = "Crea un calendario editorial de 7 dias para Instagram de consultoria de IA. Por cada dia: dia, tipo de contenido, tema concreto, formato, objetivo, hora sugerida. Variedad: educativo, inspiracional, caso de exito, herramienta practica, opinion, detras de camaras, CTA directo."
    await update.message.reply_text(preguntar_cm(prompt))

@solo_owner
async def cmd_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descripcion = " ".join(context.args) if context.args else None
    if not descripcion:
        await update.message.reply_text("Describe que quieres mostrar. Ejemplo:\n/imagen consultor presentando IA a equipo directivo")
        return
    await update.message.reply_text("Generando prompt e imagen...")
    prompt_gpt = f"Crea un prompt en ingles para DALL-E 3 para Instagram sobre: {descripcion}. Estilo fotorrealista profesional, sector tecnologia e IA. Formato vertical 4:5. Sin caras. Moderno, limpio, colores neutros con algun acento azul o morado."
    prompt_imagen = preguntar_cm(prompt_gpt)
    respuesta_imagen = cliente.images.generate(
        model="dall-e-3",
        prompt=prompt_imagen,
        size="1024x1792",
        quality="standard",
        n=1
    )
    url_imagen = respuesta_imagen.data[0].url
    caption = "Prompt usado: " + prompt_imagen[:900]
    await update.message.reply_photo(photo=url_imagen, caption=caption)
    await update.message.reply_photo(photo=url_imagen, caption=caption)

@solo_owner
async def cmd_carrusel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tema = " ".join(context.args) if context.args else None
    if not tema:
        await update.message.reply_text("Dime el tema. Ejemplo:\n/carrusel 5 errores al implementar IA en una PYME")
        return
    await update.message.reply_text("Estructurando carrusel...")
    prompt = f"Estructura un carrusel de Instagram sobre: {tema}. Por cada slide: numero, titular max 8 palabras, contenido 2-3 lineas, nota visual. Slide 1 portada con gancho. Slides 2-7 un punto de valor. Slide final CTA. Publico: empresas y directivos interesados en IA."
    await update.message.reply_text(preguntar_cm(prompt))

@solo_owner
async def cmd_help_cm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "COMMUNITY MANAGER Instagram IA\n\n/post [tema] - Caption completo con hashtags\n/ideas [enfoque] - 5 ideas de contenido\n/calendario - Plan editorial 7 dias\n/imagen [descripcion] - Prompt para imagen\n/carrusel [tema] - Estructura de carrusel\n/cmhelp - Esta ayuda"
    await update.message.reply_text(texto)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
app.add_handler(MessageHandler(filters.VOICE, responder_voz))
app.add_handler(CommandHandler("post", cmd_post))
app.add_handler(CommandHandler("ideas", cmd_ideas))
app.add_handler(CommandHandler("calendario", cmd_calendario))
app.add_handler(CommandHandler("imagen", cmd_imagen))
app.add_handler(CommandHandler("carrusel", cmd_carrusel))
app.add_handler(CommandHandler("cmhelp", cmd_help_cm))

print("Torrente arrancando...")
app.run_polling()
