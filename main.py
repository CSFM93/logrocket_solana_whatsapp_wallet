
import os
from dotenv import load_dotenv

from flask import Flask, request, Response

from twilio.rest import Client
from twilio.rest.api.v2010.account.message import MessageInstance
from twilio.twiml.messaging_response import MessagingResponse

from wallet import create_account, fund_account, get_balance, send_sol

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ['ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['AUTH_TOKEN']
TWILIO_WHATSAPP_NUMBER = os.environ['WHATSAPP_NUMBER']

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = Flask(__name__)


@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    print('incoming message', incoming_msg)

    message = command_handler(incoming_msg, sender)
    print('message', message)

    resp = MessagingResponse()
    msg = resp.message(message)
    return Response(str(resp), content_type='text/xml')


def command_handler(incoming_msg,sender):
    if "/createAccount" in incoming_msg:
        public_key = create_account(sender)
        if public_key is not None:
            message = "Solana Account created successfully.\n"
            message += "Your account public key is {}".format(public_key)
            return message
        else:
            message = "Failed to create account.\n"
            return message


    elif "/fundAccount" in incoming_msg:
        amount = float(incoming_msg.split(" ")[1])
        if amount <= 2 :
            message = "Requesting {} SOL to your Solana account, please wait !!!".format(
                amount)
            print(message)
            send_message(sender, message)

            transaction_id = fund_account(sender, amount)

            if transaction_id is not None:
                message = "You have successfully requested {} SOL for your Solana account \n".format(
                    amount)
                message += "The transaction id is {}".format(transaction_id)
                return message

            else:
                message = "Failed to fund your Solana account"
                return message
        else:
            message = "The maximum amount allowed is 2 SOL"
            print(message)
            return message

    elif "/balance" in incoming_msg:
        data = get_balance(sender)
        if data is not None:
            public_key = data['publicKey']
            balance = data['balance']
            message = "Your Solana account {} ,balance is {} SOL".format(
                public_key, balance)
            return message
        else:
            message = "Failed to retrieve balance"
            print(message)
            return message

    elif "/send" in incoming_msg:
        split_msg = incoming_msg.split(" ")
        amount = float(split_msg[1])
        receiver = split_msg[2]

        message = "Sending {} SOL to {}, please wait !!!".format(
            amount, receiver)
        print(message)
        send_message(sender, message)

        transaction_id = send_sol(sender, amount, receiver)
        if transaction_id is not None:
            message = "You have successfully sent {} SOL to {} \n".format(
                amount, receiver)
            message += "The transaction id is {}".format(transaction_id)
            return message
        else:
            message = "Failed to send SOL"
            return message
    else:
        return "command not recognized"  



def send_message(sender, text):
    from_whatsapp_number = 'whatsapp:{}'.format(TWILIO_WHATSAPP_NUMBER)
    to_whatsapp_number = sender
    body = text

    message: MessageInstance = client.messages.create(
        body=body, from_=from_whatsapp_number, to=to_whatsapp_number)

    return message.sid


if __name__ == "__main__":
    app.run(port=5000, debug=True)
