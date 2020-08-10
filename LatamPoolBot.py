import logging
import webbrowser
import json
import datetime

from telegram import *
from telegram.ext import *

class UserData(object):
    def __init__(self):
        self._current_data = json.loads(read_file())

    def update_data(self, data, username):
        info = self._current_data.get(username, {}).get('info', {})
        info.update(data)
        if 'Fecha de registro' not in info:
            info['Fecha de registro'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data = self._current_data.get(username, {})
        user_data.update({'info': info})
        self._current_data.update({username: user_data})
        print("\n Datos actualizados: ", self._current_data)

    def get_data(self):
        return self._current_data

    def get_user_info(self, username):
        return self._current_data.get(username, {}).get('info', {})

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

_FILE_NAME = 'delegators.txt'

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

Inline_board =  [[InlineKeyboardButton("\u26A0 BUSCA TU DIRECCION DE STAKE AQUI \u26A0", url='https://pooltool.io/pool/c922da2949ca73c3300326dc5f9dc4cb39cf6c855ab8256dffdb9289/delegators')]]
markup2 = InlineKeyboardMarkup(Inline_board)
reply_keyboard = [['Direccion de Stake', 'Direccion de Cardano'],
                  ["Referente (Usuario de telegram)",'Nombre de usuario'],
                  ['Hecho']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

def read_file(file_name=_FILE_NAME):
    file_to_read = open(file_name, "r")
    data = file_to_read.read()
    file_to_read.close()
    return data


def write_file(data, file_name=_FILE_NAME):
    with open(file_name, 'w') as file_to_write:
        file_to_write.write(data)
    file_to_write.close()


def update_user_information(current_data, username, info):
    current_data[username] = info
    return current_data


def write_user_data(username, info):
    current_data = json.loads(read_file())
    data = json.dumps(update_user_information(current_data, username, info))
    write_file(data)


def insert_json(telegram_name, chat_id, info=None):
    user_info = {
        'chat_id': chat_id,
        'info': info,
        'updated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    write_user_data(telegram_name, user_info)


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(update, context):
    user = update.message.from_user
    update.message.reply_text(
        "¡Hola! Bienvenido a Cardano Latam Pool, {}. "
        "Para poder participar en recomensas por favor llena esta información. "
        "ADVERTENCIA: Nunca te pediremos tu dirección privada. "
        "Si tienes dudas contactar a un administrador del grupo de telegram https://t.me/joinchat/NFPHBAvdIx162AoNnibCXg".format (user['username']),
       # reply_markup=InlineKeyboardMarkup(keyboard),
        reply_markup=markup)
    update.message.reply_text('Si no sabes tu dirección de stake verifica este link',
                              reply_markup=markup2)

    return CHOOSING


def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Por favor indica tu {} en la siguiente línea. No proporciones '.format(text.lower()))

    return TYPING_REPLY

def received_information(current_data):
    def function(update, context):
        user = update.message.from_user
        user_data = context.user_data
        text = update.message.text
        category = user_data['choice']
        user_data[category] = text
        del user_data['choice']

        current_data.update_data(user_data, user['username'])

        update.message.reply_text("Gracias, por favor verifica que los datos sean correctos"
                                "{}Para guardar los datos presiona el botón hecho.".format(facts_to_str(current_data.get_user_info(user['username']))),
                                reply_markup=markup)

        return CHOOSING
    
    return function


def done(current_data):
    def function(update, context):
        user = update.message.from_user
        user_data = context.user_data
        if 'choice' in user_data:
            del user_data['choice']

        update.message.reply_text("Estos son tus datos para participar en recompensas:"
                                "{}"  
                                "Usuario de telegram: {} \n"
                                "ID del chat: {} \n"
                                "Hasta la proxima".format(
                                    facts_to_str(current_data.get_user_info(user['username'])),
                                    user['username'],
                                    user['id']))

        insert_json(user['username'], user['id'], current_data.get_user_info(user['username']))

        user_data.clear()
        return ConversationHandler.END
    
    return function


def main():
    current_data = UserData()
  
    updater = Updater(read_file('key.txt'), use_context=True)

  
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^(Direccion de Stake|Direccion de Cardano|Nombre de usuario|Referente (Usuario de telegram))$'),
                                      regular_choice)
                       ],

            TYPING_CHOICE: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Hecho$')),
                               regular_choice)],

            TYPING_REPLY: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Hecho$')),
                               received_information(current_data))],
        },

        fallbacks=[MessageHandler(Filters.regex('^Hecho$'), done(current_data))]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()