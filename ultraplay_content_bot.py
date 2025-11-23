import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import requests
import logging
from flask import Flask
from threading import Thread
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURAÇÕES
TOKEN = "8407027369:AAFKyTJ7JC6W8Hx3JdB1DznPg3uCWgQO1qE"
TMDB_KEY = "5c1ec82567d7036856c4e09aa60c8278"
CHANNEL = "-1003262670465"
TOPIC = 9
ADMINS = [7937632147]

# Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Online"

@app.route('/status')
def status():
    return {"status": "ok"}

def buscar(query):
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/search/multi",
            params={"api_key": TMDB_KEY, "query": query, "language": "pt-BR"},
            timeout=10
        )
        return [x for x in r.json().get("results", []) if x.get("media_type") in ["movie", "tv"]][:5]
    except:
        return []

def detalhes(tipo, id):
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/{tipo}/{id}",
            params={"api_key": TMDB_KEY, "language": "pt-BR"},
            timeout=10
        )
        return r.json()
    except:
        return None

def formatar(d, tipo):
    titulo = d.get("title" if tipo == "movie" else "name", "")
    data = d.get("release_date" if tipo == "movie" else "first_air_date", "")
    ano = data[:4] if data else "N/A"
    rating = d.get("vote_average", 0)
    sinopse = d.get("overview", "Sinopse não disponível.")
    generos = ", ".join([g["name"] for g in d.get("genres", [])][:3]) or "N/A"
    
    emoji = "🎬" if tipo == "movie" else "📺"
    nome = "FILME" if tipo == "movie" else "SÉRIE"
    
    msg = f"""╔═══════════════════════╗
║   {emoji} <b>ULTRAPLAY NEWS</b>   ║
╚═══════════════════════╝

🆕 <b>{nome} ADICIONADO</b>

━━━━━━━━━━━━━━━━━━━━
📺 <b>{titulo.upper()}</b>
━━━━━━━━━━━━━━━━━━━━

⭐ <b>{rating:.1f}</b>/10 | 🎭 {generos}
📅 {ano}"""
    
    if tipo == "movie":
        dur = d.get("runtime", 0)
        if dur:
            msg += f" | ⏱️ {dur//60}h {dur%60}min"
    else:
        temp = d.get("number_of_seasons", 0)
        if temp:
            msg += f" | 📚 {temp} temp"
    
    msg += f"""
🌍 Legendas: PT

📖 <b>Sinopse:</b>
<i>{sinopse[:250]}{'...' if len(sinopse) > 250 else ''}</i>

━━━━━━━━━━━━━━━━━━━━
💎 Qualidade: <b>Full HD</b>
🔊 Áudio: <b>Original</b>
✅ Disponível: <b>AGORA</b>
━━━━━━━━━━━━━━━━━━━━

🔥 <b>ULTRAPLAY</b> | Seu entretenimento premium
🌐 Assine já!"""
    return msg

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id not in ADMINS:
        await u.message.reply_text("❌ Sem permissão")
        return
    await u.message.reply_text("🎬 <b>Bot UltraPlay</b>\n\n/adicionar <i>nome</i>", parse_mode=ParseMode.HTML)

async def adicionar(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id not in ADMINS:
        await u.message.reply_text("❌ Sem permissão")
        return
    
    if not c.args:
        await u.message.reply_text("❌ Use: /adicionar <i>nome</i>", parse_mode=ParseMode.HTML)
        return
    
    q = " ".join(c.args)
    await u.message.reply_text(f"🔍 <b>{q}</b>...", parse_mode=ParseMode.HTML)
    
    res = buscar(q)
    if not res:
        await u.message.reply_text("❌ Nada encontrado")
        return
    
    kb = []
    for r in res:
        t = r.get("media_type")
        i = r.get("id")
        tit = r.get("title" if t == "movie" else "name", "")
        ano = (r.get("release_date" if t == "movie" else "first_air_date", ""))[:4]
        em = "🎬" if t == "movie" else "📺"
        kb.append([InlineKeyboardButton(f"{em} {tit} ({ano})", callback_data=f"p_{t}_{i}")])
    
    kb.append([InlineKeyboardButton("❌ Cancelar", callback_data="x")])
    await u.message.reply_text("📋 Escolha:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def callback(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    
    if q.data == "x":
        await q.edit_message_text("❌ Cancelado")
        return
    
    p = q.data.split("_")
    if len(p) != 3:
        await q.edit_message_text("❌ Erro")
        return
    
    tipo = p[1]
    mid = int(p[2])
    
    await q.edit_message_text("⏳ Postando...")
    
    d = detalhes(tipo, mid)
    if not d:
        await q.edit_message_text("❌ Erro")
        return
    
    msg = formatar(d, tipo)
    poster = d.get("poster_path")
    
    try:
        if poster:
            await c.bot.send_photo(
                CHANNEL,
                f"https://image.tmdb.org/t/p/original{poster}",
                caption=msg,
                parse_mode=ParseMode.HTML,
                message_thread_id=TOPIC
            )
        else:
            await c.bot.send_message(CHANNEL, msg, parse_mode=ParseMode.HTML, message_thread_id=TOPIC)
        
        tit = d.get("title") or d.get("name")
        await q.edit_message_text(f"✅ <b>{tit}</b> postado!", parse_mode=ParseMode.HTML)
    except Exception as e:
        await q.edit_message_text(f"❌ {e}")

def bot():
    logger.info("BOT: Iniciando...")
    a = Application.builder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    a.add_handler(CommandHandler("adicionar", adicionar))
    a.add_handler(CallbackQueryHandler(callback))
    logger.info("BOT: Handlers OK")
    logger.info("BOT: Polling...")
    a.run_polling(drop_pending_updates=True)
    logger.info("BOT: Rodando!")

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("SISTEMA INICIANDO")
    logger.info("="*50)
    
    # Bot
    t = Thread(target=bot, daemon=True)
    t.start()
    logger.info("Thread bot OK")
    
    # Espera bot iniciar
    time.sleep(5)
    
    # Flask
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Flask porta {port}")
    app.run(host="0.0.0.0", port=port)