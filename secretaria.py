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
import requests
from datetime import datetime
import pytz

PRESTA_KEY = os.getenv("PRESTA_KEY")
PRESTA_URL = os.getenv("PRESTA_URL")

ultima_consulta = {}

def consultar_pedidos(usuario_id):
    try:
        zona_esp = pytz.timezone("Europe/Madrid")
        ahora = datetime.now(zona_esp)
        hoy = ahora.strftime("%Y-%m-%d")
        ultima = ultima_consulta.get(usuario_id)

        url_dia = f"{PRESTA_URL}/api/orders?ws_key={PRESTA_KEY}&output_format=JSON&limit=1000&filter[date_add]=[{hoy}%2000:00:00,{hoy}%2023:59:59]&date=1"
        r_dia = requests.get(url_dia)
        pedidos_dia = r_dia.json().get("orders", [])

        total_dia = 0
        pedidos_nuevos = []

        for pd in pedidos_dia:
            det = requests.get(f"{PRESTA_URL}/api/orders/{pd['id']}?ws_key={PRESTA_KEY}&output_format=JSON").json()
            orden = det.get("order", {})
            total_dia += float(orden.get("total_paid", 0))
            fecha_str = orden.get("date_add", "")
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                fecha = zona_esp.localize(fecha)
            except:
                continue
            if ultima is None or fecha > ultima:
                pedidos_nuevos.append((orden, fecha_str))

        ultima_consulta[usuario_id] = ahora
        resumen_dia = f"Total hoy ({hoy}): {len(pedidos_dia)} pedidos — {total_dia:.2f}EUR"

        if not pedidos_nuevos:
            return [f"No hay pedidos nuevos desde la ultima consulta.\n\n{resumen_dia}"]

        mensajes = []
        bloque = f"{len(pedidos_nuevos)} pedidos nuevos:\n\n"

        for orden, fecha_str in pedidos_nuevos:
            importe = float(orden.get("total_paid", 0))
            linea = f"Pedido #{orden['id']} - {fecha_str[:10]}\n"
            linea += f"  Importe: {importe:.2f}EUR\n"
            articulos = orden.get("associations", {}).get("order_rows", [])
            for a in articulos:
                nombre = a.get("product_name", "")[:40]
                cantidad = a.get("product_quantity", 1)
                linea += f"  {cantidad}x {nombre}\n"
            linea += "\n"
            if len(bloque) + len(linea) > 3800:
                mensajes.append(bloque)
                bloque = ""
            bloque += linea

        bloque += resumen_dia
        mensajes.append(bloque)
        return mensajes

    except Exception as e:
        return [f"Error: {str(e)}"]

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
cliente = OpenAI(api_key=OPENAI_API_KEY)
conversaciones = {}

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
            {"role": "system", "content": "Eres una secretaria personal eficiente y amable. Te llamas Aria. SIEMPRE respondes en español, nunca en inglés."}
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
                    "consulta": {"type": "string", "description": "La busqueda a realizar"}
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
    if any(palabra in mensaje.lower() for palabra in ["pedidos", "pedido", "compras", "ordenes"]):
        mensajes = consultar_pedidos(usuario_id)
        for msg in mensajes:
            await update.message.reply_text(msg)
        return

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

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
app.add_handler(MessageHandler(filters.VOICE, responder_voz))
print("Secretaria Aria arrancando...")
app.run_polling()
