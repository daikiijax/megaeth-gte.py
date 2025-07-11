import time, random
from web3 import Web3

PRIVATE_KEYS = [
    "YOUR_PRIVATE_KEY_1",
    # Multi private keys
]

RPC_URL = 'https://carrot.megaeth.com/rpc'
GTE_ADDRESS = Web3.to_checksum_address('0x9629684df53db9E4484697D0A50C442B2BFa80A8')
ROUTER_ADDRESS = Web3.to_checksum_address('0xA6b579684E943F7D00d616A48cF99b5147fC57A5')
WETH_ADDRESS = Web3.to_checksum_address('0x776401b9BC8aAe31A685731B7147D4445fD9FB19')
GTE_TO_ETH_RATE = 0.000033753025406442
TX_DELAY = 10  # Seconds
SWAP_PER_WALLET = 2
LIQ_PER_WALLET = 2

ROUTER_ABI = [
    {"inputs": [
        {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
        {"internalType": "address[]", "name": "path", "type": "address[]"},
        {"internalType": "address", "name": "to", "type": "address"},
        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
    ], "name": "swapExactETHForTokens", "outputs": [
        {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
    ], "stateMutability": "payable", "type": "function"},
    {"inputs": [
        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
        {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
        {"internalType": "address[]", "name": "path", "type": "address[]"},
        {"internalType": "address", "name": "to", "type": "address"},
        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
    ], "name": "swapExactTokensForETH", "outputs": [
        {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
    ], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [
        {"internalType": "address", "name": "token", "type": "address"},
        {"internalType": "uint256", "name": "amountTokenDesired", "type": "uint256"},
        {"internalType": "uint256", "name": "amountTokenMin", "type": "uint256"},
        {"internalType": "uint256", "name": "amountETHMin", "type": "uint256"},
        {"internalType": "address", "name": "to", "type": "address"},
        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
    ], "name": "addLiquidityETH", "outputs": [
        {"internalType": "uint256", "name": "amountToken", "type": "uint256"},
        {"internalType": "uint256", "name": "amountETH", "type": "uint256"},
        {"internalType": "uint256", "name": "liquidity", "type": "uint256"},
    ], "stateMutability": "payable", "type": "function"}
]
TOKEN_ABI = [
    {"inputs": [
        {"internalType": "address", "name": "spender", "type": "address"},
        {"internalType": "uint256", "name": "amount", "type": "uint256"}
    ], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
     "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [
        {"internalType": "address", "name": "account", "type": "address"}
    ], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
CHAIN_ID = w3.eth.chain_id   # otomatis ambil chain id

def get_gas_price():
    return w3.eth.gas_price   # otomatis ambil gas price terbaru

def approve_gte(wallet, amount):
    contract = w3.eth.contract(GTE_ADDRESS, abi=TOKEN_ABI)
    nonce = w3.eth.get_transaction_count(wallet.address, 'pending')
    tx = contract.functions.approve(ROUTER_ADDRESS, amount).build_transaction({
        'from': wallet.address,
        'gas': 100000,
        'gasPrice': get_gas_price(),
        'nonce': nonce,
        'chainId': CHAIN_ID,
    })
    signed = wallet.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.status == 1

def swap_eth_for_tokens(wallet, amount_eth):
    contract = w3.eth.contract(ROUTER_ADDRESS, abi=ROUTER_ABI)
    path = [WETH_ADDRESS, GTE_ADDRESS]
    deadline = int(time.time()) + 60 * 20
    value = w3.to_wei(amount_eth, 'ether')
    nonce = w3.eth.get_transaction_count(wallet.address, 'pending')
    tx = contract.functions.swapExactETHForTokens(
        0, path, wallet.address, deadline
    ).build_transaction({
        'from': wallet.address,
        'value': value,
        'gas': 382028,
        'gasPrice': get_gas_price(),
        'nonce': nonce,
        'chainId': CHAIN_ID,
    })
    signed = wallet.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

def swap_tokens_for_eth(wallet, amount_gte):
    contract = w3.eth.contract(ROUTER_ADDRESS, abi=ROUTER_ABI)
    gte_contract = w3.eth.contract(GTE_ADDRESS, abi=TOKEN_ABI)
    path = [GTE_ADDRESS, WETH_ADDRESS]
    deadline = int(time.time()) + 60 * 20
    amount_in = w3.to_wei(amount_gte, 'ether')
    amount_out_min = int(amount_gte * GTE_TO_ETH_RATE * 0.95 * 1e18)
    gte_balance = gte_contract.functions.balanceOf(wallet.address).call()
    if gte_balance < amount_in:
        return
    approved = approve_gte(wallet, amount_in)
    if not approved:
        return
    time.sleep(TX_DELAY)
    nonce = w3.eth.get_transaction_count(wallet.address, 'pending')
    tx = contract.functions.swapExactTokensForETH(
        amount_in, amount_out_min, path, wallet.address, deadline
    ).build_transaction({
        'from': wallet.address,
        'gas': 382028,
        'gasPrice': get_gas_price(),
        'nonce': nonce,
        'chainId': CHAIN_ID,
    })
    signed = wallet.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

def add_liquidity(wallet):
    router = w3.eth.contract(ROUTER_ADDRESS, abi=ROUTER_ABI)
    gte_contract = w3.eth.contract(GTE_ADDRESS, abi=TOKEN_ABI)
    gte_amt = float(f"{random.uniform(0.0001, 0.0005):.18f}")
    eth_amt = float(f"{gte_amt * GTE_TO_ETH_RATE:.18f}")
    gte_amt_wei = w3.to_wei(gte_amt, 'ether')
    eth_amt_wei = w3.to_wei(eth_amt, 'ether')
    gte_balance = gte_contract.functions.balanceOf(wallet.address).call()
    eth_balance = w3.eth.get_balance(wallet.address)
    if eth_balance < eth_amt_wei or gte_balance < gte_amt_wei:
        return
    approved = approve_gte(wallet, gte_amt_wei)
    if not approved:
        return
    time.sleep(TX_DELAY)
    deadline = int(time.time()) + 60 * 20
    nonce = w3.eth.get_transaction_count(wallet.address, 'pending')
    tx = router.functions.addLiquidityETH(
        GTE_ADDRESS, gte_amt_wei, 0, 0, wallet.address, deadline
    ).build_transaction({
        'from': wallet.address,
        'value': eth_amt_wei,
        'gas': 460547,
        'gasPrice': get_gas_price(),
        'nonce': nonce,
        'chainId': CHAIN_ID,
    })
    signed = wallet.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

def main():
    wallets = [w3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    for wallet in wallets:
        print(f'Wallet: {wallet.address}')
        for i in range(SWAP_PER_WALLET):
            amt = float(f"{random.uniform(0.0001, 0.00025):.18f}")
            if i % 2 == 0:
                swap_eth_for_tokens(wallet, amt)
            else:
                swap_tokens_for_eth(wallet, amt)
            time.sleep(TX_DELAY)
        for _ in range(LIQ_PER_WALLET):
            add_liquidity(wallet)
            time.sleep(TX_DELAY)
    print('Done.')

main()
