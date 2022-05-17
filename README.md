# Flashbots searcher-minter-py

This is a python version of [searcher-minter](https://github.com/flashbots/searcher-minter)

The script is a simple demonstration of using Flashbots to mint an NFT. It assembles a signed transaction and sends it to the Flashbots relay.

# How to run

You will need the following:

1. Goerli testnet ETH -- [faucet](https://faucet.goerli.mudit.blog/)
2. HTTP Provider URL pointing to a mev-geth node

Update the example.env: 
1. Include the private key of your test wallet
**(Test wallets only! Never use a wallet that contains, or will contain, real money!!)**
3. Update the HTTP provider with your endpoint
4. save as .env

Let Poetry do its magic, and run the script
```
poetry install
```
```
python examples/minter.py
```

# Goerli Contract Addresses
Provided by the original project
* WasteGas: `0x957B500673A4919C9394349E6bbD1A66Dc7E5939`
* FakeArtMinter: `0x20EE855E43A7af19E407E39E5110c2C1Ee41F64D`
