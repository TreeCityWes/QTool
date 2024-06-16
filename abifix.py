import os
import json

def reformat_abi(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                try:
                    abi_data = json.load(file)
                    if isinstance(abi_data, dict) and "result" in abi_data:
                        # Extract the ABI from the result field and parse it
                        raw_abi = abi_data["result"]
                        formatted_abi = json.loads(raw_abi)
                        with open(file_path, 'w') as outfile:
                            json.dump(formatted_abi, outfile, indent=4)
                        print(f"Reformatted ABI in file: {filename}")
                    else:
                        print(f"File {filename} is already in correct format or not containing the expected structure.")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from file {filename}: {e}")

if __name__ == "__main__":
    folder_path = "abis"
    reformat_abi(folder_path)
