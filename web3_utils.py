from web3 import Web3
import os
import json
from dotenv import load_dotenv

load_dotenv()

SEPOLIA_RPC = os.getenv("INFURA_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = Web3.to_checksum_address("0x5fBb604D87F544F423d40cE5E43b7ae0e2b41deb")

with open("backend/abi.json", "r") as f:
    abi = json.load(f)

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def register_mother():
    try:
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        txn = contract.functions.registerMother(WALLET_ADDRESS).build_transaction({
            'from': WALLET_ADDRESS,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.to_wei('20', 'gwei')
        })
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash.hex()
    except Exception as e:
        return f"Error: {str(e)}"

def get_mother_id():
    return contract.functions.getMotherID(WALLET_ADDRESS).call()

def register_baby():
    try:
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        txn = contract.functions.registerBaby(WALLET_ADDRESS).build_transaction({
            'from': WALLET_ADDRESS,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.to_wei('20', 'gwei')
        })
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash.hex()
    except Exception as e:
        return f"Error: {str(e)}"

def get_baby_id():
    return contract.functions.getBabyID(WALLET_ADDRESS).call()
