import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURAÇÕES
TELEGRAM_BOT_TOKEN = "8407027369:AAFKyTJ7JC6W8Hx3JdB1DznPg3uCWgQO1qE"
TMDB_API_KEY = "5c1ec82567d7036856c4e09aa60c8278"
CHANNEL_ID = "-1003262670465"
TOPIC_ID = 9
ADMIN_IDS = [7937632147]

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

def buscar_conteudo(query: str):
    try:
        url = f"{TMDB_BASE_URL}/search/multi"
        params = {"api_key": TMDB_API_KEY, "query": query, "language": "pt-BR", "page": 1}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        results = response.json().get("results", [])
        return [r for r in results if r.get("media_type") in ["movie", "tv"]][:5]
    except:
        return []

def obter_detalhes(media_type: str, media_id: int):
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{media_id}"
        params = {"api_key": TMDB_API_KEY, "language": "pt-BR"}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except:
        return None

def formatar_mensagem(detalhes: dict, media_type: str):
    if media_type == "movie":
        titulo = detalhes.get("title", "")
        data = detalhes.get("release_date", "")
        duracao = detalhes.get("runtime", 0)
        tipo_emoji = "🎬"
        tipo_nome = "FILME"
    else:
        titulo = detalhes.get("name", "")
        data = detalhes.get("first_air_date", "")
        num_seasons = detalhes.get("number_of_seasons", 0)
        tipo_emoji = "📺"
        tipo_nome = "SÉRIE"
    
    ano = data.split("-")[0] if data else "N/A"
    rating = detalhes.get("vote_average", 0)
    sinopse = detalhes.get("overview", "Sinopse não disponível.")
    generos = [g["name"] for g in detalhes.get("genres", [])]
    generos_str = ", ".join(generos[:3]) if generos else "N/A"
    
    mensagem = f"""╔═══════════════════════╗
║   {tipo_emoji} <b>ULTRAPLAY NEWS</b>   ║
╚═══════════════════════╝

🆕 <b>{tipo_nome} ADICIONADO</b>

━━━━━━━━━━━━━━━━━━━━
📺 <b>{titulo.upper()}</b>
━━━━━━━━━━━━━━━━━━━━

⭐ <b>{rating:.1f}</b>/10 | 🎭 {generos_str}
📅 {ano}"""

    if media_type == "movie" and duracao:
        horas = duracao // 60
        minutos = duracao % 60
        mensagem += f" | ⏱️ {horas}h {minutos}min"
    elif media_type == "tv" and num_seasons:
        mensagem += f" | 📚 {num_seasons} temporada{'s' if num_seasons > 1 else ''}"
    
    mensagem += f"""
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
    return mensagem

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sem permissão.")
        return
    
    await update.message.reply_text(
        "🎬 <b>Bot UltraPlay</b>\n\n/adicionar <i>nome</i>\n\nExemplo: /adicionar Gladiador 2",
        parse_mode=ParseMode.HTML
    )

async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sem permissão.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Use: /adicionar <i>nome</i>", parse_mode=ParseMode.HTML)
        return
    
    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando: <b>{query}</b>...", parse_mode=ParseMode.HTML)
    
    resultados = buscar_conteudo(query)
    if not resultados:
        await update.message.reply_text("❌ Nada encontrado.", parse_mode=ParseMode.HTML)
        return
    
    keyboard = []
    for resultado in resultados:
        media_type = resultado.get("media_type")
        media_id = resultado.get("id")
        
        if media_type == "movie":
            titulo = resultado.get("title", "")
            ano = resultado.get("release_date", "")[:4]
            emoji = "🎬"
        else:
            titulo = resultado.get("name", "")
            ano = resultado.get("first_air_date", "")[:4]
            emoji = "📺"
        
        texto_botao = f"{emoji} {titulo} ({ano})"
        callback_data = f"post_{media_type}_{media_id}"
        keyboard.append([InlineKeyboardButton(texto_botao, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    await update.message.reply_text(
        "📋 <b>Escolha:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar":
        await query.edit_message_text("❌ Cancelado.")
        return
    
    parts = query.data.split("_")
    if len(parts) != 3:
        await query.edit_message_text("❌ Erro.")
        return
    
    media_type = parts[1]
    media_id = int(parts[2])
    
    await query.edit_message_text("⏳ Postando...")
    
    detalhes = obter_detalhes(media_type, media_id)
    if not detalhes:
        await query.edit_message_text("❌ Erro ao obter detalhes.")
        return
    
    mensagem = formatar_mensagem(detalhes, media_type)
    poster_path = detalhes.get("poster_path")
    
    try:
        if poster_path:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=f"{TMDB_IMAGE_BASE}{poster_path}",
                caption=mensagem,
                parse_mode=ParseMode.HTML,
                message_thread_id=TOPIC_ID
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=mensagem,
                parse_mode=ParseMode.HTML,
                message_thread_id=TOPIC_ID
            )
        
        titulo = detalhes.get("title") or detalhes.get("name")
        await query.edit_message_text(f"✅ <b>{titulo}</b> postado! 🎉", parse_mode=ParseMode.HTML)
    except Exception as e:
        await query.edit_message_text(f"❌ Erro: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adicionar", adicionar))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("🤖 Bot iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()