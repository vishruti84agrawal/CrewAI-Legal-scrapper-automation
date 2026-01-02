from crewai import Agent, LLM
from tools import excel_writer, web_scraper, elite_posting_scraper, html_reader, json_writer, address_verifier, json_reader

# Using Groq via CrewAI's LLM wrapper with simplified configuration
llm = LLM(
    model="openai/gpt-4o",
    temperature=0
)

# Navigator Agent: Specialized in web scraping and data extraction for Washington State
navigator = Agent(
    role='Elite Posting Foreclosure Data Navigator',
    goal='Extract Washington State foreclosure data from Elite Posting & Publishing website with CAPTCHA handling.',
    backstory="""Expert web scraper specializing in Washington State foreclosure data collection from:
    
    ELITE POSTING & PUBLISHING WEBSITE:
    - Advanced CAPTCHA solving capabilities using OCR and pattern recognition
    - Experienced with Elite Posting search interface and workflow
    - Skilled in handling verification codes like "mpgmt", "ausivuTl", "Soxiguuy" formats
    - Expert in click-through address verification for accurate property descriptions
    - Specialized in filtering active "T RECORD" status vs "SOLD"/"Cancelled" records
    - Proficient in multi-county data extraction with proper date range management
    
    Technical expertise includes:
    - Automated form filling with State=WA, County selection, Date ranges
    - Real-time CAPTCHA image processing and verification code entry
    - Robust retry mechanisms for failed CAPTCHA attempts
    - Precise data extraction from search result tables
    - Address click-through automation for detailed property information
    
    Uses modern AI techniques for resilient data extraction, CAPTCHA solving, and automated field mapping to ATTOM standards.
    
    IMPORTANT: Only extracts REAL data from actual websites - no mock or dummy data allowed.
    Must handle real CAPTCHA challenges and website authentication as required.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
    tools=[elite_posting_scraper, web_scraper]
)

# Data Mapper Agent: Extracts and maps fields from HTML to ATTOM template
data_mapper = Agent(
    role='HTML Data Parser & ATTOM Field Mapper',
    goal='Parse foreclosure data from HTML tables and map to ATTOM Excel template fields intelligently.',
    backstory="""Expert in HTML parsing and data structure mapping specializing in foreclosure records.
    
    KEY RESPONSIBILITIES:
    1. READ HTML FILE: Open and parse search_results_debug.html saved by navigator agent
    2. IDENTIFY TABLE STRUCTURE: Find the results table with foreclosure records
    3. EXTRACT FIELDS from each row:
       - EPP# (Trustee Sale Number) - unique identifier
       - TS# (Secondary Trustee Number) - alternative identifier  
       - Trustee Details - multi-line field containing:
         * Company name (first line)
         * Street address (subsequent lines)
         * City, State, ZIP
       - Sale Date & Time - format: "Postponed to MM/DD/YYYY HH:MM AM/PM" or "MM/DD/YYYY HH:MM AM/PM"
       - Address - multi-line field containing:
         * Street address (first line) - EXTRACT THE CLICKABLE LINK URL
         * City (second line)
         * STATE ZIP (third line - split into state and zip)
       - Estimated Sale Amount - currency value
       - Bid Amount, Bid Info - financial details
       - Status - record status (filter out "Cancelled", "SOLD")
    
    4. INTELLIGENT PARSING LOGIC:
       - Split multi-line fields by newline characters
       - Parse dates: extract date and time separately
       - Parse addresses: identify street, city, state, zip components
       - Handle "Postponed to" prefix in sale dates
       - Extract numeric values from currency strings
    
    5. MAP TO ATTOM TEMPLATE:
       - Record_Type = "T" (Trustee Sale for WA)
       - Document_Number = EPP# 
       - EPP_Number = EPP#
       - TS_Number = TS#
       - Trustee_Name = First line of Trustee field
       - Trustee_Address = Remaining lines of Trustee field (joined)
       - Sale_Date = Parsed date (MM/DD/YYYY)
       - Sale_Time = Parsed time (HH:MM AM/PM)
       - Situs_Address = First line of Address field (street)
       - Address_Link = URL extracted from the clickable address link
       - Situs_City = Second line of Address field
       - Situs_State = State from third line (before ZIP)
       - Situs_Zip = ZIP from third line (after state)
       - Estimated_Sale_Amount = Numeric value
       - County = From search parameters
       - State = "WA"
    
    6. CREATE JSON OUTPUT: Structure as array of objects ready for Excel export
    
    FILTERING RULES:
    - EXCLUDE records with Status containing "Cancelled" or "SOLD"
    - EXCLUDE records where Sold field = "YES"
    - ONLY include active foreclosure records
    
    Expert in pattern recognition, text parsing, and data structure transformation.
    Can verify addresses by using address_verifier tool to extract accurate information from Google Maps links.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
    tools=[html_reader, address_verifier, json_writer]
)

# Auditor Agent: Enforces the Rejection Rules v5 and validates data quality
auditor = Agent(
    role='Compliance Auditor & Excel Output Generator',
    goal='Apply ATTOM rejection rules, map data to template, and generate Excel output using ATTOM template.',
    backstory="""Data quality specialist and Excel automation expert enforcing ATTOM Data Rejection Rules v5.
    
    Responsibilities:
    - Validate Washington State foreclosure records (Record Type T)
    - Ensure situs addresses start with numbers (WA requirement) 
    - Check required fields: Sale Date, Recording Date, City, County, State
    - Map Elite Posting data to ATTOM Foreclosure Template v6.7
    - Generate final Excel file using the ATTOM template from docs folder
    - Apply proper formatting and validation status tracking
    - Create comprehensive data quality reports
    
    Excel expertise:
    - Read JSON files with foreclosure data using json_reader tool
    - Load and use ATTOM Foreclosure Template V6.7.xls from docs folder
    - Map all fields from JSON to appropriate ATTOM template columns:
      * EPP#, TS#, Document Number
      * Sale Date, Sale Time
      * Trustee Name and Address
      * Situs Address, City, State, Zip
      * County, State (WA)
      * Estimated Sale Amount, Bid Amount, Bid Info
      * Status, Sold
      * Address Verified, Address Link, CAPTCHA Status
    - Apply proper formatting and field validation
    - Save to output/foreclosure_data.xlsx""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
    tools=[json_reader, excel_writer]
)
