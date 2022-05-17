from eth_account.signers.local import LocalAccount
from flashbots import flashbot
from eth_account.account import Account
from web3 import Web3, HTTPProvider, exceptions
from web3.types import TxParams

import os
import requests
import math

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("FAKE_NFT_CONTRACT") or not os.environ.get("WALLET_PRIVATE_KEY"):
    print("env variables WALLET_PRIVATE_KEY and FAKE_NFT_CONTRACT required")
    exit(1)

# signifies your identify to the flashbots network
FLASHBOTS_SIGNATURE: LocalAccount = Account.create()
USER_ACCOUNT: LocalAccount = Account.from_key(os.environ.get("WALLET_PRIVATE_KEY"))

NFT_FAKE_CONTRACT = os.environ.get("FAKE_NFT_CONTRACT")
HTTP_PROVIDER =     os.environ.get("HTTP_PROVIDER")
USE_GOERLI =        os.environ.get("USE_GOERLI")

w3 = Web3(HTTPProvider(HTTP_PROVIDER))

if USE_GOERLI:
    flashbot(w3, FLASHBOTS_SIGNATURE, "https://relay-goerli.flashbots.net")
else:
    flashbot(w3, FLASHBOTS_SIGNATURE)

# the bribe can be paid either via gas price or coinbase.transfer() in a contract.
# here we use gas. it must be high enough to make all the transactions in the
# bundle have a competitive effective gas price. see more about this here:
# https://docs.flashbots.net/flashbots-core/searchers/advanced/bundle-pricing/
def get_gas_price():
    gas_api = "https://ethgasstation.info/json/ethgasAPI.json"
    response = requests.get(gas_api).json()

    gas_multiplier = 3
    gas_price_gwei = math.floor(response["fastest"] / 10 * gas_multiplier)
    gas_price = w3.toWei(gas_price_gwei, "gwei")
    return gas_price

def main():

    print("connecting to RPC")
    print(f"USER ACCOUNT: {USER_ACCOUNT.address}: {w3.eth.get_balance(USER_ACCOUNT.address)} wei")

    # create a transaction
    gas_price = get_gas_price()
    tx: TxParams = {
        "chainId": 5,
        "data": "0x1249c58b", #  mint function
        "from": USER_ACCOUNT.address,
        "maxFeePerGas": gas_price,
        "maxPriorityFeePerGas": Web3.toWei(50, "gwei"),
        "nonce": w3.eth.get_transaction_count(USER_ACCOUNT.address),
        "to": w3.toChecksumAddress(NFT_FAKE_CONTRACT),
        "type": 2,
        "value": w3.toWei("0.03", "ether"),
    }
    # Get the gas estimate for this transaction
    gas_estimate = math.floor(w3.eth.estimate_gas(tx))
    tx["gas"] = gas_estimate

    gas_in_gwei = int(gas_price / 10**9)
    print(f"Estimated gas: {gas_estimate}")
    print(f"Gas Price: {gas_in_gwei} Gwei")

    signed_tx = USER_ACCOUNT.sign_transaction(tx)

    # create a flashbots bundle.
    # bundles will be dropped / filtered in production if
    # 1. your bundle uses < 42k gas total
    # 2. you have another tx with the same nonce in the mempool
    bundle = [
        {"signed_transaction": signed_tx.rawTransaction},
        # you can include other transactions in the bundle
        # in the order that you want them in the block
    ]

    # flashbots bundles target a specific block, so we target
    # any one of the next 3 blocks by emitting 3 bundles
    block_number = w3.eth.block_number

    # SIMULATE it
    print("SIMULATING TRANSACTION...")
    try:
        simulation = w3.flashbots.simulate(bundle, block_number + 1)
    except Exception as e:
        print("Error in simulation", e)
        return

    print(f'bundleHash: {simulation["bundleHash"]}')
    print(f'coinbaseDiff: {simulation["coinbaseDiff"]}')
    print(f'totalGasUsed: {simulation["totalGasUsed"]}')

    print("SENDING bundles to flashbots")
    for i in range(1, 3):
        w3.flashbots.send_bundle(bundle, target_block_number=block_number + i)

    print(f"broadcast started at block {block_number}")

    # target 3 future blocks
    # if we dont see confirmation in those blocks, assume the mint wasn't mined
    while True:
        try:
            w3.eth.wait_for_transaction_receipt(signed_tx.hash, timeout=1, poll_latency=0.1)
            break

        except exceptions.TimeExhausted:
            print(f"Block: {w3.eth.block_number}")
            if w3.eth.block_number > (block_number + 3):
                print("ERROR: transaction was not mined so you didn't mint a thing")
                exit(1)

    print(f"transaction confirmed at block {w3.eth.block_number}")

if __name__ == "__main__":
    main()