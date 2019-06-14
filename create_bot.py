"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pickle
import time
import telepot
from geopy.distance import great_circle
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import querySPARQL as query


def read_monuments():
    with open("monuments.pickle", "rb") as file:
        return pickle.load(file)


def send_monument_nearby(bot, updates):
    last_positions[updates["chat"]["id"]] = (updates['location']["latitude"], updates['location']["longitude"])
    nearby_list = list()
    chat = updates["chat"]["id"]
    mypos = (updates['location']["latitude"], updates['location']["longitude"])
    for placemark in monuments:
        placepos = (placemark["latitudine"], placemark["longitudine"])
        dist = great_circle(mypos, placepos).meters
        if dist < 300:
            nearby_list.append(placemark)
    if not nearby_list:
        bot.sendMessage(chat, "Mi dispiace, nel raggio di 300 metri non sono presenti monumenti da visitare..")
    else:
        send_custom_keyboard(bot, updates, nearby_list)


def send_custom_keyboard(bot, updates, monument_list):
    chat = updates["chat"]["id"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='{}'.format(text["nome"]), callback_data='{}'.format(text["id"]))]
                         for text in monument_list])
    bot.sendMessage(chat_id=chat, text="Sei vicino a: ", reply_markup=keyboard)


"""
Callback_query viene chiamata in due casi:
Primo caso da send_custom_keyboard una volta che l'utente seleziona il monumento d'interesse
Secondo caso in cui l'utente seleziona uno dei tre pulsanti messi a disposizione "torna indietro" "foto storiche" e "Più immagini",
in questo caso all'interno del paccheto msg sarà presente oltre il campo id del monumento, anche un numero identificativo, che permette
di capire cosa bisogna visualizzare, nello specifio 1 se si tratta di torna indietro, 2 foto storiche e 3 più immagini. Ad esempio se l'utente preme torna indietro
il pacchetto msg avrà un formato del tipo id/1 (supponendo che id sia formato interamente da cifre, il carattere separatore sarà / ).
"""


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if query_data.find("/") == -1:
        if query.info_monument(query_data, "cis:institutionalName") != -1:
            monument_name = query.info_monument(query_data, "cis:institutionalName")
            bot.sendMessage(from_id, "*" + monument_name[query_data][0] + "*", parse_mode="Markdown")

        if query.info_monument(query_data, "pmo:picture") != -1:
            monument_photo = query.info_monument(query_data, "pmo:picture")
            bot.sendPhoto(from_id, monument_photo[query_data][0])
        """
        Per visualizzare un immagine di default nel caso in cui non sia presente all'interno del dataset.
        else:
            bot.sendPhoto(from_id, photo=open("img/og-stemma-palermo.gif", "rb"))
        """
        if query.info_monument(query_data, "cis:description") != -1:
            monument_description = query.info_monument(query_data, "cis:description")
            bot.sendMessage(from_id, monument_description[query_data][0])
        keyboard = []
        keyboard.append(InlineKeyboardButton(text="Torna indietro", callback_data=query_data + '/1'))
        if query.check_more_img(query_data) != -1:
            keyboard.append(InlineKeyboardButton(text="Più immagini", callback_data=query_data + '/3'))
        if query.info_monument(query_data, "pmo:oldPicture") != -1:
            keyboard.append(InlineKeyboardButton(text="foto storiche", callback_data=query_data + '/2'))
        if query.info_monument(query_data, "dbo:lat") != -1 and query.info_monument(query_data, "dbo:long") != -1:
            monument_lat = query.info_monument(query_data, "dbo:lat")
            monument_long = query.info_monument(query_data, "dbo:long")
            bot.sendLocation(from_id, monument_lat[query_data][0], monument_long[query_data][0],
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]))
        return
    command = query_data[query_data.find("/") + 1]
    id = query_data[0:query_data.find("/")]
    if int(command) == 1:
        # Nel caso in cui l'utente vuole tornare indietro, non faccio altro che
        # ricreare il pacchetto msg originale inviando id, lat e long e richiamando la funzione send_monument_nearby.
        # Questo perchè è più comodo ricostruire la lista piuttosto che doverla memorizzare per ogni utente la
        # relativa keyboard
        lat = last_positions[from_id][0]
        long = last_positions[from_id][1]
        # Per utilizzare come ultima posizione il monumento scelto precedentemente
        # lat = info_monument(str(id), "dbo:lat")
        # long = info_monument(str(id), "dbo:long")
        update = {'chat': {
            "id": from_id
        }, 'location': {
            "latitude": str(lat),
            "longitude": str(long)
        }}
        send_monument_nearby(bot, update)
    if int(command) == 2:
        if query.info_monument(str(id), "pmo:oldPicture") != -1:
            old_picture = query.info_monument(str(id), "pmo:oldPicture")
            for x in range(0, len(old_picture[str(id)]), 1):
                bot.sendPhoto(from_id, old_picture[str(id)][x])
            keyboard = []
            keyboard.append(InlineKeyboardButton(text="Torna indietro", callback_data=str(id) + '/1'))
            text = "Spero queste immagini siano di tuo gradimento, torna indietro per visualizzare i monumenti nelle vicinanze"
            bot.sendMessage(from_id, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]))
    if int(command) == 3:
        if query.info_monument(str(id), "pmo:nearbyCulturalInstituteOrSite") != -1:
            more_picture = query.info_monument(str(id), "pmo:nearbyCulturalInstituteOrSite")
            id_monuments = list()
            for x in range(0, len(more_picture[str(id)]), 1):
                string = "<" + str(more_picture[str(id)][x]) + ">"
                monument = query.id_monument(string)
                id_monuments.append(monument[string][0])
            message_info = 1
            for m in id_monuments:
                if query.info_monument(m, "pmo:picture") != -1:
                    if message_info:
                        bot.sendMessage(from_id, "Ecco alcune immagini dei monumenti vicini a quello selezionato")
                        message_info = 0
                    monument_name = query.info_monument(m, "cis:institutionalName")
                    monument_photo = query.info_monument(m, "pmo:picture")
                    bot.sendMessage(from_id, "*" + monument_name[m][0] + "*", parse_mode="Markdown")
                    bot.sendPhoto(from_id, monument_photo[m][0])
        keyboard = []
        keyboard.append(InlineKeyboardButton(text="Torna indietro", callback_data=str(id) + '/1'))
        bot.sendMessage(from_id,
                        "Spero queste immagini siano di tuo gradimento, clicca per visualizzare i monumenti nelle vicinanze",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]))


def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'location':
        send_monument_nearby(bot, msg)
    else:
        if msg["text"] == "/start":
            bot.sendMessage(chat_id,
                            "Benvenuto, mandami la tua posizione per trovare i punti di interesse vicino a te:",
                            reply_markup=None)
        elif msg["text"] == "/info":
            bot.sendMessage(chat_id, "Benvenuto all'interno del bot Guida ai monumenti di Palermo.\n" +
                            "Questo bot è stato realizzato per permettere ai turisti o semplicemente " +
                            "ai palermitani, di conoscere con maggiore dettaglio i monumenti che li " +
                            "circondano, permettendo in oltre di visionare ove presenti, le immagini " +
                            "storiche del monumento scelto. Banca dati utilizzata per la geolocalizzazione: " +
                            "OpenStreetMap.org (licenza: ODBL).\nInoltre si ringrazia la biblioteca comunale " +
                            "di Palermo per aver reso possibile questo progetto mediante foto messe a " +
                            "disposizione in modo totalmente gratuito all'interno della piattaforma Flickr " +
                            "con username: \"Biblioteca comunale Palermo\" a cura della dott.ssa" +
                            "Eliana Calandra.", reply_markup=None)
        else:
            bot.sendMessage(chat_id, "Comandi disponibili: \n /start \n /info", reply_markup=None)


TOKEN = "XXX"
bot = telepot.Bot(TOKEN)
"""
struttura dati utilizzata solo per ricavare i monumenti vicino alla posizione mandata dall'utente,
cosa non possibile mediante query per problemi dovuti alla geodistance.
"""
monuments = read_monuments()
last_positions = {}


def main():
    MessageLoop(bot, {'chat': handle, 'callback_query': on_callback_query}).run_as_thread()
    print("In attesa di un messaggio..")
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
