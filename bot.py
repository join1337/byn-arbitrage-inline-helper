import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent
import requests
import threading
from flask import Flask
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "bot worked"

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
# --------------------------------------

CURRENCIES = {
    'BYN': '🇧🇾',
    'USD': '🇺🇸',
    'EUR': '🇪🇺',
    'RUB': '🇷🇺',
    'PLN': '🇵🇱',
    'CNY': '🇨🇳',
    'KZT': '🇰🇿',
    'UAH': '🇺🇦'
}

FLAGS_CODES = {
    'BYN': 'by',
    'USD': 'us',
    'EUR': 'eu',
    'RUB': 'ru',
    'PLN': 'pl',
    'CNY': 'cn',
    'KZT': 'kz',
    'UAH': 'ua'
}

ALIASES = {
    'usd': 'USD', '$': 'USD', 'dollar': 'USD', 'dollars': 'USD', 'доллар': 'USD', 'долларов': 'USD', 'баксов': 'USD',
    'eur': 'EUR', 'euro': 'EUR', 'евро': 'EUR', '€': 'EUR',
    'rub': 'RUB', 'руб': 'RUB', 'р': 'RUB', 'рублей': 'RUB', 'рубль': 'RUB',
    'pln': 'PLN', 'зл': 'PLN', 'злотых': 'PLN', 'злотый': 'PLN',
    'cny': 'CNY', 'юань': 'CNY', 'юаней': 'CNY',
    'kzt': 'KZT', 'kz': 'KZT', 'тг': 'KZT', 'тенге': 'KZT',
    'byn': 'BYN', 'бун': 'BYN', 'бел': 'BYN', 'зайцев': 'BYN',
    'uah': 'UAH', 'ua': 'UAH', 'грн': 'UAH', 'гривна': 'UAH', 'гривны': 'UAH', 'гривен': 'UAH'
}

def get_all_rates():
    url = "https://api.nbrb.by/exrates/rates?periodicity=0"
    try:
        response = requests.get(url).json()
        rates = {'BYN': {'rate': 1.0, 'scale': 1}}
        for item in response:
            abbr = item['Cur_Abbreviation']
            if abbr in CURRENCIES:
                rates[abbr] = {
                    'rate': item['Cur_OfficialRate'],
                    'scale': item['Cur_Scale']
                }
        return rates
    except Exception as e:
        print("Ошибка API:", e)
        return None

@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    parts = inline_query.query.strip().lower().split()
    try:
        amount = float(parts[0].replace(',', '.'))
    except ValueError:
        return

    base_currency = 'BYN'
    if len(parts) > 1:
        base_currency = ALIASES.get(parts[1], 'BYN')

    rates = get_all_rates()
    if not rates:
        return

    results = []
    
    if base_currency == 'BYN':
        amount_in_byn = amount
    else:
        base_rate = rates[base_currency]['rate']
        base_scale = rates[base_currency]['scale']
        amount_in_byn = (amount / base_scale) * base_rate

    for index, (currency, flag) in enumerate(CURRENCIES.items()):
        if currency == base_currency:
            continue
            
        if currency in rates:
            target_rate = rates[currency]['rate']
            target_scale = rates[currency]['scale']
            amount_target = (amount_in_byn / target_rate) * target_scale
            
            short_desc = f"{amount:g} {base_currency} = {amount_target:.2f} {currency}"
            full_text = f"💱 Конвертация:\n*{short_desc}* {flag}\n_По курсу НБРБ_"
            
            country_code = FLAGS_CODES.get(currency, 'by')
            flag_icon_url = f"https://flagcdn.com/w160/{country_code}.png"
            
            item = InlineQueryResultArticle(
                id=str(index),
                title=f"В {currency} {flag}",
                description=short_desc,
                thumbnail_url=flag_icon_url,
                thumbnail_width=48,
                thumbnail_height=36,
                input_message_content=InputTextMessageContent(
                    message_text=full_text,
                    parse_mode="Markdown"
                )
            )
            results.append(item)

    bot.answer_inline_query(inline_query.id, results, cache_time=5)

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()

    print("100%")
    bot.remove_webhook()
    bot.polling(none_stop=True)
