import pandas as pd
from pymongo import MongoClient

uri = ""
client = MongoClient(uri, serverSelectionTimeoutMS=5000)

def test_connection():
    try:
        client.admin.command('ping')
        print(" MongoDB Connection Successful!")
        return True
    except Exception as e:
        print(f" An unexpected error occurred during connection: {e}")
    return False

if test_connection():
    db = client['US_Flight_Cancellation_Delay_History']
    collection = db['flights']

    csv_files = [
        'data/sample_2016.csv', 
        'data/sample_2017.csv', 
        'data/sample_2018.csv'
    ]

    for file in csv_files:
        try:
            print(f"\n--- Starting: {file} ---")
            df = pd.read_csv(file)
            data = df.to_dict(orient='records')
            
            if data:
                result = collection.insert_many(data)
                print(f" Successfully uploaded {len(result.inserted_ids)} records from {file}")
            else:
                print(f" Warning: {file} is empty.")
                
        except FileNotFoundError:
            print(f"Error: Could not find {file}. Check if the folder name is 'data'.")
        except Exception as e:
            print(f"An error occurred during upload for {file}: {e}")

    print("\nMission Accomplished: All files processed.")
else:
    print("\nAborting: Could not establish a stable connection to MongoDB.")