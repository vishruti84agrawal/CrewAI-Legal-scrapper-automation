from crewai import Task
from agents import navigator, data_mapper, auditor

# Task 1: Extract Washington State foreclosure data from Elite Posting & Publishing
extraction_task = Task(
    description="""
    EXTRACT REAL WASHINGTON STATE FORECLOSURE DATA FROM ELITE POSTING & PUBLISHING WEBSITE:
    
    CRITICAL: NO MOCK DATA - Extract only real, live data from actual website.
    
    1. WEBSITE ACCESS AND NAVIGATION:
    - Use elite_posting_scraper tool to access actual Elite Posting & Publishing website
    - Navigate to the real Search section on the live website
    - Handle any authentication, login, or access requirements
    
    2. SEARCH PARAMETERS SETUP:
    - Access the actual search form on Elite Posting & Publishing website
    - Set State dropdown to "WA" (Washington) 
    - Set County dropdown to "King" (start with King County)
    - Configure Sale Date Range on the real form:
      * Start Date: 01/01/2026  (DYNAMIC - will be replaced with actual date range)
      * End Date: 01/31/2026    (DYNAMIC - will be replaced with actual date range)
    - Leave EPP#, TS#, APN, City, and Zip Code fields empty for broad search
    
    3. REAL CAPTCHA VERIFICATION HANDLING:
    - CRITICAL: Solve actual CAPTCHA verification that appears on the website
    - Use the enhanced CAPTCHA solver (Vision LLM + APIs + OCR)
    - Automatically attempt solving with fallback methods
    - Implement proper error handling for CAPTCHA failures
    
    4. SAVE HTML RESPONSE:
    - Use elite_posting_scraper tool with parameters:
      * state: "WA"
      * county: "King"
      * start_date: "01/01/2026"  (DYNAMIC - replaced at runtime)
      * end_date: "01/31/2026"    (DYNAMIC - replaced at runtime)
      * output_file: "search_results_debug.html"  (DYNAMIC - replaced with unique filename)
    - The tool will save the search results HTML to the specified output_file
    - This file will be used by the next agent for data extraction
    - Ensure the HTML file contains the complete table with all records
    
    5. RETURN SEARCH STATUS:
    - Report number of tables found in response
    - Report page title and any error messages
    - Provide path to saved HTML file
    - DO NOT attempt to parse or map data - that's the next agent's job
    
    DELIVERABLE: Successfully execute search and save HTML response file for data mapper agent.
    """,
    expected_output="""
    Search execution report:
    - CAPTCHA status (solved/failed)
    - Search submission status (success/failure)
    - Number of tables found in response
    - Path to saved HTML file (search_results_debug.html)
    - Page title from response
    - Any error messages encountered
    """,
    agent=navigator
)

# Task 2: Parse HTML and map fields to ATTOM template
mapping_task = Task(
    description="""
    PARSE HTML RESULTS AND MAP TO ATTOM TEMPLATE FIELDS:
    
    1. READ SAVED HTML FILE:
    - Open the file 'search_results_debug.html' (DYNAMIC - replaced with actual filename for date range)
    - Parse the HTML to identify the results table structure
    
    2. IDENTIFY TABLE STRUCTURE:
    - Find the table containing foreclosure records
    - Identify column headers: EPP#, TS#, Trustee, Sale Date, Address, Estimated Sale Amount, Bid Amount, Bid Info, Sold, Status
    
    3. EXTRACT DATA FROM EACH ROW:
    For each table row (excluding header), extract:
    
    a) EPP# - Unique foreclosure identifier (e.g., "43054")
    
    b) TS# - Trustee sale number (e.g., "234-5")
    
    c) Trustee - Multi-line field, parse into:
       - Line 1: Company name (e.g., "North Star Trustee, LLC")
       - Line 2-N: Address components (e.g., "6100 219th St SW, Suite 480 Mountlake Terrace, WA 98043")
         * Parse address to extract: Street, City, State, ZIP
         * Example: "6100 219th St SW, Suite 480 Mountlake Terrace, WA 98043" →
           Trustee_Address: "6100 219th St SW, Suite 480"
           Trustee_City: "Mountlake Terrace"
           Trustee_State: "WA"
           Trustee_Zip: "98043"
       → Output: Trustee_Name, Trustee_Address, Trustee_City, Trustee_State, Trustee_Zip
    
    d) Sale Date - Parse format "Postponed to MM/DD/YYYY HH:MM AM/PM" or "MM/DD/YYYY HH:MM AM/PM":
       - Remove "Postponed to" prefix if present
       - Extract date part (MM/DD/YYYY)
       - Extract time part (HH:MM AM/PM)
       → Output: Sale_Date and Sale_Time
    
    e) Address - Multi-line field, parse into:
       - Line 1: Street address (e.g., "1512 3RD AVE") - EXTRACT THE CLICKABLE LINK URL
       - Line 2: City (e.g., "SEATTLE")
       - Line 3: STATE ZIP (e.g., "WASHINGTON 98119")
         * Split line 3 to get State and ZIP separately
       → Output: Situs_Address, Address_Link (URL), Situs_City, Situs_State, Situs_Zip
    
    f) Estimated Sale Amount - Currency value (e.g., "$1,341,720.08")
       → Output: Estimated_Sale_Amount
    
    g) Bid Amount, Bid Info - Financial details
       → Output: Bid_Amount, Bid_Info
    
    h) Sold, Status - Record status indicators
       → Output: Sold, Status
    
    4. FILTERING LOGIC:
    - SKIP records where Status contains "Cancelled"
    - SKIP records where Sold = "YES"
    - ONLY include active foreclosure records
    
    5. MAP TO ATTOM TEMPLATE FORMAT:
    Create JSON array where each record has:
    {
      "Record_Type": "T",
      "EPP_Number": <from EPP# column>,
      "TS_Number": <from TS# column>,
      "Document_Number": <same as EPP#>,
      "Trustee_Name": <first line from Trustee field>,
      "Trustee_Address": <street address from Trustee field>,
      "Trustee_City": <city parsed from Trustee address>,
      "Trustee_State": <state parsed from Trustee address>,
      "Trustee_Zip": <ZIP parsed from Trustee address>,
      "Sale_Date": <parsed date MM/DD/YYYY>,
      "Sale_Time": <parsed time HH:MM AM/PM>,
      "Situs_Address": <street from Address field>,
      "Address_Link": <URL from clickable address link>,
      "Situs_City": <city from Address field>,
      "Situs_State": <state from Address field>,
      "Situs_Zip": <ZIP from Address field>,
      "Estimated_Sale_Amount": <from table>,
      "Bid_Amount": <from table>,
      "Bid_Info": <from table>,
      "Status": <from table>,
      "Sold": <from table>,
      "County": "King",
      "State": "WA",
      "Address_Verified": "Pending",
      "CAPTCHA_Status": "Solved"
    }
    
    6. VERIFY ADDRESSES USING GOOGLE MAPS:
    - For EACH record, use address_verifier tool with the Address_Link
    - Extract accurate Situs_Address, Situs_City, Situs_State, Situs_Zip from Google Maps
    - REPLACE the parsed address components with verified accurate data from Google Maps
    - Update Address_Verified field to "Verified" (or "Failed" if verification fails)
    
    7. OUTPUT JSON:
    - Return structured JSON array of all mapped records with verified addresses
    - Include record count summary
    - List any parsing errors or warnings
    
    8. SAVE TO FILE:
    - Use json_writer tool to save the mapped records
    - Provide start_date: "01/01/2026" (DYNAMIC), end_date: "01/31/2026" (DYNAMIC), county, and state parameters
    - Tool will automatically create filename like: foreclosures_WA_King_01-01-2026_to_01-31-2026.json
    - File will be saved in json_results/ folder
    
    DELIVERABLE: JSON array of foreclosure records with all fields properly mapped to ATTOM template structure, addresses verified from Google Maps, AND saved to dated JSON file.
    """,
    expected_output="""
    JSON file saved with complete field mapping and verified addresses:
    - Filename format: foreclosures_WA_King_01-01-2026_to_01-31-2026.json
    - Saved in json_results/ folder
    - Each record fully mapped to ATTOM template fields
    - Multi-line fields parsed correctly (Trustee, Address)
    - Addresses verified using Google Maps links (Address_Verified = "Verified")
    - Dates and times extracted separately
    - Only active records included (filtered out cancelled/sold)
    - Summary: X records extracted, Y records filtered out, Z total in HTML, W addresses verified
    - File path returned for confirmation
    """,
    agent=data_mapper,
    context=[extraction_task]
)

# Task 3: Generate Excel output from JSON data
excel_generation_task = Task(
    description="""
    READ JSON DATA AND GENERATE EXCEL OUTPUT USING ATTOM TEMPLATE:
    
    1. READ JSON FILE:
    - Use json_reader tool to read the saved JSON file: json_results/foreclosures_WA_King_01-01-2026_to_01-31-2026.json (DYNAMIC filename)
    - Extract all records and metadata
    
    2. PREPARE DATA FOR EXCEL EXPORT:
    - Extract all foreclosure records from JSON
    - Verify all required fields are present:
      * Record_Type, EPP_Number, TS_Number, Document_Number
      * Trustee_Name, Trustee_Address
      * Sale_Date, Sale_Time
      * Situs_Address, Situs_City, Situs_State, Situs_Zip
      * County, State
      * Estimated_Sale_Amount, Bid_Amount, Bid_Info
      * Status, Sold
      * Address_Verified, Address_Link, CAPTCHA_Status
    
    3. WRITE TO EXCEL USING ATTOM TEMPLATE:
    - Use excel_writer tool with the following parameters:
      * data: list of all records from JSON
      * template_path: "docs/ATTOM Foreclosure Template V6.7.xls"
      * output_path: "output/foreclosures_WA_King_01-01-2026_to_01-31-2026.xlsx" (DYNAMIC filename)
    - The tool will load the existing template from docs folder
    - Add new rows with the foreclosure data
    - Save to output folder (preserving the original template)
    - Tool will automatically map fields to correct ATTOM template columns
    - Tool will apply proper formatting and column widths
    
    4. FIELD MAPPING (handled by excel_writer tool):
    - Column A: Record Type (T)
    - Column B: EPP Number
    - Column C: TS Number
    - Column D: Recording Date
    - Column E: Sale Date
    - Column F: Sale Time
    - Column G: Trustee Name
    - Column H: Trustee Address
    - Column I: Situs Address
    - Column J: Situs City
    - Column K: Situs State
    - Column L: Situs Zip
    - Column M: County
    - Column N: State
    - Column O: Estimated Sale Amount
    - Column P: Bid Amount
    - Column Q: Bid Info
    - Column R: Status
    - Column S: Sold
    - Column T: Address Verified
    - Column U: Address Link
    - Column V: CAPTCHA Status
    
    5. RETURN CONFIRMATION:
    - Provide path to generated Excel file
    - Confirm number of records written
    - Report any errors or warnings
    
    DELIVERABLE: Excel file generated from JSON data using ATTOM Foreclosure Template V6.7 with all fields properly mapped.
    """,
    expected_output="""
    Excel file generation confirmation:
    - Output file: output/foreclosures_WA_King_01-01-2026_to_01-31-2026.xlsx
    - Records written: X records
    - Template used: docs/ATTOM Foreclosure Template V6.7.xls
    - All fields mapped correctly to ATTOM template columns
    - File ready for submission
    """,
    agent=auditor,
    context=[mapping_task]
)