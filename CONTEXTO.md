# 🤖 Proyecto: SecretariaLooBe — Ecosistema Multi-Agente

> **Última actualización:** 28/04/2026
> **Estado:** En producción activa

---

## 📌 Resumen del Proyecto

Sistema de agentes de IA construido para automatizar tareas de negocio de LooBe Shop (loobeshop.com), tienda de moda fast fashion. El objetivo final es tener un ecosistema completo de agentes especializados, incluyendo un Community Manager autónomo para Instagram y TikTok.

---

## 🖥️ Infraestructura

| Elemento | Detalle |
|---|---|
| **Servidor** | Hetzner VPS — IP: 178.104.195.224 |
| **OS** | Ubuntu 24 |
| **Repositorio** | github.com/secretarialoobe-dot/SecretariaLooBe |
| **Coste servidor** | ~4,90€/mes |
| **Gestor de servicios** | systemd (bots corren 24/7) |
| **Entorno virtual Python** | `/root/SecretariaLooBe/entorno/` (Python 3.12) |
| **Panel web** | https://panel.loobeshop.es (con autenticación básica) |

---

## 📁 Estructura del Proyecto

```
/root/SecretariaLooBe/
├── secretaria.py        # Bot SecreLooBe (Telegram)
├── Torrente.py          # Bot Torrente (Telegram)
├── agente_ugc.py        # Agente captación colaboradoras UGC
├── requirements.txt     # Dependencias Python
├── .gitignore           # Excluye .env y entorno virtual
└── .env                 # Claves API (NUNCA subir a GitHub)

/root/panel-loobe/
├── main.py              # Backend FastAPI del panel
├── panel.db             # Base de datos SQLite
└── static/
    ├── index.html       # Frontend del panel
    └── ugc.js           # JS del módulo UGC (incrustado en index.html)
```

---

## 🔑 Variables de Entorno (`.env` en `/root/SecretariaLooBe/`)

```
TELEGRAM_TOKEN=token_de_secretaria
TELEGRAM_TOKEN_TORRENTE=token_de_torrente
TELEGRAM_TOKEN_TAPABOT=token_de_tapabot
OPENAI_API_KEY=clave_openai
PRESTA_KEY=clave_api_prestashop
PRESTA_URL=https://loobeshop.com
TELEGRAM_CHAT_ID_OWNER=6776332789
```

---

## 🤖 Agentes Activos

### 1. SecreLooBe (`secretaria.py`)
- **Canal:** Telegram
- **Token:** `TELEGRAM_TOKEN`
- **Usuario:** Mujer del propietario (tienda LooBe Shop)
- **Servicio systemd:** `secretaria`
- **Puerto:** —
- **Funciones:**
  - Conversación general con IA (Claude/GPT)
  - Búsqueda web en tiempo real (DuckDuckGo)
  - Respuesta por voz (gTTS) y reconocimiento de voz
  - Consulta de pedidos PrestaShop en tiempo real:
    - Pedidos nuevos desde la última consulta
    - Artículos e importe de cada pedido
    - Total facturado del día natural

### 2. Torrente (`Torrente.py`)
- **Canal:** Telegram
- **Token:** `TELEGRAM_TOKEN_TORRENTE`
- **Funciones:** Conversación general con IA
- **Servicio systemd:** `torrente`

### 3. Agente UGC (`agente_ugc.py`) ⭐ NUEVO
- **Tipo:** API REST (FastAPI + uvicorn)
- **Puerto interno:** 8001
- **Puerto externo:** https://panel.loobeshop.es/ugc/
- **Servicio systemd:** `agente-ugc`
- **Función:** Captación y evaluación automática de colaboradoras UGC
- **Flujo completo:**
  1. ManyChat recibe comentario "UGC" en Instagram
  2. ManyChat hace las preguntas y recoge los datos
  3. ManyChat llama al webhook: `POST https://panel.loobeshop.es/ugc/candidata`
  4. El agente analiza con GPT-4o-mini y puntúa (0-10)
  5. Notifica a Telegram (chat ID: 6776332789) con ficha completa y botones
  6. Guarda la candidata en `panel.db` → tabla `ugc_candidatas`
  7. La candidata aparece en el panel web

---

## 🏪 Integración PrestaShop

| Elemento | Detalle |
|---|---|
| **Tienda** | loobeshop.com |
| **API activada** | Sí (Webservice) |
| **Clave API** | En `.env` del servidor (`PRESTA_KEY`) |
| **Permisos** | GET en orders, products, customers |
| **Funciones activas** | Pedidos nuevos + total día |

---

## 🖥️ Panel Web (panel.loobeshop.es)

- **Backend:** FastAPI en Python
- **Base de datos:** SQLite (`panel.db`)
- **Puerto interno:** 8081
- **Servicio systemd:** `panel-loobe`
- **Nginx:** `/etc/nginx/sites-enabled/panel-loobe`
- **Autenticación:** Basic Auth (`.htpasswd`)

### Pestañas del panel:
1. **Community Manager** — Generador de contenido para Instagram/TikTok
2. **Anuncios Meta Ads** — Análisis de campañas CSV + generador de copy
3. **Colaboradoras UGC** ⭐ NUEVA — Gestión de candidatas UGC

### Módulo Colaboradoras UGC:
- Ver todas las candidatas con puntuación, veredicto y datos
- Filtrar por: Todas / Aptas / Revisar / No aptas / Aprobadas / Rechazadas
- Aprobar / Rechazar candidatas con un clic
- Eliminar candidatas
- Ver perfil de Instagram directamente

### Endpoints API del panel:
```
GET    /api/ugc/candidatas        — Listar candidatas
POST   /api/ugc/decision          — Aprobar/rechazar candidata
DELETE /api/ugc/candidatas/{id}   — Eliminar candidata
```

---

## 📊 Base de Datos SQLite (`panel.db`)

### Tabla `ugc_candidatas`
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
nombre TEXT
instagram_id TEXT
edad TEXT
ubicacion TEXT
disponibilidad TEXT
puntuacion INTEGER    -- 0 a 10 (GPT-4o-mini)
veredicto TEXT        -- APTA | REVISAR | NO APTA
motivo TEXT           -- Explicación del veredicto
decision TEXT         -- aprobada | rechazada | null
fecha TEXT            -- dd/mm/yyyy HH:MM
```

---

## 📱 Integración ManyChat

- **Plataforma:** ManyChat Pro (Instagram)
- **Automatización:** "UGC Colaboradoras"
- **Disparador:** Comentario con palabra clave **UGC** en Instagram

### Campos personalizados creados en ManyChat:
| Campo | Tipo | Pregunta asociada |
|---|---|---|
| `ugc_nombre` | Texto | ¿Cómo te llamas? |
| `ugc_edad` | Texto | ¿Cuántos años tienes? |
| `ugc_ubicacion` | Texto | ¿Dónde vives? |
| `ugc_perfil` | Texto | ¿Cuál es tu Instagram o TikTok? |
| `ugc_disponibilidad` | Texto | ¿Cuándo podrías grabar? |

### Flujo del DM en ManyChat:
1. Respuesta al comentario público (avisa que se ha enviado DM)
2. DM de bienvenida con explicación de la colaboración
3. Preguntas una a una guardando en campos personalizados
4. Mensaje de cierre
5. Llamada HTTP POST al agente con los datos

### Webhook configurado en ManyChat:
- **URL:** `https://panel.loobeshop.es/ugc/candidata`
- **Método:** POST (CORREO en español)
- **Body:** JSON con variables de ManyChat

---

## 🧰 Stack Tecnológico

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.12 |
| IA | OpenAI GPT-4o-mini |
| Telegram | python-telegram-bot 22.7 |
| API REST | FastAPI + uvicorn |
| Voz | gTTS + SpeechRecognition |
| Búsqueda web | DuckDuckGo Search |
| E-commerce | PrestaShop API (REST) |
| Base de datos | SQLite |
| Servidor web | nginx (proxy inverso + SSL) |
| SSL | Let's Encrypt (Certbot) |
| Servicios | systemd |
| Repositorio | GitHub |
| Marketing automation | ManyChat Pro |

---

## 🚀 Comandos Útiles del Servidor

```bash
# Conectarse al servidor
ssh root@178.104.195.224

# Ver estado de todos los servicios
systemctl status secretaria torrente agente-ugc panel-loobe

# Reiniciar servicios
systemctl restart secretaria
systemctl restart torrente
systemctl restart agente-ugc
systemctl restart panel-loobe

# Ver logs en tiempo real
journalctl -u secretaria -f
journalctl -u torrente -f
journalctl -u agente-ugc -f
journalctl -u panel-loobe -f

# Actualizar código desde GitHub
cd /root/SecretariaLooBe
git pull origin main
systemctl restart secretaria torrente agente-ugc

# Probar webhook UGC manualmente
curl -X POST http://localhost:8001/ugc/candidata \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Test","instagram_id":"test_user","edad":"22","ubicacion":"Madrid","disponibilidad":"este finde"}'

# Probar endpoint panel UGC
curl -s http://localhost:8081/api/ugc/candidatas

# Ver candidatas en BD
python3 -c "import sqlite3; con=sqlite3.connect('/root/panel-loobe/panel.db'); print(con.execute('SELECT * FROM ugc_candidatas').fetchall())"
```

---

## ⚙️ Servicios systemd

### agente-ugc.service
```ini
[Unit]
Description=Agente UGC LooBe
After=network.target

[Service]
User=root
WorkingDirectory=/root/SecretariaLooBe
ExecStart=/root/SecretariaLooBe/entorno/bin/uvicorn agente_ugc:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
EnvironmentFile=/root/SecretariaLooBe/.env

[Install]
WantedBy=multi-user.target
```

### panel-loobe.service
```ini
[Unit]
Description=Panel LooBe Shop
After=network.target

[Service]
User=root
WorkingDirectory=/root/panel-loobe
ExecStart=/root/SecretariaLooBe/entorno/bin/uvicorn main:app --host 0.0.0.0 --port 8081
Restart=always
RestartSec=5
EnvironmentFile=/root/SecretariaLooBe/.env

[Install]
WantedBy=multi-user.target
```

---

## 🌐 Nginx — panel.loobeshop.es

```nginx
server {
    server_name panel.loobeshop.es;

    location /ugc/ {
        proxy_pass http://127.0.0.1:8001/ugc/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        auth_basic "LooBe Shop — Panel CM";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/panel.loobeshop.es/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/panel.loobeshop.es/privkey.pem;
}
```

---

## 📣 Campaña UGC en Instagram

### Carrusel de 3 slides publicado/pendiente de publicar:

**Slide 1 — Gancho:**
> ¿Y si te pagaran por llevar nuestra ropa?

**Slide 2 — Valor:**
> ✦ Ropa gratis de cada colección
> ✦ Compensación económica por contenido
> ✦ Tu cara en nuestra cuenta
> ✦ Sin mínimo de seguidores

**Slide 3 — CTA:**
> Comenta **UGC** 👇 y te mandamos toda la info al privado

### Caption:
> ¿Y si te pagaran por llevar nuestra ropa? 👀
> Buscamos creadoras UGC para colaborar con LooBe. Sin millones de seguidores. Solo tú, tu móvil y las ganas de crear contenido real.
> Solo 5 plazas para empezar. Comenta **UGC** y te escribimos al privado con toda la info en menos de 24h.
> #ugccreator #ugcspain #ugcspañol #creadoresdecontenido #loobe #loobestore #modajoven #fastfashion

---

## 🗺️ Hoja de Ruta

### ✅ Completado
- [x] Bot SecreLooBe con consulta PrestaShop, voz y búsqueda web
- [x] Bot Torrente conversacional
- [x] Panel web con generador de contenido CM
- [x] Panel web con análisis de Meta Ads
- [x] Agente UGC con webhook, análisis GPT y notificación Telegram
- [x] Integración ManyChat → Agente UGC
- [x] Panel web módulo Colaboradoras UGC (ver, filtrar, aprobar, rechazar, eliminar)
- [x] Exposición segura por HTTPS via nginx

### 🔜 Próximos pasos (corto plazo)
- [ ] Publicar carrusel UGC en Instagram
- [ ] DM automático de confirmación a candidatas aprobadas/rechazadas vía ManyChat API
- [ ] Guardar decisiones en Google Sheets
- [ ] Mejorar consulta PrestaShop: filtrar pedidos por estado
- [ ] Consultar stock de productos desde Telegram
- [ ] Consultar datos de un cliente específico

### 📅 Medio plazo
- [ ] Agente Community Manager completo:
  - Agente Redactor (copies Instagram + TikTok)
  - Agente Planificador (calendario editorial)
  - Agente Diseñador (prompts de imágenes)
  - Agente de Comunidad (respuestas automáticas)
  - Agente Analista (métricas)
  - Agente Orquestador (coordina todos)
- [ ] Conectar con Buffer/Later para publicación automática
- [ ] Integrar con Google Calendar

### 🔭 Largo plazo
- [ ] Template replicable para nuevos clientes/marcas
- [ ] Panel de control web completo para gestionar todos los agentes

---

## 📝 Notas Importantes

- Las claves API **nunca** se suben a GitHub, solo están en el `.env` del servidor
- El `app.mount("/", StaticFiles(...))` en `main.py` del panel **debe ir siempre al final** del archivo, después de todos los endpoints, o FastAPI no registra las rutas nuevas
- El entorno virtual es compartido por todos los servicios: `/root/SecretariaLooBe/entorno/`
- ManyChat requiere HTTPS para webhooks — el agente UGC se expone via nginx en `panel.loobeshop.es/ugc/`
- Las variables de ManyChat deben insertarse con el botón de variables del editor, no pegadas como texto plano
- GPT-4o-mini a veces devuelve JSON envuelto en ```json ... ``` — el agente limpia esto antes de parsear
- El JS del módulo UGC está incrustado directamente en `index.html` (no como archivo externo)
