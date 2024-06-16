import os
import json
from web3 import Web3
import pandas as pd
from tabulate import tabulate

# Hardcoded RPC URL and contract addresses
ANKR_API_URL = 'https://rpc.ankr.com/eth'
Q_CONTRACT_ADDRESS = '0xB09da56fa0f59E6a6Ea7C851AD30956351B0BB7D'
Q_PAYMENT_ADDRESS = '0xB207b52fe740d8981A78f1714c7089B662AA6c1f'
Q_ERC20_ADDRESS = '0xACA40632C51C2a03209D2714b88Aa0f1456A2101'
Q_BUYBURN_ADDRESS = '0x67a2afa58Ee0a32D0D33384E9fE204086D29CCfA'

# Load ABIs
def load_abi(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

abis = {
    'QContract': load_abi('abis/QContract.json'),
    'QPayment': load_abi('abis/QPayment.json'),
    'QERC20': load_abi('abis/QERC20.json'),
    'QBuyBurn': load_abi('abis/QBuyBurn.json'),
}

# Connect to the Ethereum network
web3 = Web3(Web3.HTTPProvider(ANKR_API_URL))

# Verify connection
if not web3.is_connected():
    raise ConnectionError("Failed to connect to the Ethereum network")

# Load contracts
QContract = web3.eth.contract(address=Q_CONTRACT_ADDRESS, abi=abis['QContract'])
QPayment = web3.eth.contract(address=Q_PAYMENT_ADDRESS, abi=abis['QPayment'])
QERC20 = web3.eth.contract(address=Q_ERC20_ADDRESS, abi=abis['QERC20'])
QBuyBurn = web3.eth.contract(address=Q_BUYBURN_ADDRESS, abi=abis['QBuyBurn'])

# Helper function to convert from Wei
def from_wei(value):
    return value / 10**18

# Get the latest cycle from the CSV if it exists
def get_latest_cycle_from_csv(file_path='cycle_stats.csv'):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if not df.empty:
            return df['Cycle'].max()
    return 0

# Fetch and display cycle statistics for all cycles
def fetch_cycle_stats(start_cycle):
    try:
        current_cycle = QContract.functions.currentCycle().call()
        if current_cycle <= start_cycle:
            print(f"No new cycles to fetch. Current cycle is {current_cycle}.")
            return None

        all_stats = []

        print(f"Fetching data for cycles {start_cycle + 1} to {current_cycle}...")
        for cycle in range(start_cycle + 1, current_cycle + 1):
            print(f"Fetching data for cycle {cycle}...")
            eth_in_cycle = QContract.functions.cycleAccruedFees(cycle).call()
            q_produced = QContract.functions.rewardPerCycle(cycle).call()
            total_entries_scaled = QContract.functions.cycleTotalEntries(cycle).call()
            eth_burned = QContract.functions.nativeBurnedPerCycle(cycle).call()
            total_q_supply = QContract.functions.summedCycleStakes(cycle).call()

            # Calculate the actual total batches
            total_batches = total_entries_scaled // 100

            stats = {
                'Cycle': cycle,
                'ETH In Cycle': round(from_wei(eth_in_cycle), 3),
                'Q Produced': round(from_wei(q_produced), 3),
                'Total Batches': total_batches,
                'Total Q Supply': round(from_wei(total_q_supply), 3),
                'ETH Burned': round(from_wei(eth_burned), 3)
            }

            all_stats.append(stats)

        return all_stats
    except Exception as e:
        print(f"Error fetching cycle stats: {e}")
        return None

def display_stats(all_stats):
    if all_stats:
        # Format data in green but not headers and borders
        formatted_stats = [
            {k: f'\033[92m{v}\033[0m' if k not in ['Cycle'] else v for k, v in stat.items()}
            for stat in all_stats
        ]
        print(tabulate(formatted_stats, headers='keys', tablefmt='pretty'))
    else:
        print("No stats to display.")

def save_stats_to_csv(all_stats, file_path='cycle_stats.csv'):
    if all_stats:
        df = pd.DataFrame(all_stats)
        if os.path.exists(file_path):
            df.to_csv(file_path, mode='a', header=False, index=False)
        else:
            df.to_csv(file_path, index=False)
    else:
        print("No stats to save.")

def main():
    latest_cycle = get_latest_cycle_from_csv()
    all_stats = fetch_cycle_stats(latest_cycle)
    if all_stats:
        display_stats(all_stats)
        save_stats_to_csv(all_stats)

if __name__ == '__main__':
    main()
