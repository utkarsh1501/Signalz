import pandas as pd
import requests
import json
from datetime import datetime as dt
import argparse
import time
import psycopg2
from psycopg2.extras import execute_values

API_URL = "https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString"
COCKROACH_URI = "postgresql://utkarsh:1zgU9KPihUlQY_mpnwlFMw@smooth-turkey-7412.jxf.gcp-europe-west1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"

def fetch_nifty_data(index_name, start_date, end_date, retries=3, timeout=60):
    start_date_str = dt.strptime(start_date, "%Y-%m-%d").strftime("%d-%b-%Y")
    end_date_str = dt.strptime(end_date, "%Y-%m-%d").strftime("%d-%b-%Y")
    
    print(f"\n🔄 Fetching data for {index_name} from {start_date_str} to {end_date_str}...")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.niftyindices.com/reports/historical-data",
        "Origin": "https://www.niftyindices.com"
    }

    payload = {
        "cinfo": json.dumps({
            "name": index_name,
            "startDate": start_date_str,
            "endDate": end_date_str,
            "indexName": index_name
        })
    }

    time.sleep(2)

    for attempt in range(retries):
        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()

            if "d" not in result or not result["d"]:
                print("⚠️ No data returned.")
                return None

            data = json.loads(result["d"])
            df = pd.DataFrame(data)

            if df.empty:
                print("⚠️ Data is empty.")
                return None

            df = df.rename(columns={
                "HistoricalDate": "date",
                "OPEN": "open",
                "HIGH": "high",
                "LOW": "low",
                "CLOSE": "close"
            })

            df["date"] = pd.to_datetime(df["date"], format="%d %b %Y")
            df = df[["date", "open", "high", "low", "close"]]
            df["index_name"] = index_name  # Add index name column

            print("✅ Data fetched successfully!")
            return df

        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                print("🚫 All retries failed.")
                return None
            time.sleep(2 ** attempt)

def save_to_cockroachdb(df):
    print("📤 Inserting data into CockroachDB...")
    conn = psycopg2.connect(COCKROACH_URI)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO niftydata (index_name, date, open, high, low, close)
        VALUES %s
        ON CONFLICT (index_name, date) DO UPDATE 
        SET open = excluded.open, 
            high = excluded.high, 
            low = excluded.low, 
            close = excluded.close;
    """

    values = [
        (
            row["index_name"],
            row["date"].date(),
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"])
        )
        for _, row in df.iterrows()
    ]

    try:
        execute_values(cur, insert_query, values)
        conn.commit()
        print("✅ Data inserted successfully!")
    except Exception as e:
        print(f"❌ Failed to insert data: {e}")
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Fetch NIFTY historical index data.")
    parser.add_argument("--index-name", required=True, help="e.g., NIFTY BANK")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")

    args = parser.parse_args()

    df = fetch_nifty_data(args.index_name, args.start_date, args.end_date)
    if df is not None:
        save_to_cockroachdb(df)

if __name__ == "__main__":
    main()
