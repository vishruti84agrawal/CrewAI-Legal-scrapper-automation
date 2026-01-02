# Washington State Foreclosure Data Extraction

Automated foreclosure data collection system for Washington State using AI agents. This project extracts, verifies, and formats foreclosure records from Elite Posting & Publishing website into ATTOM-compliant Excel templates.

## 🎯 Overview

This POC (Proof of Concept) demonstrates an AI-driven workflow using CrewAI agents to:
- **Scrape** foreclosure data from Elite Posting & Publishing website
- **Solve CAPTCHA** challenges automatically using Vision LLM and OCR
- **Parse and map** foreclosure records to ATTOM Foreclosure Template V6.7
- **Verify addresses** via Google Maps integration
- **Generate Excel reports** with properly formatted data

The system processes **two date ranges automatically**:
1. **Previous month to current date** (e.g., Dec 1, 2025 - Jan 1, 2026)
2. **Current date to next month** (e.g., Jan 1, 2026 - Feb 1, 2026)

## 🏗️ Architecture

The project uses a **three-agent workflow**:

### 1. Navigator Agent
- Accesses Elite Posting & Publishing website
- Handles CAPTCHA verification using enhanced solver
- Submits search forms with date range parameters
- Saves HTML results for parsing

### 2. Data Mapper Agent
- Reads saved HTML files
- Extracts foreclosure records from tables
- Parses multi-line fields (Trustee, Address)
- Verifies addresses via Google Maps links
- Saves structured data to JSON files

### 3. Auditor Agent
- Reads JSON files with foreclosure records
- Loads ATTOM Foreclosure Template V6.7
- Maps fields to correct template columns
- Generates formatted Excel files

## 📁 Project Structure

```
attomcrawl/
├── agents.py                 # AI agent definitions (navigator, data_mapper, auditor)
├── tasks.py                  # Task descriptions for each agent
├── tools.py                  # Tool implementations (scraper, parsers, writers)
├── main.py                   # Workflow orchestration with date range handling
├── captcha_solver.py         # CAPTCHA solving logic (Vision LLM + OCR)
├── requirements.txt          # Python dependencies
├── docs/
│   └── ATTOM Foreclosure Template V6.7.xls   # Excel template
├── json_results/             # Extracted JSON data by date range
├── output/                   # Generated Excel files by date range
└── .venv/                    # Virtual environment
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key (for GPT-4)
- Windows/Linux/macOS

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd attomcrawl
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure API Key**
   
   Open `main.py` and update line 10 with your OpenAI API key:
   ```python
   os.environ["OPENAI_API_KEY"] = "your-api-key-here"
   ```

   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## 🏃 Running the Project

### Basic Execution

Simply run the main script:

```bash
python main.py
```

### What Happens

The system will automatically:

1. **Generate Date Ranges**
   - Range 1: Previous month to current date
   - Range 2: Current date to next month

2. **Process Range 1**
   - Navigate to Elite Posting & Publishing
   - Solve CAPTCHA
   - Submit search form with dates
   - Save HTML results
   - Parse and map data
   - Verify addresses via Google Maps
   - Save JSON file
   - Generate Excel file

3. **Wait 3 seconds** (rate limit protection)

4. **Process Range 2**
   - Repeat all steps for second date range

5. **Show Summary**
   - Display success/failure status for each range
   - List generated files

### Expected Output

After successful execution, you'll find:

**Range 1 Files:**
- `search_results_12-01-2025_to_01-01-2026.html`
- `json_results/foreclosures_WA_King_12-01-2025_to_01-01-2026.json`
- `output/foreclosures_WA_King_12-01-2025_to_01-01-2026.xlsx`

**Range 2 Files:**
- `search_results_01-01-2026_to_02-01-2026.html`
- `json_results/foreclosures_WA_King_01-01-2026_to_02-01-2026.json`
- `output/foreclosures_WA_King_01-01-2026_to_02-01-2026.xlsx`

## 📊 Output Format

### JSON Schema

Each JSON file contains:
```json
{
  "metadata": {
    "search_date": "2026-01-01T10:00:00",
    "state": "WA",
    "county": "King",
    "start_date": "12/01/2025",
    "end_date": "01/01/2026",
    "total_records": 5,
    "record_type": "T - Trustee Sale"
  },
  "records": [
    {
      "Record_Type": "T",
      "EPP_Number": "43054",
      "TS_Number": "234-5",
      "Trustee_Name": "North Star Trustee, LLC",
      "Trustee_Address": "6100 219th St SW, Suite 480",
      "Trustee_City": "Mountlake Terrace",
      "Trustee_State": "WA",
      "Trustee_Zip": "98043",
      "Sale_Date": "01/15/2026",
      "Sale_Time": "10:00 AM",
      "Situs_Address": "1512 3RD AVE",
      "Situs_City": "SEATTLE",
      "Situs_State": "WASHINGTON",
      "Situs_Zip": "98119",
      "Address_Link": "http://maps.google.com/maps?q=...",
      "Address_Verified": "Verified",
      "County": "King",
      "State": "WA",
      "Estimated_Sale_Amount": "$1,341,720.08",
      "Bid_Amount": "$500,000",
      "Status": "Active",
      "CAPTCHA_Status": "Solved"
    }
  ]
}
```

### Excel Format

Excel files follow the **ATTOM Foreclosure Template V6.7** structure with 60+ columns including:

- **Column A**: RECORD TYPE (T)
- **Column E**: FORECLOSURE DOC NO (EPP Number)
- **Column G**: TRUSTEE SALE NO (TS Number)
- **Columns AB-AF**: Trustee Name/Address/City/State/Zip
- **Columns AJ-AN**: Situs Address/City/County/State/Zip
- **Column AP**: APPRAISED VALUE (Estimated Sale Amount)
- **Column AQ**: MINIMUM BID (Bid Amount)
- **Columns AW-AX**: AUCTION DATE/TIME
- **Columns BL-BQ**: Custom tracking (Address Link, Verified Status, CAPTCHA Status)

## ⚙️ Configuration

### Modifying Date Ranges

Edit `main.py` - `generate_date_ranges()` function to customize:

```python
def generate_date_ranges():
    current_date = datetime.now()
    
    # Customize these ranges
    start_date_scenario1 = current_date - relativedelta(months=1)
    end_date_scenario1 = current_date
    
    start_date_scenario2 = current_date
    end_date_scenario2 = current_date + relativedelta(months=1)
    
    return [scenario1, scenario2]
```

### Changing County or State

Update `tasks.py` - `extraction_task` and `mapping_task` descriptions:
- Replace `"King"` with desired county
- Replace `"WA"` with desired state code

### Rate Limiting

Modify the delay between ranges in `main.py`:

```python
# Current: 3 seconds
time.sleep(3)

# Change to 5 seconds
time.sleep(5)
```

## 🔧 Tools & Technologies

- **CrewAI**: Multi-agent orchestration framework
- **OpenAI GPT-4**: LLM for intelligent parsing and decision-making
- **BeautifulSoup4**: HTML parsing
- **openpyxl**: Excel file generation
- **xlrd**: Legacy .xls template reading
- **requests**: HTTP requests for web scraping
- **python-dateutil**: Date range calculations

## 🎨 Key Features

✅ **Automatic CAPTCHA Solving** - Vision LLM + OCR fallback  
✅ **Address Verification** - Google Maps integration  
✅ **Multi-line Field Parsing** - Intelligent extraction of complex fields  
✅ **Dynamic Date Ranges** - Automatic date calculation  
✅ **Template Preservation** - Loads existing ATTOM template  
✅ **Rate Limit Protection** - Configurable delays between requests  
✅ **Error Handling** - Graceful failure with detailed logging  
✅ **Unique File Naming** - Separate files per date range  

## 🐛 Troubleshooting

### CAPTCHA Solving Fails

- Check OpenAI API key is valid
- Ensure `captcha_solver.py` is in the project directory
- Review CAPTCHA image quality in saved files

### No Records Found

- Verify date ranges have foreclosure sales
- Check website accessibility
- Review HTML files to confirm data is present

### Excel Generation Fails

- Ensure ATTOM template exists in `docs/` folder
- Verify JSON file was created successfully
- Check `xlrd` library is installed for .xls templates

### Rate Limit Errors

- Increase delay between date ranges in `main.py`
- Check OpenAI API usage limits
- Reduce number of concurrent requests

## 📝 License

[Your License Here]

## 👥 Contributing

[Your Contributing Guidelines Here]

## 📧 Contact

[Your Contact Information Here]

---

**Note**: This is a POC (Proof of Concept) project. Ensure compliance with website terms of service and data usage policies before production deployment.
