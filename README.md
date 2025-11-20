# 🤖 AI-Powered Dynamic Scraper Builder

An autonomous **multi-agent system** that builds, tests, and deploys custom web crawlers using **AWS Bedrock** and **AutoGen**.

This project is not just a web scraper; it is a **Scraper Factory**.  
It uses a team of AI agents to investigate a target website, analyze its structure, and write a robust, production-grade Python script to scrape data into a normalized relational database.

---

## 🚀 Features

### ✅ Multi-Agent Architecture  
Uses Microsoft’s **AutoGen** framework to coordinate:
- **WebSurfer (Investigator)**
- **Coder (Developer)**
- **Executor (Tester)**

### 🔎 Smart Investigation  
The agents use **Playwright** to browse target sites, perform searches, and map URL patterns and HTML structures *dynamically*.

### 🥷 Anti-Detection  
Generated scrapers use **curl_cffi** to impersonate a real browser (Chrome 110) to bypass common bot protections.

### 🗄️ Relational Database (3-Tier Schema)  
Automatically designs SQLite DB with:
- `businesses`
- `filing_details`
- `annual_reports`

### 🔁 Smart Pagination  
Implements “Next On List” crawling logic to scrape thousands of records automatically.

### 🧱 Duplicate Prevention  
Uses `UNIQUE` constraints and `INSERT OR IGNORE` to preserve data integrity.

### 🖥️ Offline Database Viewer  
Automatically generates a clean, interactive SQL viewer tool.

---

## 🛠️ System Architecture

The system runs in **3 automated phases**:

### **Phase 1 — Investigation**  
The WebSurfer agent:
- Navigates to the target URL (e.g., Sunbiz)
- Performs a real search
- Extracts link structures, parameters, and form data

### **Phase 2 — Construction**  
The AI CoderAgent:
- Designs DB schemas
- Builds a full `my_scraper.py` crawler
- Implements pagination and error handling

### **Phase 3 — Deployment**  
The Executor:
- Validates the generated code
- Saves files in `scraping_output/`

---

## 📋 Prerequisites

- Python **3.10+**
- AWS credentials with access to **Bedrock**
  - Recommended model: **Claude 3.5 Sonnet**
- Playwright installed

---

## 🔧 Installation

Clone the repo:

```bash
git clone https://github.com/yourusername/ai-scraper-builder.git
cd ai-scraper-builder
````

Install dependencies:

```bash
pip install pyautogen autogen-agentchat autogen-ext[anthropic] playwright curl_cffi beautifulsoup4 python-dotenv prettytable
playwright install
```

Create `.env` file:

```env
AWS_ACCESS_KEY_ID="your_access_key"
AWS_SECRET_ACCESS_KEY="your_secret_key"
AWS_SESSION_TOKEN="your_session_token"   # optional
AWS_REGION="us-east-1"
```

---

## ⚡ Usage Guide

### **1. Run the Builder**

```bash
python3 normalized_scraper_builder.py
```

You will be prompted for:

| Prompt          | Example                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Target URL      | [https://search.sunbiz.org/Inquiry/CorporationSearch/ByName](https://search.sunbiz.org/Inquiry/CorporationSearch/ByName) |
| Search Term     | BLACK FROG LLC                                                                                                           |
| Data to Scrape  | Name, Filing Info, Annual Reports                                                                                        |
| Output Filename | my_scraper.py                                                                                                            |
| Limit           | 10                                                                                                                       |

---

### **2. Run the Generated Scraper**

```bash
python3 scraping_output/my_scraper.py
```

This will:

* Fetch live data
* Auto-paginate
* Populate `sunbiz_relational.db`

---

### **3. View Data**

```bash
python3 scraping_output/view_data.py
```

This lets you browse DB tables without writing SQL.

---

## 📂 Project Structure

```
.
├── normalized_scraper_builder.py   # The AI orchestrator
├── .env                            # AWS credentials
├── README.md                       # Documentation
└── scraping_output/                # AI-generated folder
    ├── my_scraper.py               # The final scraper
    ├── view_data.py                # Viewer tool
    └── sunbiz_normalized.db        # SQLite relational dataset
```

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**.
Always verify compliance with:

* Website Terms of Service
* Applicable laws
* robots.txt restrictions

You are responsible for how you use this tool.
