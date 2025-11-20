# filename: my_scraper.py
import sqlite3
from curl_cffi import requests
from bs4 import BeautifulSoup
import time

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY,
        name TEXT,
        status TEXT,
        principal_address TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS filing_details (
        id INTEGER PRIMARY KEY,
        business_id INTEGER,
        label TEXT,
        value TEXT,
        FOREIGN KEY(business_id) REFERENCES businesses(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS annual_reports (
        id INTEGER PRIMARY KEY,
        business_id INTEGER,
        year TEXT,
        filed_date TEXT,
        FOREIGN KEY(business_id) REFERENCES businesses(id)
    )
    ''')
    conn.commit()

def scrape_and_save(url, conn):
    session = requests.Session()
    scraped_count = 0
    limit = 10

    while url and (limit == -1 or scraped_count < limit):
        try:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract data using KNOWN-GOOD SELECTORS
            name_element = soup.select_one("div.corporationName p:nth-of-type(2)")
            name = name_element.text.strip() if name_element else "N/A"

            filing_info = {}
            filing_container = soup.select_one("div.filingInformation > span > div")
            if filing_container:
                labels = filing_container.find_all("label")
                for label in labels:
                    key = label.text.strip()
                    value_span = label.find_next_sibling("span")
                    if value_span:
                        value = value_span.text.strip()
                        filing_info[key] = value

            status = filing_info.get("Status", "N/A")

            address = "N/A"
            address_span = soup.find("span", string=lambda t: t and "Principal Address" in t)
            if address_span:
                address_div = address_span.find_next_sibling("span").div
                if address_div:
                    address = ' '.join(address_div.stripped_strings)

            if address == "N/A":
                owners_span = soup.find("span", string="Owners")
                if owners_span:
                    owner_div = owners_span.find_parent("div", class_="detailSection")
                    if owner_div:
                        address_div = owner_div.find("div")
                        if address_div:
                            address = ' '.join(address_div.stripped_strings)

            annual_reports = []
            reports_span = soup.find("span", string=lambda t: t and "Annual Reports" in t)
            if reports_span:
                reports_table = reports_span.find_next_sibling("table")
                if reports_table:
                    for row in reports_table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        if len(cols) == 2:
                            year = cols[0].text.strip()
                            date_filed = cols[1].text.strip()
                            annual_reports.append({"Year": year, "Filed Date": date_filed})

            # Save to database
            cursor = conn.cursor()
            cursor.execute("INSERT INTO businesses (name, status, principal_address) VALUES (?, ?, ?)",
                           (name, status, address))
            business_id = cursor.lastrowid

            for key, value in filing_info.items():
                cursor.execute("INSERT INTO filing_details (business_id, label, value) VALUES (?, ?, ?)",
                               (business_id, key, value))

            for report in annual_reports:
                cursor.execute("INSERT INTO annual_reports (business_id, year, filed_date) VALUES (?, ?, ?)",
                               (business_id, report['Year'], report['Filed Date']))

            conn.commit()

            scraped_count += 1

            # Find "Next On List" link
            next_link = soup.find('a', title='Next On List')
            if next_link and 'href' in next_link.attrs:
                url = "https://search.sunbiz.org" + next_link['href']
            else:
                url = None

            time.sleep(1)  # Be nice to the server

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            break

    return scraped_count

def main():
    start_url = "https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=BLACKFROG%20L230000072140&aggregateId=flal-l23000007214-8dc00d53-ceda-4ca2-bb26-4f1ea0d171a9&searchTerm=BLACK%20FROG%20LLC&listNameOrder=BLACKFROG%20L230000072140"
    
    conn = sqlite3.connect('sunbiz_normalized.db')
    create_tables(conn)

    try:
        scraped_count = scrape_and_save(start_url, conn)
        print(f"Successfully scraped {scraped_count} records and saved to sunbiz_normalized.db")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()