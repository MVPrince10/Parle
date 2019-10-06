from flask import Flask, request
from twilio.rest import Client
from twilio import twiml

app = Flask(__name__)

account_sid = 'ACf849c1947357510945e67fa9a6884327'
auth_token = 'a436f7bd8888bc2fe79a4ffc50ec2e1b'
client = Client(account_sid, auth_token)


@app.route("/sms", methods=['POST'])
def recieve_massage():

    number = request.form['From']
    message = request.form['Body']
    number = str(number)
    message = str(message)

    message2 = client.messages \
                .create(
                     body=message,
                     from_='+17047282359',
                     to='+18016358666'
                )
    print(message2.sid)
   # print(number, message_body)
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True)