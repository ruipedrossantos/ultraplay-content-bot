import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import logging

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÕES - PREENCHA AQUI =====
TELEGRAM_BOT_TOKEN = "8407027369:AAFKyTJ7JC6W8Hx3JdB1DznPg3uCWgQO1qE"  # Token do @BotFather
TMDB_API_KEY = "5c1ec82567d7036856c4e09aa60c8278"
CHANNEL_ID = "-1003262670465"  # Seu canal UltraPlay
TOPIC_ID = 9  # ID do tópico "Novidades VOD"
ADMIN_IDS = [7937632147]  # Lista de IDs de admin que podem usar o bot (ex: [123456789, 987654321])
# =========================================

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

def buscar_conteudo(query: str):
    """Busca filme ou série no TMDB"""
    url = f"{TMDB_BASE_URL}/search/multi"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "pt-BR",
        "page": 1
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        # Filtra apenas filmes e séries
        filtered = [r for r in results if r.get("media_type") in ["movie", "tv"]]
        return filtered[:5]  # Retorna até 5 resultados
    except Exception as e:
        logger.error(f"Erro ao buscar conteúdo: {e}")
        return []

def obter_detalhes(media_type: str, media_id: int):
    """Obtém detalhes completos do filme ou série"""
    url = f"{TMDB_BASE_URL}/{media_type}/{media_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "pt-BR",
        "append_to_response": "credits"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao obter detalhes: {e}")
        return None

def formatar_mensagem(detalhes: dict, media_type: str):
    """Formata a mensagem para postar no canal"""
    
    if media_type == "movie":
        titulo = detalhes.get("title", "")
        titulo_original = detalhes.get("original_title", "")
        data = detalhes.get("release_date", "")
        duracao = detalhes.get("runtime", 0)
        tipo_emoji = "🎬"
        tipo_nome = "FILME"
    else:  # tv
        titulo = detalhes.get("name", "")
        titulo_original = detalhes.get("original_name", "")
        data = detalhes.get("first_air_date", "")
        num_seasons = detalhes.get("number_of_seasons", 0)
        tipo_emoji = "📺"
        tipo_nome = "SÉRIE"
    
    ano = data.split("-")[0] if data else "N/A"
    rating = detalhes.get("vote_average", 0)
    sinopse = detalhes.get("overview", "Sinopse não disponível.")
    
    # Gêneros
    generos = [g["name"] for g in detalhes.get("genres", [])]
    generos_str = ", ".join(generos[:3]) if generos else "N/A"
    
    # Monta a mensagem
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
🌍 Legendas: PT, EN, ES

📖 <b>Sinopse:</b>
<i>{sinopse[:250]}{'...' if len(sinopse) > 250 else ''}</i>

━━━━━━━━━━━━━━━━━━━━
💎 Qualidade: <b>4K Ultra HD</b>
🔊 Áudio: <b>Multi-idioma</b>
✅ Disponível: <b>AGORA</b>
━━━━━━━━━━━━━━━━━━━━

🔥 <b>ULTRAPLAY</b> | Seu entretenimento premium
💬 @UltraPlayBot | 🌐 Assine já!"""

    return mensagem

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este bot.")
        return
    
    mensagem = """🎬 <b>Bot de Conteúdo UltraPlay</b>

Comandos disponíveis:

/adicionar <i>nome do filme ou série</i>
<b>Exemplo:</b> /adicionar Gladiador 2

O bot vai buscar o conteúdo e você escolhe qual postar no canal!

━━━━━━━━━━━━━━━━━━━━
🔥 <b>ULTRAPLAY</b> - Gestão de Conteúdo"""
    
    await update.message.reply_text(mensagem, parse_mode=ParseMode.HTML)

async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /adicionar para buscar e postar conteúdo"""
    user_id = update.effective_user.id
    
    # Verifica permissão
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    # Verifica se forneceu o nome
    if not context.args:
        await update.message.reply_text(
            "❌ Use: /adicionar <i>nome do filme ou série</i>\n\n"
            "<b>Exemplo:</b> /adicionar Gladiador 2",
            parse_mode=ParseMode.HTML
        )
        return
    
    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando: <b>{query}</b>...", parse_mode=ParseMode.HTML)
    
    # Busca no TMDB
    resultados = buscar_conteudo(query)
    
    if not resultados:
        await update.message.reply_text(
            f"❌ Nenhum resultado encontrado para: <b>{query}</b>\n\n"
            "Tente outro nome ou verifique a ortografia.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Cria botões com os resultados
    keyboard = []
    for resultado in resultados:
        media_type = resultado.get("media_type")
        media_id = resultado.get("id")
        
        if media_type == "movie":
            titulo = resultado.get("title", "")
            ano = resultado.get("release_date", "")[:4]
            emoji = "🎬"
        else:  # tv
            titulo = resultado.get("name", "")
            ano = resultado.get("first_air_date", "")[:4]
            emoji = "📺"
        
        texto_botao = f"{emoji} {titulo} ({ano})"
        callback_data = f"post_{media_type}_{media_id}"
        
        keyboard.append([InlineKeyboardButton(texto_botao, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📋 <b>Selecione o conteúdo para postar:</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dos botões de seleção"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar":
        await query.edit_message_text("❌ Operação cancelada.")
        return
    
    # Parse do callback_data: post_movie_12345 ou post_tv_67890
    parts = query.data.split("_")
    if len(parts) != 3 or parts[0] != "post":
        await query.edit_message_text("❌ Erro ao processar seleção.")
        return
    
    media_type = parts[1]
    media_id = int(parts[2])
    
    await query.edit_message_text("⏳ Preparando publicação...")
    
    # Obtém detalhes completos
    detalhes = obter_detalhes(media_type, media_id)
    
    if not detalhes:
        await query.edit_message_text("❌ Erro ao obter detalhes do conteúdo.")
        return
    
    # Formata mensagem
    mensagem = formatar_mensagem(detalhes, media_type)
    
    # URL da imagem (poster)
    poster_path = detalhes.get("poster_path")
    if poster_path:
        imagem_url = f"{TMDB_IMAGE_BASE}{poster_path}"
    else:
        imagem_url = None
    
    try:
        # Posta no canal no tópico específico
        if imagem_url:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=imagem_url,
                caption=mensagem,
                parse_mode=ParseMode.HTML,
                message_thread_id=TOPIC_ID  # Posta no tópico "Novidades VOD"
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=mensagem,
                parse_mode=ParseMode.HTML,
                message_thread_id=TOPIC_ID  # Posta no tópico "Novidades VOD"
            )
        
        titulo = detalhes.get("title") or detalhes.get("name")
        await query.edit_message_text(
            f"✅ <b>{titulo}</b> foi postado no canal com sucesso! 🎉",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Erro ao postar no canal: {e}")
        await query.edit_message_text(
            f"❌ Erro ao postar no canal.\n\n"
            f"Detalhes: {str(e)}"
        )

def main():
    """Inicia o bot"""
    
    # Verifica configurações
    if TELEGRAM_BOT_TOKEN == "SEU_TOKEN_DO_BOT_AQUI":
        print("❌ ERRO: Configure o TELEGRAM_BOT_TOKEN no arquivo!")
        print("Obtenha o token com @BotFather no Telegram")
        return
    
    if not ADMIN_IDS:
        print("⚠️ AVISO: Lista ADMIN_IDS vazia. Qualquer pessoa poderá usar o bot!")
        print("Adicione seu ID de usuário na lista ADMIN_IDS para restringir o acesso.")
    
    # Cria aplicação
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("adicionar", adicionar))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Inicia o bot
    print("🤖 Bot iniciado! Aguardando comandos...")
    print(f"📺 Canal configurado: {CHANNEL_ID}")
    print(f"📌 Tópico: Novidades VOD (ID: {TOPIC_ID})")
    print(f"🔑 TMDB API: Configurada")
    print("\nPressione Ctrl+C para parar o bot.\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
