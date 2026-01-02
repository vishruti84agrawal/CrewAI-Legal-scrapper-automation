import os
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 1. DISABLE TELEMETRY (Fixes the connection error at the bottom of your logs)
os.environ["OTEL_SDK_DISABLED"] = "true"
# Set your API Key BEFORE importing agents

# Get free API key from: https://console.groq.com
from crewai import Crew, Process, Task
from agents import navigator, data_mapper, auditor
import tasks

def generate_date_ranges():
    """Generate 2 date ranges: previous month and next month from current date."""
    # Current date
    current_date = datetime.now()
    
    # Scenario 1: Previous 1 month to current date
    # Example: Dec 1, 2025 - Jan 1, 2026
    start_date_scenario1 = current_date - relativedelta(months=1)
    end_date_scenario1 = current_date
    
    # Scenario 2: Current date to next 1 month
    # Example: Jan 1, 2026 - Jan 31, 2026 (or Feb 1, 2026)
    start_date_scenario2 = current_date
    end_date_scenario2 = current_date + relativedelta(months=1)
    
    # Format as MM/DD/YYYY
    scenario1 = (
        start_date_scenario1.strftime("%m/%d/%Y"),
        end_date_scenario1.strftime("%m/%d/%Y")
    )
    scenario2 = (
        start_date_scenario2.strftime("%m/%d/%Y"),
        end_date_scenario2.strftime("%m/%d/%Y")
    )
    
    return [scenario1, scenario2]

def run_poc():
    """Run the foreclosure data extraction for 2 scenarios: previous month and next month."""
    
    # Generate 2 date ranges: previous month and next month from current date
    date_ranges = generate_date_ranges()
    
    print("="*80)
    print("### Starting Agentic Data Collection POC ###")
    print(f"\n📅 DATE RANGES GENERATED:")
    print(f"   Range 1 (Previous Month): {date_ranges[0][0]} to {date_ranges[0][1]}")
    print(f"   Range 2 (Next Month):     {date_ranges[1][0]} to {date_ranges[1][1]}")
    print("="*80)
    
    successful_ranges = []
    failed_ranges = []
    
    for idx, (start_date, end_date) in enumerate(date_ranges, 1):
        print(f"\n{'='*80}")
        print(f"### PROCESSING DATE RANGE {idx} of {len(date_ranges)} ###")
        print(f"### Start Date: {start_date} | End Date: {end_date} ###")
        print(f"{'='*80}\n")
        
        try:
            # Create unique filenames for this date range
            date_suffix = f"{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}"
            html_file = f"search_results_{date_suffix}.html"
            json_file = f"json_results/foreclosures_WA_King_{date_suffix}.json"
            excel_file = f"output/foreclosures_WA_King_{date_suffix}.xlsx"
            
            # Create FRESH task instances for this date range
            extraction_task_copy = Task(
                description=tasks.extraction_task.description.replace(
                    "01/01/2026", start_date
                ).replace(
                    "01/31/2026", end_date
                ).replace(
                    "search_results_debug.html", html_file
                ),
                expected_output=tasks.extraction_task.expected_output,
                agent=navigator
            )
            
            mapping_task_copy = Task(
                description=tasks.mapping_task.description.replace(
                    "01/01/2026", start_date
                ).replace(
                    "01/31/2026", end_date
                ).replace(
                    "search_results_debug.html", html_file
                ).replace(
                    "json_results/foreclosures_WA_King_01-01-2026_to_01-31-2026.json",
                    json_file
                ),
                expected_output=tasks.mapping_task.expected_output,
                agent=data_mapper,
                context=[extraction_task_copy]
            )
            
            # Use unique Excel file for this date range
            excel_task_copy = Task(
                description=tasks.excel_generation_task.description.replace(
                    "json_results/foreclosures_WA_King_01-01-2026_to_01-31-2026.json",
                    json_file
                ).replace(
                    "output/foreclosures_WA_King_01-01-2026_to_01-31-2026.xlsx",
                    excel_file
                ),
                expected_output=tasks.excel_generation_task.expected_output,
                agent=auditor,
                context=[mapping_task_copy]
            )
            
            # Create crew for this date range with fresh task instances
            crew = Crew(
                agents=[navigator, data_mapper, auditor],
                tasks=[extraction_task_copy, mapping_task_copy, excel_task_copy],
                process=Process.sequential
            )
            
            result = crew.kickoff()
            
            print(f"\n{'='*80}")
            print(f"### ✅ COMPLETED DATE RANGE {idx}: {start_date} to {end_date} ###")
            print(f"{'='*80}\n")
            print(result)
            
            successful_ranges.append(f"Range {idx}: {start_date} to {end_date}")
            
            # Add delay between date ranges to avoid rate limits
            if idx < len(date_ranges):
                print(f"\n### Waiting 3 seconds before processing next date range... ###\n")
                time.sleep(3)
            
        except Exception as e:
            print(f"\n### ❌ ERROR PROCESSING DATE RANGE {idx} ({start_date} to {end_date}) ###")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response}")
            if hasattr(e, 'body'):
                print(f"Body: {e.body}")
            import traceback
            traceback.print_exc()
            
            failed_ranges.append(f"Range {idx}: {start_date} to {end_date} - {type(e).__name__}: {str(e)[:100]}")
            print(f"\n⚠️ Continuing to next date range...\n")
            continue
    
    print(f"\n{'='*80}")
    print(f"### PROCESSING COMPLETE ###")
    print(f"{'='*80}")
    print(f"\n✅ Successful: {len(successful_ranges)}/{len(date_ranges)}")
    for success in successful_ranges:
        print(f"   ✓ {success}")
    
    if failed_ranges:
        print(f"\n❌ Failed: {len(failed_ranges)}/{len(date_ranges)}")
        for failure in failed_ranges:
            print(f"   ✗ {failure}")
    
    print(f"\n{'='*80}")
    print(f"### ALL {len(date_ranges)} DATE RANGES PROCESSED ###")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    run_poc()