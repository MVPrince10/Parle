from flask import Flask, request
from twilio.rest import Client
from twilio import twiml
from googletrans import Translator
from db import *

app = Flask(__name__)

account_sid = 'ACf849c1947357510945e67fa9a6884327'
auth_token = 'a436f7bd8888bc2fe79a4ffc50ec2e1b'
client = Client(account_sid, auth_token)
twilio_num = '+19097267210'

languages = { 'english':'en', 'spanish':'es','hindi':'hi','japanese':'ja', 'german':'de', 'french': 'fr'}
languages_num = {'1': 'english', '2': 'french', '3': 'spanish', '4': 'german', '5': 'hindi'}

translator = Translator()

def trans(message, languageSRC, languageDST):
    print(message, languageSRC, languageDST)
    i = 0
    start = 0
    substr = ""
    while i < len(message):
        if message[i] == '@':
            print(message[start:i])
            if i - 1 > start:
                s = message[start:i]
                if not s.isspace() and len(s) > 0:
                    substr += translator.translate(s, dest=languages[languageDST], src=languages[languageSRC]).text
                else:
                    substr += s
            j = i
            while j < len(message) and message[j] != ' ':
                j += 1
            print(message[i:j])
            substr += message[i:j+1]
            start = j
            i = j
        i += 1
    s = message[start:len(message)]
    if not s.isspace() and len(s) > 0:
        substr += translator.translate(message[start:len(message)], dest=languages[languageDST], src=languages[languageSRC]).text
    else:
        substr += s
    print(substr)
    return substr

@app.route("/sms", methods=['POST'])
def recieve_message():

    number = request.form['From']
    message = request.form['Body']
    number = str(number).strip()
    message = str(message).strip()


    # query for user
    try:
        select = user.select().where(user.c.number == number)
        conn = engine.connect()
        sender = conn.execute(select)
        sender = sender.fetchone()
    except Exception as err:
        print(str(err))
        return ''

    if sender is None:
        print('number', number)
        # add number to database
        try:
            ins = user.insert().values(number=number)
            conn = engine.connect()
            result = conn.execute(ins)
        except Exception as err:
            print('ERROR: ', str(err))
            return ''
        # send message
        msg = '\nFor English text 1\nPour Francais texte 2\nPara Espanol texto 3\nFur Deutsch schreib 4\nHindi paath 5'
        send_message(msg, number)
        return ''

    # Have username, but we need language
    elif sender['language'] is None:
        lang = languages_num.get(message)
        if lang is None:
            message = '\nFor English text 1\nPour Francais texte 2\nPara Espanol texto 3\nFur Deutsch schreib 4\nHindi paath 5'
            send_message(message, number)
            return ''

        lang = languages[lang]
        conn = engine.connect()
        upd = user.update().where(user.c.number == number).values(language = lang)
        result = conn.execute(upd)

        message = '\nLanguage registered! Please send your username'
        message = translator.translate(message, dest=lang, src='en').text
        send_message(message, number)
        return ''

    # Have prompted for username, but don't have username
    elif sender['username'] is None:
        message = message.lower()
        try:
            conn = engine.connect()
            upd = user.update().where(user.c.number == number).values(username = message)
            result = conn.execute(upd)
        except Exception as err:
            print('ERROR: ', str(err))
            message = '\nUsername in use. Please try again.'
            message = translator.translate(message, dest=str(sender['language']), src='en').text
            send_message(message, number)
            return ''
        
        message = '\nRegistered!'
        message = translator.translate(message, dest=str(sender['language']), src='en').text
        send_message(message, number)
        return ''

    # Have username and language, but need currency
    # Have all information from user
    else:
        i = 0
        usernames = []
        words = message.split()
        for word in words:
            if len(word) > 0 and word[0] == '@':
                usernames.append(word[1:])

                        
        if len(usernames) == 0:
            message = '\nUser not found'
            message = translator.translate(message, dest=str(sender['language']), src='en').text
            send_message(message, number)
            return ''
        else:
            for username in usernames:
                username = username.lower()
                try:
                    select = user.select().where(user.c.username == username)
                    conn = engine.connect()
                    recipient = conn.execute(select)
                    recipient = recipient.fetchone()
                    number = str(recipient['number'])
                except Exception as err:
                    print('ERROR: ', str(err))
                    message = '\n invalid username.'
                    message = translator.translate(message, dest=str(sender['language']), src='en').text
                    send_message(message, number)
                    return ''
                print(recipient['username'], recipient['language'])
                body = translator.translate(message, dest=str(recipient['language']), src=str(sender['language'])).text
                From = translator.translate('From', dest=str(recipient['language']), src='en').text
                trans_message = From + ' @' + sender['username'] + ': \n' + body
                send_message(trans_message, number)
            return ''      

    return "Hello World!"

def send_message(message, to_num):
    # using twilio
    message2 = client.messages \
                .create(
                     body= message,
                     from_= twilio_num,
                     to= to_num
                )
    return ''


if __name__ == "__main__":
    app.run(debug=True)