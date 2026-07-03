"""
ingestion/cleaner.py
--------------------
Strips boilerplate HTML artifacts and structures raw text into clean,
fact-dense paragraphs ready for chunking.
"""
import re

def clean(raw_text: str) -> str:
    # 1. NAV and Date
    nav_match = re.search(r'NAV: (.*?)\n(₹[\d,.]+)', raw_text)
    nav_date = nav_match.group(1).strip() if nav_match else ""
    nav_val = nav_match.group(2).strip() if nav_match else ""
    
    # 2. Min SIP
    sip_match = re.search(r'Min\. for SIP\n(₹[\d,.]+)', raw_text)
    min_sip = sip_match.group(1).strip() if sip_match else ""
    
    # 3. Fund Size
    size_match = re.search(r'Fund size \(AUM\)\n(₹[\d,.]+\s*Cr)', raw_text)
    fund_size = size_match.group(1).strip() if size_match else ""
    
    # 4. Expense Ratio
    exp_match = re.search(r'Expense ratio\n([\d.]+%?)', raw_text)
    expense_ratio = exp_match.group(1).strip() if exp_match else ""
    
    # 5. Exit Load
    exit_match = re.search(r'Exit load\n(.*?)\n', raw_text)
    exit_load = exit_match.group(1).strip() if exit_match else ""
    
    # 6. Fund Manager
    manager_match = re.search(r'([A-Za-z\s]+) is the Current Fund Manager', raw_text)
    fund_manager = manager_match.group(1).strip() if manager_match else ""
    if not fund_manager:
        # Fallback to "Fund management" section
        fm_match = re.search(r'Fund management\n.*?\n(.*?)\n', raw_text)
        fund_manager = fm_match.group(1).strip() if fm_match else ""

    # 7. Investment Objective
    obj_match = re.search(r'Investment Objective\n(.*?)\n', raw_text)
    objective = obj_match.group(1).strip() if obj_match else ""
    
    # 8. Benchmark
    bench_match = re.search(r'Fund benchmark\n(.*?)\n', raw_text)
    benchmark = bench_match.group(1).strip() if bench_match else ""
    
    # 9. Fund name, risk, category from the "About ..." section
    about_match = re.search(r'About (.*?)\n(.*?)\n', raw_text)
    fund_name = about_match.group(1).strip() if about_match else ""
    about_text = about_match.group(2).strip() if about_match else ""
    
    # Fallback to the top lines if About is missing
    if not fund_name:
        lines = raw_text.split("\n")
        for line in lines:
            if "Fund Direct Growth" in line or "Plan Direct Growth" in line:
                fund_name = line.strip()
                break
                
    # Format the cleaned fact-dense paragraph
    cleaned = f"Fund Name: {fund_name}\n"
    if nav_val and nav_date:
        cleaned += f"NAV: {nav_val} (as of {nav_date})\n"
    if expense_ratio:
        cleaned += f"Expense Ratio: {expense_ratio}\n"
    if exit_load:
        cleaned += f"Exit Load: {exit_load}\n"
    if min_sip:
        cleaned += f"Minimum SIP: {min_sip}\n"
    if fund_size:
        cleaned += f"Fund Size (AUM): {fund_size}\n"
    if benchmark:
        cleaned += f"Benchmark Index: {benchmark}\n"
    if fund_manager:
        cleaned += f"Fund Manager: {fund_manager}\n"
    if objective:
        cleaned += f"Investment Objective: {objective}\n"
    if about_text:
        cleaned += f"Overview: {about_text}\n"
        
    return cleaned
