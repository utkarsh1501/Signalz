import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os # Import the os module
 
def get_mentors_from_csv(csv_path):
    # Add a check to see if the file exists
    if not os.path.exists(csv_path):
        print(f"Error: The file '{csv_path}' was not found.")
        # You might want to raise an exception or return an empty list/None here
        return [] # Return an empty list if the file is not found
 
    df = pd.read_csv(csv_path)
    mentors = []
    for _, row in df.iterrows():
        mentors.append({
            'name': row['Name'],
            'sebi_reg_no': row['INH000016009']
        })
    return mentors
 
def get_validity_date(reg_no, driver):
    url = f'https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=14®no={reg_no}'
    driver.get(url)
    time.sleep(2)
 
    soup = BeautifulSoup(driver.page_source, 'html.parser')
 
    try:
        td = soup.find('td', string=lambda x: x and 'Validity' in x)
        validity_text = td.find_next_sibling('td').text.strip()
 
        # Handle "Perpetual" case
        if "Perpetual" in validity_text:
            return datetime(9999, 12, 31)  # Far-future date for perpetual validity
 
        for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%b %d, %Y']:
            try:
                return datetime.strptime(validity_text, fmt)
            except:
                continue
        return None
    except:
        return None
 
def main():
    csv_path = 'signal2_mentors_combined.csv'  # Ensure your CSV path is correct
    mentors = get_mentors_from_csv(csv_path)
 
    # If get_mentors_from_csv returned an empty list, exit gracefully
    if not mentors:
        print("Could not load mentor data. Exiting.")
        return
 
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
 
    today = datetime(2025, 6, 3)  # Set to current date: June 03, 2025
    valid_mentors = []
    invalid_mentors = []
 
    for mentor in mentors:
        reg_no = mentor['sebi_reg_no']
        validity = get_validity_date(reg_no, driver)
        if validity:
            if validity > today:
                valid_mentors.append({
                    'name': mentor['name'],
                    'sebi_reg_no': reg_no,
                    'validity': validity.strftime('%Y-%m-%d') if validity.year != 9999 else 'Perpetual'
                })
            else:
                invalid_mentors.append({
                    'name': mentor['name'],
                    'sebi_reg_no': reg_no,
                    'validity': validity.strftime('%Y-%m-%d')
                })
        else:
            invalid_mentors.append({
                'name': mentor['name'],
                'sebi_reg_no': reg_no,
                'validity': 'Not Found'
            })
 
    driver.quit()
 
    # Display results
    print("\n✅ Valid Mentors:")
    if valid_mentors:
        for vm in valid_mentors:
            print(f"- {vm['name']} (SEBI: {vm['sebi_reg_no']}, Valid till: {vm['validity']})")
    else:
        print("No valid mentors found.")
 
    print("\n❌ Invalid Mentors:")
    if invalid_mentors:
        for im in invalid_mentors:
            print(f"- {im['name']} (SEBI: {im['sebi_reg_no']}, Valid till: {im['validity']})")
    else:
        print("No invalid mentors found.")
 
if _name_ == "_main_":
    main()