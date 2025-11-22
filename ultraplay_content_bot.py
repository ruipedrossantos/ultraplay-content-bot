import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import NetworkError, TimedOut, TelegramError
import logging
import time
from datetime import datetime

# Configuração de logging mais detalhada
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÕES - PREENCHA AQUI =====
TELEGRAM_BOT_TOKEN = "8407027369:AAFKyTJ7JC6W8Hx3JdB1DznPg3uCWgQO1qE"
TMDB_API_KEY = "5c1ec82567d7036856c4e09aa60c8278"
CHANNEL_ID = "-1003262670465"
TOPIC_ID = 9
ADMIN_IDS = [7937632147]
# =========================================

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

def buscar_conteudo(query: str):
    """Busca filme ou série no TMDB com retry"""
    url = f"{TMDB_BASE_URL}/search/multi"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "pt-BR",
        "page": 1
    }
    
    max_retries = 3
    for tentativa in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            filtered = [r for r in results if r.get("media_type") in ["movie", "tv"]]
            return filtered[:5]
        except requests.Timeout:
            logger.warning(f"Timeout na tentativa {tentativa + 1}/{max_retries}")
            if tentativa < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo (tentativa {tentativa + 1}): {e}")
            if tentativa < max_retries - 1:
                time.sleep(2)
    
    return []

def obter_detalhes(media_type: str, media_id: int):
    """Obtém detalhes completos com retry"""
    url = f"{TMDB_BASE_URL}/{media_type}/{media_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "pt-BR",
        "append_to_response": "credits"
    }
    
    max_retries = 3
    for tentativa in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            logger.warning(f"Timeout ao obter detalhes (tentativa {tentativa + 1}/{max_retries})")
            if tentativa < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            logger.error(f"Erro ao obter detalhes (tentativa {tentativa + 1}): {e}")
            if tentativa < max_retries - 1:
                time.sleep(2)
    
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
    else:
        titulo = detalhes.get("name", "")
        titulo_original = detalhes.get("original_name", "")
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

def formatar_mensagem_atualizacao(detalhes: dict):
    """Formata a mensagem para anunciar novos episódios"""
    
    titulo = detalhes.get("name", "")
    titulo_original = detalhes.get("original_name", "")
    data = detalhes.get("first_air_date", "")
    ano = data.split("-")[0] if data else "N/A"
    rating = detalhes.get("vote_average", 0)
    sinopse = detalhes.get("overview", "Sinopse não disponível.")
    num_seasons = detalhes.get("number_of_seasons", 0)
    
    generos = [g["name"] for g in detalhes.get("genres", [])]
    generos_str = ", ".join(generos[:3]) if generos else "N/A"
    
    ultima_temporada = detalhes.get("last_episode_to_air", {})
    season_number = ultima_temporada.get("season_number", num_seasons)
    episode_number = ultima_temporada.get("episode_number", "?")
    
    mensagem = f"""╔═══════════════════════╗
║   📺 <b>ULTRAPLAY NEWS</b>   ║
╚═══════════════════════╝

🆕 <b>NOVOS EPISÓDIOS</b>

━━━━━━━━━━━━━━━━━━━━
📺 <b>{titulo.upper()}</b>
━━━━━━━━━━━━━━━━━━━━

⭐ <b>{rating:.1f}</b>/10 | 🎭 {generos_str}
📅 {ano} | 📚 {num_seasons} temporada{'s' if num_seasons > 1 else ''}

🔥 <b>Novos episódios disponíveis!</b>
📺 Temporada {season_number}

🌍 Legendas: PT

📖 <b>Sobre a série:</b>
<i>{sinopse[:200]}{'...' if len(sinopse) > 200 else ''}</i>

━━━━━━━━━━━━━━━━━━━━
💎 Qualidade: <b>Full HD</b>
🔊 Áudio: <b>Original</b>
✅ Disponível: <b>AGORA</b>
━━━━━━━━━━━━━━━━━━━━

🔥 <b>ULTRAPLAY</b> | Seu entretenimento premium
🌐 Assine já!"""

    return mensagem

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    try:
        user_id = update.effective_user.id
        
        if ADMIN_IDS and user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Você não tem permissão para usar este bot.")
            return
        
        mensagem = """🎬 <b>Bot de Conteúdo UltraPlay</b>

Comandos disponíveis:

/adicionar <i>nome do filme ou série</i>
<b>Exemplo:</b> /adicionar Gladiador 2

/atualizar <i>nome da série</i>
<b>Exemplo:</b> /atualizar Breaking Bad
(Para anunciar novos episódios)

O bot vai buscar o conteúdo e você escolhe qual postar no canal!

━━━━━━━━━━━━━━━━━━━━
🔥 <b>ULTRAPLAY</b> - Gestão de Conteúdo"""
        
        await update.message.reply_text(mensagem, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Erro no comando start: {e}")

async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /adicionar para buscar e postar conteúdo"""
    try:
        user_id = update.effective_user.id
        
        if ADMIN_IDS and user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Use: /adicionar <i>nome do filme ou série</i>\n\n"
                "<b>Exemplo:</b> /adicionar Gladiador 2",
                parse_mode=ParseMode.HTML
            )
            return
        
        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 Buscando: <b>{query}</b>...", parse_mode=ParseMode.HTML)
        
        resultados = buscar_conteudo(query)
        
        if not resultados:
            await update.message.reply_text(
                f"❌ Nenhum resultado encontrado para: <b>{query}</b>\n\n"
                "Tente outro nome ou verifique a ortografia.",
                parse_mode=ParseMode.HTML
            )
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
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📋 <b>Selecione o conteúdo para postar:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Erro no comando adicionar: {e}")
        try:
            await update.message.reply_text("❌ Erro ao processar comando. Tente novamente.")
        except:
            pass

async def atualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /atualizar para anunciar novos episódios de séries"""
    try:
        user_id = update.effective_user.id
        
        if ADMIN_IDS and user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Use: /atualizar <i>nome da série</i>\n\n"
                "<b>Exemplo:</b> /atualizar Breaking Bad",
                parse_mode=ParseMode.HTML
            )
            return
        
        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 Buscando série: <b>{query}</b>...", parse_mode=ParseMode.HTML)
        
        resultados = buscar_conteudo(query)
        series = [r for r in resultados if r.get("media_type") == "tv"]
        
        if not series:
            await update.message.reply_text(
                f"❌ Nenhuma série encontrada para: <b>{query}</b>\n\n"
                "Tente outro nome ou verifique a ortografia.",
                parse_mode=ParseMode.HTML
            )
            return
        
        keyboard = []
        for resultado in series:
            media_id = resultado.get("id")
            titulo = resultado.get("name", "")
            ano = resultado.get("first_air_date", "")[:4]
            
            texto_botao = f"📺 {titulo} ({ano})"
            callback_data = f"update_{media_id}"
            
            keyboard.append([InlineKeyboardButton(texto_botao, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📋 <b>Selecione a série para anunciar novos episódios:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Erro no comando atualizar: {e}")
        try:
            await update.message.reply_text("❌ Erro ao processar comando. Tente novamente.")
        except:
            pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dos botões de seleção"""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancelar":
            await query.edit_message_text("❌ Operação cancelada.")
            return
        
        parts = query.data.split("_")
        
        if len(parts) == 2 and parts[0] == "update":
            media_id = int(parts[1])
            
            await query.edit_message_text("⏳ Preparando anúncio de novos episódios...")
            
            detalhes = obter_detalhes("tv", media_id)
            
            if not detalhes:
                await query.edit_message_text("❌ Erro ao obter detalhes da série.")
                return
            
            mensagem = formatar_mensagem_atualizacao(detalhes)
            
            poster_path = detalhes.get("poster_path")
            if poster_path:
                imagem_url = f"{TMDB_IMAGE_BASE}{poster_path}"
            else:
                imagem_url = None
            
            try:
                if imagem_url:
                    await context.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=imagem_url,
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
                
                titulo = detalhes.get("name")
                await query.edit_message_text(
                    f"✅ Atualização de <b>{titulo}</b> foi postada no canal com sucesso! 🎉",
                    parse_mode=ParseMode.HTML
                )
                
            except Exception as e:
                logger.error(f"Erro ao postar no canal: {e}")
                await query.edit_message_text(
                    f"❌ Erro ao postar no canal.\n\n"
                    f"Detalhes: {str(e)}"
                )
            return
        
        if len(parts) != 3 or parts[0] != "post":
            await query.edit_message_text("❌ Erro ao processar seleção.")
            return
        
        media_type = parts[1]
        media_id = int(parts[2])
        
        await query.edit_message_text("⏳ Preparando publicação...")
        
        detalhes = obter_detalhes(media_type, media_id)
        
        if not detalhes:
            await query.edit_message_text("❌ Erro ao obter detalhes do conteúdo.")
            return
        
        mensagem = formatar_mensagem(detalhes, media_type)
        
        poster_path = detalhes.get("poster_path")
        if poster_path:
            imagem_url = f"{TMDB_IMAGE_BASE}{poster_path}"
        else:
            imagem_url = None
        
        try:
            if imagem_url:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=imagem_url,
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
    except Exception as e:
        logger.error(f"Erro no button_callback: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
            )
    except:
        pass

def main():
    """Inicia o bot com recuperação automática"""
    
    if TELEGRAM_BOT_TOKEN == "SEU_TOKEN_DO_BOT_AQUI":
        print("❌ ERRO: Configure o TELEGRAM_BOT_TOKEN no arquivo!")
        print("Obtenha o token com @BotFather no Telegram")
        return
    
    if not ADMIN_IDS:
        print("⚠️ AVISO: Lista ADMIN_IDS vazia. Qualquer pessoa poderá usar o bot!")
    
    while True:
        try:
            logger.info(f"🤖 Iniciando bot... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("adicionar", adicionar))
            application.add_handler(CommandHandler("atualizar", atualizar))
            application.add_handler(CallbackQueryHandler(button_callback))
            
            # Adiciona handler de erros
            application.add_error_handler(error_handler)
            
            print("🤖 Bot iniciado! Aguardando comandos...")
            print(f"📺 Canal configurado: {CHANNEL_ID}")
            print(f"📌 Tópico: Novidades VOD (ID: {TOPIC_ID})")
            print(f"🔑 TMDB API: Configurada")
            print("\nPressione Ctrl+C para parar o bot.\n")
            
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                pool_timeout=30,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot parado pelo usuário")
            break
            
        except NetworkError as e:
            logger.error(f"❌ Erro de rede: {e}")
            logger.info("🔄 Reconectando em 10 segundos...")
            time.sleep(10)
            
        except TimedOut as e:
            logger.error(f"❌ Timeout: {e}")
            logger.info("🔄 Reconectando em 10 segundos...")
            time.sleep(10)
            
        except TelegramError as e:
            logger.error(f"❌ Erro do Telegram: {e}")
            logger.info("🔄 Reconectando em 15 segundos...")
            time.sleep(15)
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            logger.info("🔄 Reiniciando em 20 segundos...")
            time.sleep(20)

if __name__ == "__main__":
    main()
