import sqlite3
import os
import sys

# Make sure this matches the DB name in the builder script
DB_NAME = "scraping_output/sunbiz_normalized.db"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    print("\n" + "=" * 60)
    print(f"   {text}")
    print("=" * 60)

def get_db_connection():
    if not os.path.exists(DB_NAME):
        print(f"Error: Database '{DB_NAME}' not found.")
        print("Please run the scraper script first to generate the data.")
        sys.exit(1)
    return sqlite3.connect(DB_NAME)

def view_filing_details(cursor, business_id):
    cursor.execute("SELECT label, value FROM filing_details WHERE business_id=?", (business_id,))
    rows = cursor.fetchall()
    
    print(f"\n   --- FILING DETAILS ---")
    print(f"   {'-'*50}")
    print(f"   | {'Label':<20} | {'Value':<23} |")
    print(f"   {'-'*50}")
    
    if not rows:
        print("   | (No filing details found)                    |")
    else:
        for label, value in rows:
            # Truncate long text for cleaner table
            lbl = (label[:18] + '..') if len(label) > 18 else label
            val = (value[:21] + '..') if len(value) > 21 else value
            print(f"   | {lbl:<20} | {val:<23} |")
    print(f"   {'-'*50}")

def view_annual_reports(cursor, business_id):
    cursor.execute("SELECT year, filed_date FROM annual_reports WHERE business_id=?", (business_id,))
    rows = cursor.fetchall()
    
    print(f"\n   --- ANNUAL REPORTS ---")
    print(f"   {'-'*35}")
    print(f"   | {'Year':<10} | {'Date Filed':<18} |")
    print(f"   {'-'*35}")
    
    if not rows:
        print("   | (No reports found)              |")
    else:
        for year, date in rows:
            print(f"   | {year:<10} | {date:<18} |")
    print(f"   {'-'*35}")

def show_business_details(conn, business_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, status, principal_address FROM businesses WHERE id=?", (business_id,))
    biz = cursor.fetchone()
    
    if not biz:
        print("Error: Business not found.")
        return

    clear_screen()
    print_header(f"DETAILS FOR: {biz[0]}")
    print(f"ID: {business_id}")
    print(f"STATUS: {biz[1]}")
    print(f"ADDRESS: {biz[2]}")
    
    # Show the linked tables
    view_filing_details(cursor, business_id)
    view_annual_reports(cursor, business_id)
    
    input("\nPress Enter to go back to the main list...")

def main_menu():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    while True:
        clear_screen()
        print_header("SUNBIZ DATABASE VIEWER")
        
        # Fetch all businesses
        cursor.execute("SELECT id, name, status FROM businesses")
        businesses = cursor.fetchall()
        
        print(f"{'ID':<5} | {'NAME':<40} | {'STATUS'}")
        print("-" * 60)
        
        for biz in businesses:
            print(f"{biz[0]:<5} | {biz[1]:<40} | {biz[2]}")
        
        print("-" * 60)
        print("Enter ID to view details (e.g., 1)")
        choice = input("Or type 'q' to quit > ")
        
        if choice.lower() == 'q':
            break
        
        if choice.isdigit():
            show_business_details(conn, int(choice))
    
    conn.close()
    print("Goodbye!")

if __name__ == "__main__":
    main_menu()