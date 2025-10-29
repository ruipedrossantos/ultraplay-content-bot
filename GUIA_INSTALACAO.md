# 🎬 UltraPlay Content Bot - Guia de Instalação

## 📋 O QUE VOCÊ PRECISA

1. ✅ API Key TMDB: 5c1ec82567d7036856c4e09aa60c8278 (JÁ TEM!)
2. ✅ ID do Canal: -1003262670465 (JÁ TEM!)
3. ❓ Token do Bot do Telegram (vou te ensinar)
4. ❓ Seu ID de usuário do Telegram (vou te ensinar)

---

## 🤖 PASSO 1: Criar o Bot no Telegram

1. Abra o Telegram e procure por: **@BotFather**

2. Mande o comando: `/newbot`

3. BotFather vai pedir:
   - **Nome do bot:** UltraPlay Content Manager (ou qualquer nome)
   - **Username do bot:** ultraplay_content_bot (deve terminar em "bot")

4. **COPIE O TOKEN** que ele te dá! Algo como:
   `7362481958:AAHfZQwE8xYz9K0pQaBcXtU_example_token`

5. Adicione o bot como **ADMINISTRADOR** no seu canal (-1003262670465)

---

## 🆔 PASSO 2: Descobrir Seu ID de Usuário

1. No Telegram, procure por: **@userinfobot**

2. Mande qualquer mensagem para ele

3. Ele vai responder com seu **ID** (um número tipo: 123456789)

4. **GUARDE ESSE NÚMERO!**

---

## ⚙️ PASSO 3: Configurar o Bot

Abra o arquivo `ultraplay_content_bot.py` e edite estas linhas:

```python
# Linha 17 - Cole o token que o BotFather te deu
TELEGRAM_BOT_TOKEN = "COLE_SEU_TOKEN_AQUI"

# Linha 20 - Cole seu ID de usuário
ADMIN_IDS = [SEU_ID_AQUI]  # Exemplo: [123456789]
```

**Exemplo de como deve ficar:**
```python
TELEGRAM_BOT_TOKEN = "7362481958:AAHfZQwE8xYz9K0pQaBcXtU_example"
ADMIN_IDS = [123456789]
```

---

## 🚀 HOSPEDAGEM GRÁTIS - OPÇÕES

### OPÇÃO 1: Railway (Recomendado - Grátis)
- Site: https://railway.app
- 500 horas/mês grátis
- Fácil de configurar
- Deploy direto do GitHub

### OPÇÃO 2: Render
- Site: https://render.com
- Grátis para sempre
- O serviço "dorme" após 15 min inativo
- Acorda automaticamente quando você usa

### OPÇÃO 3: PythonAnywhere
- Site: https://www.pythonanywhere.com
- Plano grátis disponível
- Mais manual mas funciona bem

### OPÇÃO 4: Seu PC/Raspberry Pi
- Deixa rodando 24/7
- Controle total
- Sem custos extras

---

## 💻 INSTALAÇÃO LOCAL (Testar primeiro)

### No Windows:
```bash
# Instalar Python 3.8+ (se não tiver)
# Download: https://www.python.org/downloads/

# No terminal (CMD ou PowerShell):
pip install -r requirements.txt
python ultraplay_content_bot.py
```

### No Linux/Mac:
```bash
pip3 install -r requirements.txt
python3 ultraplay_content_bot.py
```

---

## 🎯 COMO USAR

1. No Telegram, procure seu bot pelo username que criou

2. Mande: `/start`

3. Adicione conteúdo: `/adicionar Gladiador 2`

4. O bot mostra opções, você escolhe e ele posta!

---

## 🔥 EXEMPLO DE USO

```
Você: /adicionar breaking bad

Bot: 🔍 Buscando: breaking bad...

Bot: 📋 Selecione o conteúdo para postar:
     [📺 Breaking Bad (2008)]
     [📺 El Camino: Breaking Bad (2019)]
     [🎬 Breaking Bad: The Movie (2017)]
     [❌ Cancelar]

Você: [Clica em "Breaking Bad (2008)"]

Bot: ⏳ Preparando publicação...
Bot: ✅ Breaking Bad foi postado no canal com sucesso! 🎉
```

E no seu canal aparece um post lindo com:
- Capa em alta qualidade
- Informações completas
- Design profissional

---

## ❓ PRÓXIMOS PASSOS

1. Me confirma quando conseguir o TOKEN do bot
2. Me confirma seu ID de usuário
3. Escolhe onde quer hospedar
4. Eu te ajudo a fazer o deploy!

---

## 🆘 PRECISA DE AJUDA?

Me manda aqui que eu te ajudo em qualquer passo! 🚀
