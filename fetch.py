# import redis
import os

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DataIngestor:
    def __init__(self):
        self.api_key = os.getenv("FINANCIAL_DATA_API_KEY")
        self.base_url = "https://financialdata.net/api/v1"
        # Connect to your Redis container
        # self.cache = redis.Redis(
        #     host='localhost', port=6379, db=0, decode_responses=True)

    def fetch_company_data(self, identifier: str):
        """
        Retrieves company info with Redis caching to avoid hitting API limits.
        """
        # cache_key = f"company_info:{identifier}"

        # 1. Check Redis Cache
        # cached_data = self.cache.get(cache_key)
        # if cached_data:
        #     print(f"i Loading {identifier} from Redis cache...")
        #     return json.loads(cached_data)

        # 2. Fetch from External API
        print(f"i Fetching {identifier} from FinancialData API...")
        url = f"{self.base_url}/stock-symbols"
        params = {
            "identifier": identifier,
            "key": self.api_key,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 3. Save to Redis (Expire in 24 hours)
            # self.cache.setex(cache_key, 86400, json.dumps(data))
            return data

        except requests.exceptions.RequestException as e:
            print(f"✗ API Error: {e}")

    def process_to_dataframe(self, raw_data):
        """
        Converts the JSON response into a Cleaned Pandas DataFrame
        """
        if not raw_data:
            return pd.DataFrame()

        df = pd.DataFrame(raw_data)

        # Select key ESG and metadata columns
        columns_to_keep = [
            'trading_symbol', 'registrant_name', 'industry',
            'chief_executive_officer', 'number_of_employees',
            'address_country', 'market_cap'
        ]

        # Only keep columns that actually exist in the response
        df_filtered = df[[col for col in columns_to_keep if col in df.columns]]

        return df_filtered


def process(raw_data):
    """Converts the JSON response into a Cleaned Pandas DataFrame"""
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)

    return df


def cycle():
    api_key = os.getenv("FINANCIAL_DATA_API_KEY")
    with open("links.txt") as file:
        links = []
        for line in file.readlines():
            links.append(line.strip())

    count = 0
    for url in links:
        params = {
            "key": api_key,
        }

        try:
            count+=1
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            clean = process(data)
            if not clean.empty:
                print(f"--- Processed Company Data <{count}> ---")
                # print(clean.to_string(index=False))
                clean.to_csv("processed_companies.csv", index=False, mode='a')

        except requests.exceptions.RequestException as e:
            print(f"✗ API Error: {e}")
            print(f"Company <{count}> ")

    print("result", count)
    return count





if __name__ == "__main__":
    # APPLE_INC_CIK = '0000320193'
    # APPLE_INC_ID = 'MSFT'

    # ingestor = DataIngestor()

    # # Run the process
    # raw_json = ingestor.fetch_company_data(APPLE_INC_ID)
    # clean_df = ingestor.process_to_dataframe(raw_json)

    # if not clean_df.empty:
    #     print("\n--- Processed Company Data ---")
    #     print(clean_df.to_string(index=False))

    #     # Example: Export for seeding your Database
    #     clean_df.to_csv("processed_companies.csv", index=False)
    #     print("\ni Data saved to processed_companies.csv")

    raw = cycle()
