from flask import Flask, request
from galileo import *
from twilio.rest import Client
from twilio import twiml
from googletrans import Translator
from db import *
import requests
import json

app = Flask(__name__)


account_sid = 'ACf22bede7f95a9a4daf12a0839fbb4b1b'
auth_token = '8f087f2ed7f2a3af668a0e43754d0431'
twilio_num = '+13604502362'

base_url = 'https://sandbox.galileo-ft.com/inserv/4.0/'

# account_sid = 'AC4ff68924dac04103f83927dc992a459a'
# auth_token = 'e56af4b41cf425a6c9db7de8e387e7ed'
# twilio_num = '+12076146073'

client = Client(account_sid, auth_token)

languages = { 'english':'en', 'spanish':'es','hindi':'hi','japanese':'ja', 'german':'de', 'french': 'fr'}
languages_num = {'1': 'english', '2': 'french', '3': 'spanish', '4': 'german', '5': 'hindi'}
currencies_num = {'1': 'usd', '2': 'eur', '3': 'inr', '4': 'gbp', '5': 'mxd'}
currencies_conversion = {"usd": 1, 'eur': 1.10, 'inr': .014, 'gbp': 1.23, 'mxd': .051}

translator = Translator()
galileo = Galileo()

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
        msg = '\n(1) English\n(2) Francais\n(3) Espanol\n(4) Deutsch\n(5) Hindi'
        send_message(msg, number)
        return ''

    # Recieved language prompt, but we need language
    elif sender['language'] is None:
        lang = languages_num.get(message)
        if lang is None:
            message = '\n(1) English\n(2) Francais\n(3) Espanol\n(4) Deutsch\n(5) Hindi'
            send_message(message, number)
            return ''

        lang = languages[lang]
        conn = engine.connect()
        upd = user.update().where(user.c.number == number).values(language = lang)
        result = conn.execute(upd)

        message = '\nLanguage registered!\nSelect your preferred currency:'
        message = translator.translate(message, dest=lang, src='en').text + '\n(1) USD\n(2) EUR\n(3) INR\n(4) GBP\n(5) MXN'
        send_message(message, number)
        return ''

    
    # Recieved language now ask for currency
    elif sender['currency'] is None:
        conn = engine.connect()
        upd = user.update().where(user.c.number == number).values(currency=currencies_num[message])
        result = conn.execute(upd)

        message = '\nCurrency registered!\nPlease send your username'
        message = translator.translate(message,dest=str(sender['language']), src='en').text
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
        # create galileo account
        prn = galileo.create_account()
        try:
            conn = engine.connect()
            upd = user.update().where(user.c.number == number).values(prn=prn)
            result = conn.execute(upd)
        except Exception as err:
            print('ERROR: ', str(err))
            message = '\nCould not add ParlePay.'
            message = translator.translate(message, dest=str(sender['language']), src='en').text
            send_message(message, number)
            return ''

        # credit all accounts because we love our clients
        if galileo.create_transfer(20.0, src_account='283101000794', dst_account=prn):
            print('FUNDED')
        send_message(message, number)
        return ''


    # Have all information from user
    else:
        i = 0
        paying = False
        usernames = []
        amount = None
        words = message.split()
        if len(words) > 0 and words[0].lower() == 'parlepay':
            paying = True
        for word in words:
            if len(word) > 0 and word[0] == '@':
                usernames.append(word[1:])
            elif len(word) > 0:
                try:
                    amount = float(word)
                except ValueError:
                    continue

                        
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
                if paying:
                    if galileo.create_transfer(amount * currencies_conversion[sender['currency']], str(sender['prn']), str(recipient['prn'])):
                        balance = galileo.get_balance(str(recipient['prn']))
                        message = '\n' + str('{:12.2f}'.format(amount * currencies_conversion[sender['currency']] / currencies_conversion[recipient['currency']])) + ' ' + str(recipient['currency']).upper() + ' ' + \
                        'ParlePay recieved from ' + '@' + str(sender['username']) + \
                        '. ' + 'your new balance is ' + str('{:12.2f}'.format(balance / currencies_conversion[recipient['currency']])) + ' ' + str(recipient['currency']).upper()
                        message = translator.translate(message, dest=str(recipient['language']), src='en').text
                        send_message(message, number)
                        continue
                    else:
                        message = '\nParlePay to ' + recipient['username'] + 'was unsuccessfull'
                        message = translator.translate(message, dest=str(sender['language']), src='en').text
                        send_message(message, str(sender['number']))
                        continue


                body = translator.translate(message, dest=str(recipient['language']), src=str(sender['language'])).text
                From = translator.translate('From', dest=str(recipient['language']), src='en').text
                trans_message = From + ' @' + sender['username'] + ': \n' + body
                send_message(trans_message, number)

            if paying:
                balance = galileo.get_balance(sender['prn'])
                message = '\nPayment confirmed. Your new balance is ' + str('{:12.2f}'.format(balance / currencies_conversion[sender['currency']])) + ' ' + str(sender['currency']).upper()
                message = translator.translate(message, dest=str(sender['language']), src='en').text
                send_message(message, str(sender['number']))
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