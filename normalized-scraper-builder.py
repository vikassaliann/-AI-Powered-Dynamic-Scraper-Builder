import asyncio
import os
from autogen_agentchat.agents import (
    AssistantAgent,
    CodeExecutorAgent,
)
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.models.anthropic import AnthropicBedrockChatCompletionClient, BedrockInfo
from autogen_core.models import ModelInfo
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_agentchat.messages import TextMessage
from dotenv import load_dotenv
# https://search.sunbiz.org/Inquiry/CorporationSearch/ByName
# name,status,filing information, principal address, annual reports

load_dotenv()
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_session_token = os.environ.get("AWS_SESSION_TOKEN") 
aws_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"

if not aws_access_key or not aws_secret_key:
    print("Error: AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) not found.")
    print("Please set them as environment variables or in a .env file.")
    exit(1)

model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
client = AnthropicBedrockChatCompletionClient(
    model=model_id,
    timeout_seconds=300,
    model_info=ModelInfo(
        vision=True,
        function_calling=True,
        json_output=False,
        family="claude-3-sonnet",
        structured_output=False
    ),
    bedrock_info=BedrockInfo(
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        aws_session_token=aws_session_token,
        aws_region=aws_region
    ),
)

print("Configuring AutoGen agent team...")
output_dir = os.path.join(os.getcwd(), "scraping_output")
os.makedirs(output_dir, exist_ok=True)
print(f"Executor will save files to: {output_dir}")

code_executor = LocalCommandLineCodeExecutor(
    work_dir=output_dir,
)
executor = CodeExecutorAgent(
    name="Executor",
    code_executor=code_executor,
)

web_surfer = MultimodalWebSurfer(
    name="WebSurfer",
    model_client=client,
    headless=True,
    description="A web surfing agent that can navigate, search, and report URLs."
)

coder = AssistantAgent(
    name="CoderAgent",
    model_client=client,
    system_message=(
        "You are an expert Python developer. You write clean, standalone Python scripts. "
        "You MUST follow all instructions perfectly."
        "You MUST use `curl_cffi.requests.Session` and `BeautifulSoup` for all scraping."
        "**DO NOT** use Playwright or Selenium in your final scripts."
        "The first line MUST be '# filename: <filename>.py'."
        "You MUST use `requests.exceptions.RequestException` for error handling."
        "\n\n"
        "**CRITICAL INSTRUCTION: KNOWN-GOOD SELECTORS**\n"
        "When you write the final scraper, you MUST use the following logic to extract data. DO NOT GUESS or use any other selectors."
        "\n"
        "**A. SELECTOR FOR THE *SEARCH RESULTS* PAGE:**\n"
        "1.  **First Result Link:** `soup.select_one('td:nth-of-type(3) a[href*=\"SearchResultDetail\"]')`\n"
        "\n"
        "**B. SELECTORS FOR THE *DETAIL* PAGE (after following a result link):**\n"
        "1.  **'Next On List' Link:** `soup.find('a', title='Next On List')`\n"
        "2.  **Name:**\n"
        "    `name_element = soup.select_one(\"div.corporationName p:nth-of-type(2)\")`\n"
        "    `name = name_element.text.strip() if name_element else \"N/A\"`\n"
        "\n"
        "3.  **Filing Info (as a dictionary):**\n"
        "    ```python\n"
        "    filing_info = {{}}\n"
        "    filing_container = soup.select_one(\"div.filingInformation > span > div\")\n"
        "    if filing_container:\n"
        "        labels = filing_container.find_all(\"label\")\n"
        "        for label in labels:\n"
        "            key = label.text.strip()\n"
        "            value_span = label.find_next_sibling(\"span\")\n"
        "            if value_span:\n"
        "                value = value_span.text.strip()\n"
        "                filing_info[key] = value\n"
        "    ```\n"
        "4.  **Status:**\n"
        "    `status = filing_info.get(\"Status\", \"N/A\")`\n"
        "\n"
        "5.  **Principal Address:**\n"
        "    ```python\n"
        "    address = \"N/A\"\n"
        "    # Try 'Principal Address' first (for LLCs)\n"
        "    address_span = soup.find(\"span\", string=lambda t: t and \"Principal Address\" in t)\n"
        "    if address_span:\n"
        "        address_div = address_span.find_next_sibling(\"span\").div\n"
        "        if address_div:\n"
        "            address = ' '.join(address_div.stripped_strings)\n"
        "    \n"
        "    # If not found, try 'Owners' section (for Trademarks, like KFC)\n"
        "    if address == \"N/A\":\n"
        "        owners_span = soup.find(\"span\", string=\"Owners\")\n"
        "        if owners_span:\n"
        "            owner_div = owners_span.find_parent(\"div\", class_=\"detailSection\")\n"
        "            if owner_div:\n"
        "                address_div = owner_div.find(\"div\")\n"
        "                if address_div:\n"
        "                    address = ' '.join(address_div.stripped_strings)\n"
        "    ```\n"
        "6.  **Annual Reports (as a list of dictionaries):**\n"
        "    ```python\n"
        "    annual_reports = []\n"
        "    reports_span = soup.find(\"span\", string=lambda t: t and \"Annual Reports\" in t)\n"
        "    if reports_span:\n"
        "        reports_table = reports_span.find_next_sibling(\"table\")\n"
        "        if reports_table:\n"
        "            for row in reports_table.find_all(\"tr\")[1:]:\n"
        "                cols = row.find_all(\"td\")\n"
        "                if len(cols) == 2:\n"
        "                    year = cols[0].text.strip()\n"
        "                    date_filed = cols[1].text.strip()\n"
        "                    annual_reports.append({{\"Year\": year, \"Filed Date\": date_filed}})\n"
        "    ```\n"
    )
)

team = MagenticOneGroupChat(
    participants=[executor, web_surfer, coder],
    model_client=client,
    max_turns=50, 
)

async def main():
    print("--- Dynamic Scraper Bot (Relational DB + Pagination) ---")
    print("Please provide the following details:\n")

    target_url = input("1. What is the STARTING URL? \n> ")
    search_term = input("2. What is the SEARCH TERM? (e.g., BLACK FROG LLC)\n> ")
    data_to_scrape = input("3. What data do you want to scrape? (e.g., 'Filing Information, Principal Address, Annual Reports')\n> ")
    final_script_name = input("4. What do you want to name the final .py file? (e.g., my_scraper.py)\n> ")
    
    limit_input = input("5. How many businesses to scrape? (e.g., 5, or type 'ALL' for no limit)\n> ")
    
    try:
        scrape_limit = int(limit_input)
    except ValueError:
        if limit_input.strip().upper() == 'ALL':
            scrape_limit = -1 
        else:
            print("Invalid limit. Defaulting to 5.")
            scrape_limit = 5

    if not final_script_name.endswith(".py"):
        final_script_name += ".py"

    TASK = f"""
    **Overall Goal:** Create a standalone Python script named `{final_script_name}` that scrapes data matching "{search_term}" by **following the 'Next On List' links** (Pagination) and stores it in a **normalized SQLite database (3 tables)**.

    ---
    **Phase 1: (WebSurfer's Job) - INVESTIGATE**
    1.  **Navigate:** Go to `{target_url}`.
    2.  **Search:** Perform a search for the term: "{search_term}".
    3.  **Locate:** On the search results page, find the link for the **FIRST match** for "{search_term}".
    4.  **Report:** Report the **URL of that first detail page**.
    
    *Your final report for the CoderAgent must include this "First Detail Page URL".*

    ---
    **Phase 2: (CoderAgent's Job) - BUILD RELATIONAL CRAWLER**
    1.  **Wait:** Wait for the WebSurfer's report.
    2.  **Write Final Script:** Write the **final standalone script** named `{final_script_name}`. This script MUST do the following:
        a. Import `sqlite3`, `curl_cffi.requests`, `bs4`.
        
        b. **Setup RELATIONAL Database (`sunbiz_normalized.db`):**
           i.  Create table `businesses` (id INTEGER PRIMARY KEY, name TEXT, status TEXT, principal_address TEXT).
           ii. Create table `filing_details` (id INTEGER PRIMARY KEY, business_id INTEGER, label TEXT, value TEXT, FOREIGN KEY(business_id) REFERENCES businesses(id)).
           iii. Create table `annual_reports` (id INTEGER PRIMARY KEY, business_id INTEGER, year TEXT, filed_date TEXT, FOREIGN KEY(business_id) REFERENCES businesses(id)).
        
        c. **Setup Scraper:**
           i.  Set start URL to the `First Detail Page URL` from the WebSurfer.
           ii. Initialize counter = 0 and limit = {scrape_limit}.
        
        d. **Implement the "Next On List" Loop:**
           i.   Start a loop with the condition: `while current_url and (limit == -1 or scraped_count < limit):`
           ii.  Visit the `current_url`.
           iii. Scrape data using **KNOWN-GOOD SELECTORS** from your system_message.
           
           iv.  **SAVE TO DB (Relational Logic):**
                * 1. Insert Name/Status/Address into `businesses`.
                * 2. Get the `lastrowid` (this is the `business_id`).
                * 3. Loop through the `filing_info` dictionary and insert each key/value pair into `filing_details` using the `business_id`.
                * 4. Loop through the `annual_reports` list and insert each report into `annual_reports` using the `business_id`.
                * 5. Commit changes.
           
           v.   **Increment the counter:** `scraped_count += 1`
           vi.  **Find "Next On List" link:** `next_link = soup.find('a', title='Next On List')`
           vii. If a `next_link` is found and has an `href`:
                `current_url = "https://search.sunbiz.org" + next_link['href']`
           viii. If no "Next On List" link is found, set `current_url = None` to break the loop.
        
        e. **Finish:**
           i.  Close the database connection.
           ii. Print a message: "Successfully scraped X records and saved to sunbiz_normalized.db".
           
        f. Include `try...except...finally` blocks. Use `requests.exceptions.RequestException` for request errors.
    
    ---
    **Phase 3: (Executor's Job) - EXECUTE**
    1.  **Run Final Script:** Run `{final_script_name}`.
    """

    print(f"\n--- Starting AutoGen Team with dynamic task ---")
    print(f"Goal: Create the '{final_script_name}' file.")

    stream = team.run_stream(task=TASK)

    print("\n--- Agent Conversation Log ---")

    async for message in stream:
        if isinstance(message, TextMessage):
            agent_name = message.source if message.source else "Unknown"
            content = message.content

            if isinstance(content, str):
                print(f"[{agent_name}]: {content}\n")

    print("--- AutoGen Team Task Finished ---")
    print(f"Check the '{output_dir}' directory for your script: {final_script_name}")
    print("Check for the database file: sunbiz_normalized.db")

    await web_surfer.close()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    asyncio.run(main())