import os
import json
from web3 import Web3
import pandas as pd
from tabulate import tabulate
from datetime import datetime

# Hardcoded RPC URL and contract addresses
ANKR_API_URL = 'https://rpc.ankr.com/eth'
Q_CONTRACT_ADDRESS = '0xB09da56fa0f59E6a6Ea7C851AD30956351B0BB7D'
Q_PAYMENT_ADDRESS = '0xB207b52fe740d8981A78f1714c7089B662AA6c1f'
Q_ERC20_ADDRESS = '0xACA40632C51C2a03209D2714b88Aa0f1456A2101'
Q_BUYBURN_ADDRESS = '0x67a2afa58Ee0a32D0D33384E9fE204086D29CCfA'
BURN_ADDRESS = '0x000000000000000000000000000000000000dead'

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
QERC20 = web3.eth.contract(address=Q_ERC20_ADDRESS, abi=abis['QERC20'])

# Convert BURN_ADDRESS to checksum address
BURN_ADDRESS_CHECKSUM = Web3.to_checksum_address(BURN_ADDRESS)

# Helper function to convert from Wei
def from_wei(value):
    return value / 10**18

# Fetch and display cycle statistics for all cycles starting from cycle 0
def fetch_cycle_stats():
    try:
        current_cycle = QContract.functions.currentCycle().call()
        all_stats = []

        print(f"Fetching data for cycles 0 to {current_cycle}...")
        for cycle in range(0, current_cycle + 1):
            print(f"Fetching data for cycle {cycle}...")
            eth_in_cycle = QContract.functions.cycleAccruedFees(cycle).call()
            q_produced = QContract.functions.rewardPerCycle(cycle).call()
            total_entries_scaled = QContract.functions.cycleTotalEntries(cycle).call()
            eth_burned = QContract.functions.nativeBurnedPerCycle(cycle).call()
            total_staked_q = QContract.functions.summedCycleStakes(cycle).call()

            # Calculate the actual total batches
            total_batches = total_entries_scaled // 100

            stats = {
                'Cycle': cycle,
                'ETH In Cycle': round(from_wei(eth_in_cycle), 3),
                'Q Produced': round(from_wei(q_produced), 3),
                'Total Batches': total_batches,
                'Total Staked Q': round(from_wei(total_staked_q), 3),
            }

            # Calculate change in stake
            if cycle > 0:
                previous_staked_q = all_stats[-1]['Total Staked Q']
                stats['Change in Stake'] = round(stats['Total Staked Q'] - previous_staked_q, 3)
            else:
                stats['Change in Stake'] = 0

            stats['ETH Burned'] = round(from_wei(eth_burned), 3)

            all_stats.append(stats)

        return all_stats
    except Exception as e:
        print(f"Error fetching cycle stats: {e}")
        return None

def display_stats(all_stats):
    if all_stats:
        print(tabulate(all_stats, headers='keys', tablefmt='pretty'))
    else:
        print("No stats to display.")

def save_stats_to_csv(all_stats, file_path='cycle_stats.csv', update_file='last_update.txt'):
    if all_stats:
        df = pd.DataFrame(all_stats)
        print("DataFrame to save:\n", df)

        # Always write new data by deleting existing files first
        if os.path.exists(file_path):
            os.remove(file_path)
        df.to_csv(file_path, index=False)
        print(f"New DataFrame saved to {file_path}")

        # Write the last update time
        with open(update_file, 'w') as f:
            f.write(f"This data was last updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
        print(f"Update file saved to {update_file}")
    else:
        print("No stats to save.")

def fetch_current_cycle_data():
    try:
        current_cycle = QContract.functions.currentCycle().call()
        total_staked_q = QContract.functions.summedCycleStakes(current_cycle).call()
        total_supply = QERC20.functions.totalSupply().call()
        burned_balance = QERC20.functions.balanceOf(BURN_ADDRESS_CHECKSUM).call()
        eth_in_cycle = QContract.functions.cycleAccruedFees(current_cycle).call()

        # Calculate circulating supply correctly
        total_circulating_supply = from_wei(total_supply - burned_balance)
        total_supply_corrected = from_wei(total_supply + total_staked_q - burned_balance)
        percentage_staked = (from_wei(total_staked_q) / total_supply_corrected) * 100

        data = {
            'Current Cycle': current_cycle,
            'Total Circulating Supply': round(total_circulating_supply, 3),
            'Total Staked Q': round(from_wei(total_staked_q), 3),
            'Total Supply': round(total_supply_corrected, 3),
            'Total Q Burned': round(from_wei(burned_balance), 3),
            'Percentage Staked': round(percentage_staked, 2),
            'ETH in Cycle': round(from_wei(eth_in_cycle), 3)
        }

        return data
    except Exception as e:
        print(f"Error fetching current cycle data: {e}")
        return None

def save_current_cycle_data_to_csv(data, file_path='current_cycle.csv'):
    if data:
        df = pd.DataFrame([data])
        df.to_csv(file_path, index=False)
        print(f"New DataFrame saved to {file_path}")

def main():
    # Fetch cycle statistics and save to CSV
    all_stats = fetch_cycle_stats()
    if all_stats:
        display_stats(all_stats)
        save_stats_to_csv(all_stats)

    # Fetch current cycle data and save to CSV
    current_cycle_data = fetch_current_cycle_data()
    if current_cycle_data:
        print(current_cycle_data)
        save_current_cycle_data_to_csv(current_cycle_data)

if __name__ == '__main__':
    main()
