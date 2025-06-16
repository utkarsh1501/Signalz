import pandas as pd

def check_validity(csv_path):
    try:
        df = pd.read_csv(csv_path)

        # Normalize column names
        df.columns = [col.strip() for col in df.columns]

        # Check required columns
        if 'Name' not in df.columns or 'SEBI Registration No.' not in df.columns or 'Validity' not in df.columns:
            print("Error: CSV must contain 'Name', 'SEBI Registration No.' and 'Validity' columns.")
            return

        valid_mentors = []
        invalid_mentors = []

        for index, row in df.iterrows():
            name = row['Name'].strip()
            reg_no = row['SEBI Registration No.'].strip()
            validity = str(row['Validity']).strip().lower()

            if validity == 'perpetual':
                valid_mentors.append(f"{name} ({reg_no})")
            else:
                invalid_mentors.append(f"{name} ({reg_no})")

        print("\n✅ Valid Mentors:")
        for mentor in valid_mentors:
            print(f"- {mentor}")

        print("\n❌ Invalid Mentors:")
        for mentor in invalid_mentors:
            print(f"- {mentor}")

    except Exception as e:
        print(f"Error: {e}")

# Run
if __name__ == "__main__":
    check_validity("signalz_mentors_combined.csv")
