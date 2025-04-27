SPECIAL_QUESTIONS = {
    "tell me about you": "I'm just here to grind roles sir",
    "who are you": "offcourse i'm human and i'm just here to grind for roles and learn about momentum finance",
    "what are you": "i'm human hehe🤣",
    "are you a bot": "no i'm not this is my way of talk sir🥲",
    "zenitsu is bot": "no i'm not this is my way of talk sir🥲",
}

def is_special_question(message):
    clean_message = message.lower().strip()
    for key in SPECIAL_QUESTIONS:
        if key in clean_message:
            return SPECIAL_QUESTIONS[key]
    return None

import shareithub
import json
import threading
import time
import os
import random
import re
import requests
from shareithub import shareithub
from dotenv import load_dotenv
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()

discord_tokens_env = os.getenv('DISCORD_TOKENS', '')
if discord_tokens_env:
    discord_tokens = [token.strip() for token in discord_tokens_env.split(',') if token.strip()]
else:
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        raise ValueError("Tidak ada Discord token yang ditemukan! Harap atur DISCORD_TOKENS atau DISCORD_TOKEN di .env.")
    discord_tokens = [discord_token]

google_api_keys = os.getenv('GOOGLE_API_KEYS', '').split(',')
google_api_keys = [key.strip() for key in google_api_keys if key.strip()]
if not google_api_keys:
    raise ValueError("Tidak ada Google API Key yang ditemukan! Harap atur GOOGLE_API_KEYS di .env.")

processed_message_ids = set()
used_api_keys = set()
last_generated_text = None
cooldown_time = 86400

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if level.upper() == "SUCCESS":
        color, icon = Fore.GREEN, "✅"
    elif level.upper() == "ERROR":
        color, icon = Fore.RED, "🚨"
    elif level.upper() == "WARNING":
        color, icon = Fore.YELLOW, "⚠️"
    elif level.upper() == "WAIT":
        color, icon = Fore.CYAN, "⌛"
    else:
        color, icon = Fore.WHITE, "ℹ️"

    border = f"{Fore.MAGENTA}{'=' * 80}{Style.RESET_ALL}"
    formatted_message = f"{color}[{timestamp}] {icon} {message}{Style.RESET_ALL}"
    print(border)
    print(formatted_message)
    print(border)

def get_random_api_key():
    available_keys = [key for key in google_api_keys if key not in used_api_keys]
    if not available_keys:
        log_message("Semua API key terkena error 429. Menunggu 24 jam sebelum mencoba lagi...", "ERROR")
        time.sleep(cooldown_time)
        used_api_keys.clear()
        return get_random_api_key()
    return random.choice(available_keys)

def get_random_message_from_file():
    try:
        with open("pesan.txt", "r", encoding="utf-8") as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            return random.choice(messages) if messages else "Tidak ada pesan tersedia di file."
    except FileNotFoundError:
        return "File pesan.txt tidak ditemukan!"

def generate_language_specific_prompt(user_message, prompt_language):
    if prompt_language == 'id':
        return f"Balas pesan berikut dalam bahasa Indonesia: {user_message}"
    elif prompt_language == 'en':
        return f"Reply to the following message in English: {user_message}"
    else:
        log_message(f"Bahasa prompt '{prompt_language}' tidak valid. Pesan dilewati.", "WARNING")
        return None

def generate_reply(prompt, prompt_language, use_google_ai=True):
    global last_generated_text
    if use_google_ai:
        google_api_key = get_random_api_key()
        lang_prompt = generate_language_specific_prompt(prompt, prompt_language)
        if lang_prompt is None:
            return None
        ai_prompt = f"{lang_prompt}\n\nBuatlah menjadi 1 kalimat menggunakan bahasa sehari hari manusia."
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={google_api_key}'
        headers = {'Content-Type': 'application/json'}
        data = {'contents': [{'parts': [{'text': ai_prompt}]}]}
        while True:
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 429:
                    log_message(f"API key {google_api_key} terkena rate limit (429). Menggunakan API key lain...", "WARNING")
                    used_api_keys.add(google_api_key)
                    return generate_reply(prompt, prompt_language, use_google_ai)
                response.raise_for_status()
                result = response.json()
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                if generated_text == last_generated_text:
                    log_message("AI menghasilkan teks yang sama, meminta teks baru...", "WAIT")
                    continue
                last_generated_text = generated_text
                return generated_text
            except requests.exceptions.RequestException as e:
                log_message(f"Request failed: {e}", "ERROR")
                time.sleep(2)
    else:
        return get_random_message_from_file()

def get_channel_info(channel_id, token):
    headers = {'Authorization': token}
    channel_url = f"https://discord.com/api/v9/channels/{channel_id}"
    try:
        channel_response = requests.get(channel_url, headers=headers)
        channel_response.raise_for_status()
        channel_data = channel_response.json()
        channel_name = channel_data.get('name', 'Unknown Channel')
        guild_id = channel_data.get('guild_id')
        server_name = "Direct Message"
        if guild_id:
            guild_url = f"https://discord.com/api/v9/guilds/{guild_id}"
            guild_response = requests.get(guild_url, headers=headers)
            guild_response.raise_for_status()
            guild_data = guild_response.json()
            server_name = guild_data.get('name', 'Unknown Server')
        return server_name, channel_name
    except requests.exceptions.RequestException as e:
        log_message(f"Error mengambil info channel: {e}", "ERROR")
        return "Unknown Server", "Unknown Channel"

def get_bot_info(token):
    headers = {'Authorization': token}
    try:
        response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        response.raise_for_status()
        data = response.json()
        username = data.get("username", "Unknown")
        discriminator = data.get("discriminator", "")
        bot_id = data.get("id", "Unknown")
        return username, discriminator, bot_id
    except requests.exceptions.RequestException as e:
        log_message(f"Gagal mengambil info akun bot: {e}", "ERROR")
        return "Unknown", "", "Unknown"

def auto_reply(channel_id, settings, token):
    headers = {'Authorization': token}
    if settings["use_google_ai"]:
        try:
            bot_info_response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
            bot_info_response.raise_for_status()
            bot_user_id = bot_info_response.json().get('id')
        except requests.exceptions.RequestException as e:
            log_message(f"[Channel {channel_id}] Gagal mengambil info bot: {e}", "ERROR")
            return

        while True:
            prompt = None
            reply_to_id = None
            log_message(f"[Channel {channel_id}] Menunggu {settings['read_delay']} detik sebelum membaca pesan...", "WAIT")
            time.sleep(settings["read_delay"])
            try:
                response = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', headers=headers)
                response.raise_for_status()
                messages = response.json()
                if messages:
                    most_recent_message = messages[0]
                    message_id = most_recent_message.get('id')
                    author_id = most_recent_message.get('author', {}).get('id')
                    message_type = most_recent_message.get('type', '')
                    if author_id != bot_user_id and message_type != 8 and message_id not in processed_message_ids:
                        user_message = most_recent_message.get('content', '').strip()
                        attachments = most_recent_message.get('attachments', [])
                        if attachments or not re.search(r'\w', user_message):
                            log_message(f"[Channel {channel_id}] Pesan tidak diproses (bukan teks murni).", "WARNING")
                        else:
                            log_message(f"[Channel {channel_id}] Received: {user_message}", "INFO")
                            if settings["use_slow_mode"]:
                                slow_mode_delay = get_slow_mode_delay(channel_id, token)
                                log_message(f"[Channel {channel_id}] Slow mode aktif, menunggu {slow_mode_delay} detik...", "WAIT")
                                time.sleep(slow_mode_delay)
                            prompt = user_message
                            reply_to_id = message_id
                            processed_message_ids.add(message_id)
                else:
                    prompt = None
            except requests.exceptions.RequestException as e:
                log_message(f"[Channel {channel_id}] Request error: {e}", "ERROR")
                prompt = None

            if prompt:
                result = generate_reply(prompt, settings["prompt_language"], settings["use_google_ai"])
                if result is None:
                    log_message(f"[Channel {channel_id}] Bahasa prompt tidak valid. Pesan dilewati.", "WARNING")
                else:
                    response_text = result if result else "Maaf, tidak dapat membalas pesan."
                    if response_text.strip().lower() == prompt.strip().lower():
                        log_message(f"[Channel {channel_id}] Balasan sama dengan pesan yang diterima. Tidak mengirim balasan.", "WARNING")
                    else:
                        if settings["use_reply"]:
                            send_message(channel_id, response_text, token, reply_to=reply_to_id, 
                                         delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])
                        else:
                            send_message(channel_id, response_text, token, 
                                         delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])
            else:
                log_message(f"[Channel {channel_id}] Tidak ada pesan baru atau pesan