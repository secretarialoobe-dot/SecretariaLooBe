from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI
from duckduckgo_search import DDGS
from gtts import gTTS
import os
import tempfile
import json

# Claves
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cliente de OpenAI
cliente = OpenAI(api_key=OPENAI_API_KEY)

# Memoria de conversación por usuario
conversaciones = {}

def buscar_web(consulta):
    print(f"🔍 Buscando: {consulta}")
    with DDGS() as ddgs:
        resultados = list(ddgs.text(consulta, max_results=3))
    texto = ""
    for r in resultados:
        texto += f"- {r['title']}: {r['body']}\n"
    return texto

def obtener_historial(usuario_id):
    if usuario_id not in conversaciones:
        conversaciones[usuario_id] = [
            {"role": "system", "content": """Eres Torrente, el asistente personal de Iván. 
Eres su colega de confianza pero muy preciso y profesional en tu trabajo.
Hablas de tú a tú, con confianza y naturalidad, como un amigo que sabe mucho de negocios.
Eres especialista en negocios, estrategia empresarial, emprendimiento e inversiones.
SIEMPRE respondes en español. Eres directo, preciso y vas al grano.
Cuando necesites información actual usa la función buscar_web."""}
        ]
    return conversaciones[usuario_id]

herramientas = [
    {
        "type": "function",
        "function": {
            "name": "buscar_web",
            "description": "Busca información actual en internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La búsqueda a realizar en internet"
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
    print(f"Transcripción: {mensaje}")
    await update.message.reply_text(f"🎤 Entendí: _{mensaje}_", parse_mode="Markdown")
    await procesar_y_responder(update, usuario_id, mensaje)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
app.add_handler(MessageHandler(filters.VOICE, responder_voz))

print("✅ Torrente arrancando...")
app.run_polling()
