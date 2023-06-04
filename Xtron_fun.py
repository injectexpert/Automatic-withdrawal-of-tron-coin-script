


import time
import requests
import logging

from art import tprint
from notifiers import get_notifier

from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

from config import private_key1, \
    private_key2, \
    from_addr, \
    to_addr, \
    bot_key, \
    admins_id, \
    api_tron

tprint("Xtron TRX")

logging.basicConfig(level=logging.INFO, filename='Xtron.log', format="%(asctime)s %(levelname)s %(message)s")

# Set provider and client(Tron)
provider = HTTPProvider(api_key=api_tron)
client = Tron(provider, network='mainnet')  # network selection

# # Set privete key wallet.
priv_key1 = PrivateKey(bytes.fromhex(private_key1))
priv_key2 = PrivateKey(bytes.fromhex(private_key2))


def get_new_transaction(api_key, addr):
    """ This function requests new transactions and processes them """
    try:
        query_time = 1
        global txid, f_txid, amount

        url = f'https://api.trongrid.io/v1/accounts/{addr}/transactions?only_to=true&limit=1'
        headers = {
            'Content-Type': "application/json",
            'TRON-PRO-API-KEY': api_key
        }

        response = requests.get(url=url, headers=headers)
        for data in response.json().get('data', []):
            o = data.get('raw_data', {})
            con = o['contract'][0]['parameter']['value']
            f_amount = con.get('amount', [])
            f_txid = data.get('txID', [])

        while True:

            url = f'https://api.trongrid.io/v1/accounts/{addr}/transactions?only_to=true&limit=1'
            headers = {
                'Content-Type': "application/json",
                'TRON-PRO-API-KEY': api_key
            }

            response = requests.get(url=url, headers=headers)
            for data in response.json().get('data', []):
                o = data.get('raw_data', {})
                con = o['contract'][0]['parameter']['value']
                amount = con.get('amount', [])
                txid = data.get('txID', [])

            if txid != f_txid:
                if amount > 1:
                    f_txid = txid
                    trx = amount / 10 ** 6

                    # info
                    print("New transaction", trx, "TRX", txid, "txID")
                    logging.info(f'new transaction: {trx} TRX: {txid} txID')
                    good_new_trans(trx, txid)
                    send_multi_sign_trx(amount=amount)

            time.sleep(query_time)

    except Exception as err_get:
        logging.error(f'error get new transaction: {err_get}')
        err_new_trans()


def commission_set():
    """ This function receives balance data and calculates the amount of TRX sends """
    bal = client.get_account_balance(from_addr)

    scaled_number = bal * 10**6  # Multiply by 10^6 to get 6 decimal places
    rounded_number = round(scaled_number)  # Rounding up the number
    int_number = int(rounded_number)  # Cast to type int

    print(int_number)


def send_multi_sign_trx(amount):
    """ This function implements the method of sending a transaction Multi-Sign TRX """

    global responce
    try:
        # the comission set
        free_amount = amount - 1_400_000

        # sign transaction
        transaction = client.trx.transfer(from_addr, to_addr, free_amount).build(10)
        segn1 = transaction.sign(priv_key1)
        segn2 = transaction.sign(priv_key2)

        id_tx = transaction.txid
        responce = transaction.broadcast().wait()
        trx = free_amount / 10 ** 6

        if id_tx is not None:
            # info
            print(f"transaction successfully sent: {trx} TRX: {id_tx} txID")
            logging.info(f'Send transaction: {trx} TRX: {id_tx} txID')
            good_send_trans(trx, id_tx)

    except Exception as err_send_multi:
        logging.error(f'error send transaction {err_send_multi}')
        err_send_trans()


def err_new_trans():
    """ Error when receiving a new transaction  """
    for admin in admins_id:
        tg = get_notifier('telegram')
        tg.notify(token=bot_key, chat_id=admin,
                  message=f"Error at receiving new transaction,see log file")


def good_new_trans(trx, txid):
    """ New transaction successfully received """
    for admin in admins_id:
        tg = get_notifier('telegram')
        tg.notify(token=bot_key, chat_id=admin,
                  message=f"New transaction successfully received: {trx} TRX: {txid}")


def err_send_trans():
    """ Transaction sending error """
    for admin in admins_id:
        tg = get_notifier('telegram')
        tg.notify(token=bot_key, chat_id=admin,
                  message=f"Error at sending transaction, see log file")


def good_send_trans(trx, id_tx):
    """ transaction was successfully sent  """
    for admin in admins_id:
        tg = get_notifier('telegram')
        tg.notify(token=bot_key, chat_id=admin,
                  message=f"transaction successfully sent: {trx} TRX: {id_tx}")


if __name__ == '__main__':
    get_new_transaction(api_key=api_tron, addr=from_addr)
