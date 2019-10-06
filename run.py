from flask import Flask, request
from twilio.rest import Client
from twilio import twiml
from googletrans import Translator

app = Flask(__name__)

account_sid = 'ACf849c1947357510945e67fa9a6884327'
auth_token = 'a436f7bd8888bc2fe79a4ffc50ec2e1b'
client = Client(account_sid, auth_token)

username_to_numbers = {}
numbers_to_usernames = {}
username_to_language = {}
phone_numbers = []
languages = { 'English':'en', 'Spanish':'es','Hindi':'hi','Japanese':'ja', 'German':'de'}

translator = Translator()


def trans(message, languageDST, languageSRC):
    print(message)
    i = 0
    start = 0
    substr = ""
    while i < len(message):
        if message[i] == '@':
            print(message[start:i])
            substr += translator.translate(message[start:i], dest=languages[languageDST], src=languages[languageSRC]).text
            j = i
            while message[j] != ' ':
                j += 1
            print(message[i:j])
            substr += message[i:j]
            start = j
            i = j
        i += 1
    
    substr += translator.translate(message[start:len(message)], dest=languages[languageDST], src=languages[languageSRC]).text
    print(substr)
    return substr


@app.route("/sms", methods=['POST'])
def recieve_massage():

    number = request.form['From']
    message = request.form['Body']
    number = str(number)
    message = str(message)

    # First message received from user
    if number not in phone_numbers:
        print("number",number)
        phone_numbers.append(number)
        message2 = client.messages \
                .create(
                     body= "\nThank you for joining Parle!\n Please send a username",
                     from_='+19097267210',
                     to=number
                )
        print(message2.sid)
    # Have prompted for username, but don't have username
    elif number not in username_to_numbers.values():
        if message in username_to_numbers.keys():
            message2 = client.messages \
                .create(
                     body= "Username already in use. Please send another username",
                     from_='+19097267210',
                     to=number
                )
            print(message2.sid)
        else:
            message2 = client.messages \
                .create(
                     body= "Thank you. What is your preffered language?",
                     from_='+19097267210',
                     to=number
                )
            print(message2.sid)
            username_to_numbers[message] = number
            numbers_to_usernames[number] = message
    # Have username, but we need language
    elif numbers_to_usernames[number] not in username_to_language:
        if message in languages:
            username_to_language[numbers_to_usernames[number]] = message
            message2 = client.messages \
                .create(
                     body= "One last thing. What country do you live in?",
                     from_='+19097267210',
                     to=number
                )
            print(message2.sid)
        else:
            message2 = client.messages \
                .create(
                     body= "This language is not supported. Please send another language.",
                     from_='+19097267210',
                     to=number
                )
            print(message2.sid)
    # Have username and language, but need currency
    # Have all information from user
    else:
        i = 0
        users = []
        while i < len(message):
            if message[i] == '@':
                j = i + 1
                while message[j] != ' ' and j < len(message):
                    j += 1
                sub = message[i+1:j]
                print(sub)
                if sub in username_to_numbers.keys():
                    users.append(sub)
                i = j + 1
            i += 1

                
        if len(users) == 0:
            message2 = client.messages \
                .create(
                     body= "No valid users in message",
                     from_='+19097267210',
                     to=number
                )
            print(message2.sid)
        else:
            
            for user in users:
               # body = trans(message, username_to_language[user], username_to_language[numbers_to_usernames[number]])
                body = translator.translate(message, dest=languages[username_to_language[user]], src=languages[username_to_language[numbers_to_usernames[number]]]).text
                message = "@" + numbers_to_usernames[number] + ": " + body
                message2 = client.messages \
                .create(
                     body= message,
                     from_='+19097267210',
                     to=username_to_numbers[user]
                )
                print(message2.sid)
            

    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True)
