"""
agente_ugc.py — Agente captación UGC para LooBe
Ubicación en servidor: /root/SecretariaLooBe/agente_ugc.py

Instalar dependencias (en el entorno virtual del servidor):
    source /root/SecretariaLooBe/entorno/bin/activate
    pip install fastapi uvicorn httpx openai

Arrancar manualmente:
    uvicorn agente_ugc:app --host 0.0.0.0 --port 8001

Servicio systemd: ver instrucciones al final del archivo
"""

import os
import json
import httpx
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Configuración 
──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID_OWNER")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")

app = FastAPI()
cliente_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)# ── Webhook 
principal 
──────────────────────────────────────────────────────────
@app.post("/ugc/candidata")
async def recibir_candidata(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    campos = ["nombre", "instagram_id", "edad", "ubicacion", 
"disponibilidad"]
    for campo in campos:
        if campo not in data or not data[campo]:
            raise HTTPException(status_code=422, detail=f"Falta el campo: 
{campo}")

    asyncio.create_task(procesar_candidata(data))
    return {"status": "ok", "mensaje": "Candidata recibida, procesando"}


# ── Lógica principal del agente 
────────────────────────────────────────────────
async def procesar_candidata(data: dict):
    nombre         = data.get("nombre", "Sin nombre")
    instagram_id   = data.get("instagram_id", "").strip().lstrip("@")
    edad           = data.get("edad", "?")
    ubicacion      = data.get("ubicacion", "?")
    disponibilidad = data.get("disponibilidad", "?")
    timestamp      = datetime.now().strftime("%d/%m/%Y %H:%M")

    analisis = await analizar_candidata(
        nombre=nombre,
        instagram_id=instagram_id,
        edad=edad,
        ubicacion=ubicacion,
        disponibilidad=disponibilidad
    )

    await notificar_telegram(
        nombre=nombre,
        instagram_id=instagram_id,
        edad=edad,
        ubicacion=ubicacion,
        disponibilidad=disponibilidad,
        analisis=analisis,
        timestamp=timestamp
    )# ── Análisis con GPT-4o-mini 
───────────────────────────────────────────────────
async def analizar_candidata(nombre, instagram_id, edad, ubicacion, 
disponibilidad) -> dict:
    bio_instagram = await obtener_bio_instagram(instagram_id)

    prompt = f"""Eres el Agente de Comunidad de LooBe, una marca de moda 
joven (fast fashion) española.
Tu tarea es evaluar si esta candidata encaja como creadora UGC (User 
Generated Content) para la marca.

PERFIL DE LOOBE:
- Marca de moda joven, entre 18-30 años
- Estética: urbana, atrevida, colorida, tendencia
- Plataformas: Instagram y TikTok
- Busca contenido auténtico, no producción de estudio

DATOS DE LA CANDIDATA:
- Nombre: {nombre}
- Instagram/TikTok: @{instagram_id}
- Edad: {edad}
- Ubicación: {ubicacion}
- Disponibilidad para grabar: {disponibilidad}
- Bio pública encontrada: {bio_instagram if bio_instagram else "No 
disponible"}

CRITERIOS DE EVALUACIÓN:
1. Edad entre 18-30 años (obligatorio)
2. Ubicación en España (preferible, no excluyente)
3. Disponibilidad inmediata o en menos de 2 semanas (señal de compromiso)
4. Bio/perfil coherente con estética moda joven

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin markdown:
{{
  "puntuacion": <número del 0 al 10>,
  "veredicto": "<APTA|REVISAR|NO APTA>",
  "motivo": "<explicación breve de 2-3 líneas>",
  "señales_positivas": ["<señal1>", "<señal2>"],
  "señales_negativas": ["<señal1>"]
}}"""

    try:
        respuesta = await cliente_openai.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = respuesta.choices[0].message.content.strip()
        return json.loads(texto)
    except Exception as e:
        return {
            "puntuacion": 5,
            "veredicto": "REVISAR",
            "motivo": f"No se pudo analizar automáticamente: {str(e)}",
            "señales_positivas": [],
            "señales_negativas": ["Error en análisis automático"]
        }


# ── Obtener bio de Instagram 
───────────────────────────────────────────────────
async def obtener_bio_instagram(username: str) -> str | None:
    if not username:
        return None
    try:
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like 
Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) 
Version/16.0 Mobile/15E148 Safari/604.1"
        }
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url, headers=headers, 
follow_redirects=True)
            if resp.status_code == 200:
                try:
                    datos = resp.json()
                    bio = datos.get("graphql", {}).get("user", 
{}).get("biography", "")
                    return bio if bio else None
                except Exception:
                    return None
    except Exception:
        return None# ── Notificación Telegram 
──────────────────────────────────────────────────────
async def notificar_telegram(nombre, instagram_id, edad, ubicacion,
                              disponibilidad, analisis, timestamp):
    puntuacion     = analisis.get("puntuacion", "?")
    veredicto      = analisis.get("veredicto", "REVISAR")
    motivo         = analisis.get("motivo", "")
    positivas      = analisis.get("señales_positivas", [])
    negativas      = analisis.get("señales_negativas", [])

    emoji_veredicto = {"APTA": "✅", "REVISAR": "⚠️", "NO APTA": 
"❌"}.get(veredicto, "⚠️")
    estrellas = "⭐" * min(int(puntuacion), 10)

    txt_positivas = "\n".join(f"  ✦ {s}" for s in positivas) if positivas 
else "  —"
    txt_negativas = "\n".join(f"  ✦ {s}" for s in negativas) if negativas 
else "  —"

    mensaje = (
        f"🎯 *Nueva candidata UGC*\n"
        f"_{timestamp}_\n\n"
        f"👤 *{nombre}*\n"
        f"📸 @{instagram_id}\n"
        f"🎂 {edad} años · 📍 {ubicacion}\n"
        f"📅 Disponibilidad: {disponibilidad}\n\n"
        f"─────────────────\n"
        f"{emoji_veredicto} *Veredicto: {veredicto}*\n"
        f"📊 Puntuación: *{puntuacion}/10* {estrellas}\n\n"
        f"💬 {motivo}\n\n"
        f"✅ Señales positivas:\n{txt_positivas}\n\n"
        f"⚠️ Señales de atención:\n{txt_negativas}\n"# 
══════════════════════════════════════════════════════════════════════════════
# INSTRUCCIONES PARA EL SERVIDOR
# 
══════════════════════════════════════════════════════════════════════════════
#
# 1. Subir al servidor:
#    scp agente_ugc.py root@178.104.195.224:/root/SecretariaLooBe/
#
# 2. Instalar dependencias:
#    ssh root@178.104.195.224
#    source /root/SecretariaLooBe/entorno/bin/activate
#    pip install fastapi uvicorn httpx openai
#
# 3. Añadir al .env del servidor:
#    TELEGRAM_CHAT_ID_OWNER=6776332789
#
# 4. Crear servicio systemd:
#    nano /etc/systemd/system/agente-ugc.service
#
#    [Unit]
#    Description=Agente UGC LooBe
#    After=network.target
#
#    [Service]
#    User=root
#    WorkingDirectory=/root/SecretariaLooBe
#    ExecStart=/root/SecretariaLooBe/entorno/bin/uvicorn agente_ugc:app 
--host 0.0.0.0 --port 8001
#    Restart=always
#    RestartSec=5
#    EnvironmentFile=/root/SecretariaLooBe/.env
#
#    [Install]
#    WantedBy=multi-user.target
#
# 5. Activar:
#    systemctl daemon-reload
#    systemctl enable agente-ugc
#    systemctl start agente-ugc
#    systemctl status agente-ugc
#
# 6. Probar el webhook manualmente:
#    curl -X POST http://178.104.195.224:8001/ugc/candidata \
#      -H "Content-Type: application/json" \
#      -d 
'{"nombre":"Test","instagram_id":"test_user","edad":"22","ubicacion":"Madrid","disponibilidad":"este 
finde"}'
#
# 7. Ver logs en tiempo real:
#    journalctl -u agente-ugc -f
#
# 
══════════════════════════════════════════════════════════════════════════════
