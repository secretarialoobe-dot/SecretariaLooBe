# 🤖 Proyecto: SecretariaLooBe — Ecosistema Multi-Agente

## 📌 Resumen del Proyecto
Sistema de agentes de IA construido para automatizar tareas de negocio. El 
objetivo final es tener un ecosistema completo de agentes especializados, 
incluyendo un Community Manager autónomo para una marca de moda joven 
(fast fashion) en Instagram y TikTok.

---

## 🖥️ Infraestructura

| Elemento | Detalle |
|---|---|
| **Servidor** | Hetzner VPS — IP: 178.104.195.224 |
| **OS** | Ubuntu 24 |
| **Repositorio** | github.com/secretarialoobe-dot/SecretariaLooBe |
| **Coste servidor** | ~4,90€/mes |
| **Gestor de servicios** | systemd (los bots corren 24/7 automáticamente) 
|

---

## 🤖 Agentes Activos

### 1. SecreLooBe (`secretaria.py`)
- **Canal:** Telegram
- **Usuario:** Mujer del propietario (tienda LooBe Shop)
- **Funciones actuales:**
  - Conversación general con IA (Claude/GPT)
  - Búsqueda web en tiempo real (DuckDuckGo)
  - Respuesta por voz (gTTS)
  - Reconocimiento de voz
  - **Consulta de pedidos PrestaShop** en tiempo real:
    - Muestra pedidos nuevos desde la última consulta
    - Muestra artículos de cada pedido
    - Muestra importe de cada pedido
    - Muestra total facturado del día natural completo
- **Servicio:** `systemctl status secretaria`

### 2. Torrente (`Torrente.py`)
- **Canal:** Telegram
- **Funciones actuales:** Conversación general con IA
- **Servicio:** `systemctl status torrente`

---

## 🏪 Integración PrestaShop

| Elemento | Detalle |
|---|---|
| **Tienda** | loobeshop.com |
| **API activada** | Sí (Webservice) |
| **Clave API** | En archivo `.env` del servidor |
| **Permisos** | GET en orders, products, customers |
| **Funciones activas** | Pedidos nuevos desde última consulta + total día 
|

---

## 📁 Estructura del Proyecto

```
SecretariaLooBe/
├── secretaria.py        # Bot secretaria con integración PrestaShop
├── Torrente.py          # Bot Torrente
├── requirements.txt     # Dependencias Python
├── .gitignore           # Excluye .env y entorno virtual
└── CONTEXTO.md          # Este archivo
```

### En el servidor (no en GitHub):
```
/root/SecretariaLooBe/
├── .env                 # Claves API (NUNCA subir a GitHub)
└── entorno/             # Entorno virtual Python 3.12
```

---

## 🔑 Variables de Entorno (`.env`)

```
TELEGRAM_TOKEN=token_de_secretaria
TELEGRAM_TOKEN_TORRENTE=token_de_torrente
OPENAI_API_KEY=clave_openai
PRESTA_KEY=clave_api_prestashop
PRESTA_URL=https://loobeshop.com
```

---

## 🧰 Stack Tecnológico

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.12 |
| IA | OpenAI GPT-4o-mini + Anthropic Claude |
| Telegram | python-telegram-bot 22.7 |
| Voz | gTTS + SpeechRecognition |
| Búsqueda web | DuckDuckGo Search |
| E-commerce | PrestaShop API (REST) |
| Servidor | Hetzner VPS Ubuntu 24 |
| Servicios | systemd |
| Repositorio | GitHub |

---

## 🗺️ Hoja de Ruta — Próximos Pasos

### Corto plazo (próximas sesiones)
- [ ] Mejorar consulta PrestaShop: filtrar pedidos por estado (pendiente, 
enviado, etc.)
- [ ] Consultar stock de productos desde Telegram
- [ ] Consultar datos de un cliente específico

### Medio plazo
- [ ] Construir Agente Community Manager para marca de moda joven
  - Agente Redactor (copies Instagram + TikTok)
  - Agente Planificador (calendario editorial)
  - Agente Diseñador (prompts de imágenes)
  - Agente de Comunidad (respuestas automáticas)
  - Agente Analista (métricas)
  - Agente Orquestador (coordina todos)
- [ ] Conectar con Buffer/Later para publicación automática
- [ ] Integrar con Google Calendar para agenda

### Largo plazo
- [ ] Template replicable para nuevos clientes/marcas
- [ ] Panel de control web para gestionar todos los agentes

---

## 🚀 Comandos Útiles del Servidor

```bash
# Conectarse al servidor
ssh root@178.104.195.224

# Ver estado de los bots
systemctl status secretaria torrente

# Reiniciar un bot
systemctl restart secretaria
systemctl restart torrente

# Ver logs en tiempo real
journalctl -u secretaria -f
journalctl -u torrente -f

# Actualizar código desde GitHub
cd /root/SecretariaLooBe
git pull origin main
systemctl restart secretaria torrente
```

---

## 📝 Notas Importantes

- Las claves API **nunca** se suben a GitHub, solo están en el `.env` del 
servidor
- El archivo `.env` está protegido por `.gitignore`
- Cada bot tiene su propio token de Telegram
- Los bots se reinician automáticamente si hay un error (gracias a systemd 
`Restart=always`)
- Python 3.12 en entorno virtual en `/root/SecretariaLooBe/entorno/`

