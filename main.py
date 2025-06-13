import os
import secrets
import hashlib
from flask import Flask, request, jsonify
import threading
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
TOTAL_SUPPLY = 1_000_000_000

class Wallet:
    def __init__(self, name):
        self.name = name
        self.private_key = secrets.token_hex(32)
        self.seed_phrase = " ".join(secrets.choice(['apple','banana','cat','dog','elephant','fish','grape','hat','ice','jug','kite','lion']) for _ in range(12))
        self.address = "0x" + hashlib.sha256(self.private_key.encode()).hexdigest()[-40:]
        self.balance = 0

class AhlaNetwork:
    def __init__(self):
        self.wallets = {}
        self.admin_wallet = None

    def create_wallet(self, name):
        if name in self.wallets:
            return None, "Wallet with this name already exists."
        wallet = Wallet(name)
        if self.admin_wallet is None:
            wallet.balance = TOTAL_SUPPLY
            self.admin_wallet = wallet
        self.wallets[name] = wallet
        return wallet, "Wallet created successfully."

    def get_balance(self, name):
        wallet = self.wallets.get(name)
        if wallet:
            return wallet.balance
        return None

    def send(self, sender_name, receiver_name, amount):
        sender = self.wallets.get(sender_name)
        receiver = self.wallets.get(receiver_name)
        if not sender or not receiver:
            return False, "Sender or receiver wallet not found."
        if sender.balance < amount:
            return False, "Insufficient balance."
        sender.balance -= amount
        receiver.balance += amount
        return True, "Transaction successful!"

network = AhlaNetwork()

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome to Ahla Network Bot!\nUse /create_wallet <name>, /balance <name>, /send <sender> <receiver> <amount>")

def create_wallet(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /create_wallet <wallet_name>")
        return
    name = context.args[0]
    wallet, msg = network.create_wallet(name)
    if wallet is None:
        update.message.reply_text(msg)
    else:
        update.message.reply_text(f"✅ Wallet '{name}' created!\nAddress: {wallet.address}\nPrivate Key: {wallet.private_key}\nSeed Phrase: {wallet.seed_phrase}\nBalance: {wallet.balance} AHLA")

def balance(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /balance <wallet_name>")
        return
    name = context.args[0]
    bal = network.get_balance(name)
    if bal is None:
        update.message.reply_text("Wallet not found.")
    else:
        update.message.reply_text(f"💰 Balance of '{name}': {bal} AHLA")

def send(update: Update, context: CallbackContext):
    if len(context.args) != 3:
        update.message.reply_text("Usage: /send <sender> <receiver> <amount>")
        return
    sender, receiver, amount_str = context.args
    try:
        amount = int(amount_str)
    except ValueError:
        update.message.reply_text("Amount must be an integer.")
        return
    success, msg = network.send(sender, receiver, amount)
    update.message.reply_text(msg)

def run_telegram_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_wallet", create_wallet))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("send", send))
    updater.start_polling()
    updater.idle()

app = Flask(__name__)
CHAIN_ID = 12345

@app.route("/rpc", methods=["POST"])
def rpc():
    data = request.get_json()
    method = data.get("method")
    params = data.get("params", [])
    id_ = data.get("id")
    if method == "web3_clientVersion":
        return jsonify({"jsonrpc": "2.0", "id": id_, "result": "AhlaNetwork/v1.0"})
    elif method == "eth_chainId":
        return jsonify({"jsonrpc": "2.0", "id": id_, "result": hex(CHAIN_ID)})
    elif method == "eth_blockNumber":
        return jsonify({"jsonrpc": "2.0", "id": id_, "result": hex(0)})
    elif method == "eth_getBalance":
        address = params[0]
        for wallet in network.wallets.values():
            if wallet.address == address:
                return jsonify({"jsonrpc": "2.0", "id": id_, "result": hex(wallet.balance * 10**18)})
        return jsonify({"jsonrpc": "2.0", "id": id_, "result": hex(0)})
    return jsonify({"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}})

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_telegram_bot()