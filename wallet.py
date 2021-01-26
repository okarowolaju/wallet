import subprocess
import json
import os
from constants import BTC, BTCTEST, ETH
from pprint import pprint
from bit import PrivateKeyTestnet
from bit.network import NetworkAPI
from web3 import Web3, middleware, Account
from web3.gas_strategies.time_based import medium_gas_price_strategy
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

load_dotenv()

mnemonic = os.getenv('MNEMONIC')

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

def derive_wallets(mnemonic, num, coin):
  command = f'php ./derive -g --mnemonic="{mnemonic}" --numderive="{num}" --coin="{coin}" --format=json'

  p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)

  output, err = p.communicate()

  p_status = p.wait()

  keys = json.loads(output)
  return keys

derive_wallets(mnemonic, 'BTC', 3)

coins = {"eth", "btc-test", "btc"}
numderive = 3

keys = {}
for coin in coins:
    keys[coin]= derive_wallets(mnemonic, coin, numderive=3)

eth_PrivateKey = keys["eth"][0]['privkey']
btc_PrivateKey = keys['btc-test'][0]['privkey']

def priv_key_to_account(coin,priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    elif coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)

def create_tx(coin,account, recipient, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas(
            {"from":eth_acc.address, "to":recipient, "value": amount}
        )
        return {
            "from": eth_acc.address,
            "to": recipient,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(eth_acc.address)
        }

    elif coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address,[(recipient, amount, BTC)])

eth_acc = priv_key_to_account(ETH, derive_wallets(mnemonic, ETH,5)[0]['privkey'])

def send_txn(coin,account,recipient, amount):
    txn = create_tx(coin, account, recipient, amount)
    if coin == ETH:
        signed_txn = eth_acc.sign_transaction(txn)
        result = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(result.hex())
        return result.hex()
    elif coin == BTCTEST:
        tx_btctest = create_tx(coin, account, recipient, amount)
        signed_txn = account.sign_transaction(txn)
        print(signed_txn)
        return NetworkAPI.broadcast_tx_testnet(signed_txn)

create_tx(BTCTEST,btc_acc,"mnUjQrVXhkCXR1vVeAfKyypycmM54P5gDT", 0.00001)

send_txn(BTCTEST,btc_acc,"mpx1NJKkr3kgB7EnoyrJazc3p3fCyskFzq", 0.00001)


