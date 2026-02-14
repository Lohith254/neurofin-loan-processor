#!/usr/bin/env python3
"""
Generate sample bank statement PDFs for demo purposes.
Creates 3 PDFs with different risk profiles:
  1. Healthy account (APPROVE)
  2. Risky account (REJECT)
  3. Borderline account (REVIEW)
"""

import os
import sys

# Try reportlab first, fall back to fpdf2
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    USE_REPORTLAB = True
except ImportError:
    USE_REPORTLAB = False

try:
    from fpdf import FPDF
    USE_FPDF = True
except ImportError:
    USE_FPDF = False


def generate_with_fpdf(output_dir: str):
    """Generate sample PDFs using fpdf2."""

    samples = [
        {
            "filename": "icici_statement_healthy.pdf",
            "bank": "ICICI Bank",
            "holder": "PRIYA SHARMA",
            "account": "XXXX XXXX 5678",
            "branch": "Indiranagar, Bengaluru",
            "period_start": "01-Aug-2025",
            "period_end": "31-Jan-2026",
            "opening": 125000.00,
            "closing": 185000.00,
            "total_credits": 780000.00,
            "total_debits": 720000.00,
            "transactions": [
                ("05-Aug-25", "NEFT-Salary Credit-TechCorp India", "", "130000.00", "255000.00"),
                ("08-Aug-25", "UPI-Rent Payment-Landlord", "35000.00", "", "220000.00"),
                ("12-Aug-25", "UPI-BigBasket-Groceries", "4500.00", "", "215500.00"),
                ("15-Aug-25", "NEFT-Freelance Payment", "", "25000.00", "240500.00"),
                ("20-Aug-25", "ECS-LIC Premium", "12000.00", "", "228500.00"),
                ("25-Aug-25", "UPI-Amazon-Shopping", "8500.00", "", "220000.00"),
                ("05-Sep-25", "NEFT-Salary Credit-TechCorp India", "", "130000.00", "350000.00"),
                ("08-Sep-25", "UPI-Rent Payment-Landlord", "35000.00", "", "315000.00"),
                ("10-Sep-25", "IMPS-Mutual Fund SIP", "15000.00", "", "300000.00"),
                ("15-Sep-25", "UPI-Swiggy-Food", "2200.00", "", "297800.00"),
                ("18-Sep-25", "ATM Withdrawal", "10000.00", "", "287800.00"),
                ("22-Sep-25", "ECS-Car EMI", "18500.00", "", "269300.00"),
                ("05-Oct-25", "NEFT-Salary Credit-TechCorp India", "", "130000.00", "399300.00"),
                ("08-Oct-25", "UPI-Rent Payment-Landlord", "35000.00", "", "364300.00"),
                ("10-Oct-25", "IMPS-Mutual Fund SIP", "15000.00", "", "349300.00"),
                ("15-Oct-25", "UPI-Flipkart-Electronics", "22000.00", "", "327300.00"),
                ("20-Oct-25", "ECS-LIC Premium", "12000.00", "", "315300.00"),
                ("05-Nov-25", "NEFT-Salary Credit-TechCorp India", "", "130000.00", "445300.00"),
                ("08-Nov-25", "UPI-Rent Payment-Landlord", "35000.00", "", "410300.00"),
                ("12-Nov-25", "UPI-Electricity Bill", "3200.00", "", "407100.00"),
                ("18-Nov-25", "ECS-Car EMI", "18500.00", "", "388600.00"),
                ("22-Nov-25", "NEFT-Bonus Credit-TechCorp", "", "50000.00", "438600.00"),
                ("05-Dec-25", "NEFT-Salary Credit-TechCorp India", "", "130000.00", "568600.00"),
                ("08-Dec-25", "UPI-Rent Payment-Landlord", "35000.00", "", "533600.00"),
                ("10-Dec-25", "IMPS-Mutual Fund SIP", "15000.00", "", "518600.00"),
                ("15-Dec-25", "UPI-Shopping-Various", "28000.00", "", "490600.00"),
                ("20-Dec-25", "ECS-LIC Premium", "12000.00", "", "478600.00"),
                ("05-Jan-26", "NEFT-Salary Credit-TechCorp India", "", "130000.00", "608600.00"),
                ("08-Jan-26", "UPI-Rent Payment-Landlord", "35000.00", "", "573600.00"),
                ("10-Jan-26", "IMPS-Mutual Fund SIP", "15000.00", "", "558600.00"),
                ("15-Jan-26", "UPI-Travel Booking", "45000.00", "", "513600.00"),
                ("31-Jan-26", "Interest Credit", "", "5000.00", "185000.00"),
            ],
        },
        {
            "filename": "sbi_statement_risky.pdf",
            "bank": "State Bank of India",
            "holder": "RAJESH KUMAR GUPTA",
            "account": "XXXX XXXX 9012",
            "branch": "MG Road, Mumbai",
            "period_start": "01-Oct-2025",
            "period_end": "31-Jan-2026",
            "opening": 8500.00,
            "closing": 2100.00,
            "total_credits": 195000.00,
            "total_debits": 201400.00,
            "transactions": [
                ("03-Oct-25", "UPI-Cash Deposit", "", "15000.00", "23500.00"),
                ("05-Oct-25", "ATM Withdrawal", "10000.00", "", "13500.00"),
                ("08-Oct-25", "ECS-Bounce-HDFC EMI-Insufficient Funds", "0.00", "", "13500.00"),
                ("10-Oct-25", "UPI-Cash Deposit", "", "20000.00", "33500.00"),
                ("12-Oct-25", "ECS-HDFC EMI Retry", "15000.00", "", "18500.00"),
                ("15-Oct-25", "ATM Withdrawal", "8000.00", "", "10500.00"),
                ("20-Oct-25", "UPI-Online Gambling-BetWay", "5000.00", "", "5500.00"),
                ("25-Oct-25", "NEFT-Cash Credit from Unknown", "", "50000.00", "55500.00"),
                ("28-Oct-25", "UPI-Transfer to Multiple Accounts", "45000.00", "", "10500.00"),
                ("02-Nov-25", "UPI-Cash Deposit", "", "12000.00", "22500.00"),
                ("05-Nov-25", "ATM Withdrawal", "8000.00", "", "14500.00"),
                ("08-Nov-25", "ECS-Bounce-SBI Card-Return Unpaid", "0.00", "", "14500.00"),
                ("10-Nov-25", "UPI-Cash Deposit", "", "25000.00", "39500.00"),
                ("12-Nov-25", "NEFT-Transfer Out", "30000.00", "", "9500.00"),
                ("15-Nov-25", "UPI-Online Gambling-Dream11", "3000.00", "", "6500.00"),
                ("18-Nov-25", "NEFT-Cash Credit from Unknown", "", "35000.00", "41500.00"),
                ("22-Nov-25", "ATM Withdrawal", "15000.00", "", "26500.00"),
                ("25-Nov-25", "UPI-Transfer to Multiple Accounts", "20000.00", "", "6500.00"),
                ("01-Dec-25", "UPI-Cash Deposit", "", "18000.00", "24500.00"),
                ("05-Dec-25", "ATM Withdrawal", "12000.00", "", "12500.00"),
                ("08-Dec-25", "ECS-Bounce-Bajaj Finance-Dishonour", "0.00", "", "12500.00"),
                ("12-Dec-25", "UPI-Cash Deposit", "", "10000.00", "22500.00"),
                ("15-Dec-25", "UPI-Online Gambling-BetWay", "8000.00", "", "14500.00"),
                ("20-Dec-25", "NEFT-Transfer Out", "10000.00", "", "4500.00"),
                ("28-Dec-25", "UPI-Cash Deposit", "", "10000.00", "14500.00"),
                ("02-Jan-26", "ATM Withdrawal", "5000.00", "", "9500.00"),
                ("05-Jan-26", "UPI-Transfer Out", "7400.00", "", "2100.00"),
            ],
        },
        {
            "filename": "axis_statement_borderline.pdf",
            "bank": "Axis Bank",
            "holder": "ANITA DESAI",
            "account": "XXXX XXXX 3456",
            "branch": "Koregaon Park, Pune",
            "period_start": "01-Sep-2025",
            "period_end": "31-Jan-2026",
            "opening": 45000.00,
            "closing": 38000.00,
            "total_credits": 425000.00,
            "total_debits": 432000.00,
            "transactions": [
                ("05-Sep-25", "NEFT-Salary Credit-StartupXYZ", "", "75000.00", "120000.00"),
                ("08-Sep-25", "UPI-Rent Payment", "22000.00", "", "98000.00"),
                ("10-Sep-25", "ECS-Home Loan EMI", "28000.00", "", "70000.00"),
                ("15-Sep-25", "UPI-Groceries-DMart", "6500.00", "", "63500.00"),
                ("20-Sep-25", "UPI-Shopping-Myntra", "12000.00", "", "51500.00"),
                ("25-Sep-25", "ATM Withdrawal", "10000.00", "", "41500.00"),
                ("05-Oct-25", "NEFT-Salary Credit-StartupXYZ", "", "75000.00", "116500.00"),
                ("08-Oct-25", "UPI-Rent Payment", "22000.00", "", "94500.00"),
                ("10-Oct-25", "ECS-Home Loan EMI", "28000.00", "", "66500.00"),
                ("12-Oct-25", "IMPS-Medical Emergency", "35000.00", "", "31500.00"),
                ("14-Oct-25", "ECS-Bounce-Credit Card-Insufficient Funds", "0.00", "", "31500.00"),
                ("15-Oct-25", "NEFT-Freelance Income", "", "15000.00", "46500.00"),
                ("20-Oct-25", "UPI-Utility Bills", "8500.00", "", "38000.00"),
                ("25-Oct-25", "ATM Withdrawal", "5000.00", "", "33000.00"),
                ("05-Nov-25", "NEFT-Salary Credit-StartupXYZ", "", "75000.00", "108000.00"),
                ("08-Nov-25", "UPI-Rent Payment", "22000.00", "", "86000.00"),
                ("10-Nov-25", "ECS-Home Loan EMI", "28000.00", "", "58000.00"),
                ("12-Nov-25", "UPI-Insurance Premium", "15000.00", "", "43000.00"),
                ("18-Nov-25", "NEFT-Freelance Income", "", "20000.00", "63000.00"),
                ("22-Nov-25", "UPI-Shopping-Various", "18000.00", "", "45000.00"),
                ("05-Dec-25", "NEFT-Salary Credit-StartupXYZ", "", "75000.00", "120000.00"),
                ("08-Dec-25", "UPI-Rent Payment", "22000.00", "", "98000.00"),
                ("10-Dec-25", "ECS-Home Loan EMI", "28000.00", "", "70000.00"),
                ("15-Dec-25", "NEFT-Freelance Income", "", "10000.00", "80000.00"),
                ("20-Dec-25", "UPI-Year End Shopping", "42000.00", "", "38000.00"),
                ("25-Dec-25", "ATM Withdrawal", "15000.00", "", "23000.00"),
                ("05-Jan-26", "NEFT-Salary Credit-StartupXYZ", "", "80000.00", "103000.00"),
                ("08-Jan-26", "UPI-Rent Payment", "22000.00", "", "81000.00"),
                ("10-Jan-26", "ECS-Home Loan EMI", "28000.00", "", "53000.00"),
                ("15-Jan-26", "UPI-Utility Bills", "8000.00", "", "45000.00"),
                ("20-Jan-26", "UPI-Travel-MakeMyTrip", "7000.00", "", "38000.00"),
            ],
        },
    ]

    for sample in samples:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, sample["bank"], ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "Statement of Account", ln=True, align="C")
        pdf.ln(5)

        # Account info
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"Account Holder: {sample['holder']}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Account Number: {sample['account']}", ln=True)
        pdf.cell(0, 6, f"Branch: {sample['branch']}", ln=True)
        pdf.cell(0, 6, f"Account Type: Savings", ln=True)
        pdf.cell(0, 6, f"Statement Period: {sample['period_start']} to {sample['period_end']}", ln=True)
        pdf.ln(3)

        # Summary
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Account Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Opening Balance: INR {sample['opening']:,.2f}", ln=True)
        pdf.cell(0, 6, f"Closing Balance: INR {sample['closing']:,.2f}", ln=True)
        pdf.cell(0, 6, f"Total Credits: INR {sample['total_credits']:,.2f}", ln=True)
        pdf.cell(0, 6, f"Total Debits: INR {sample['total_debits']:,.2f}", ln=True)
        pdf.ln(5)

        # Transaction table header
        pdf.set_font("Helvetica", "B", 9)
        col_widths = [22, 75, 25, 25, 28]
        headers = ["Date", "Description", "Debit", "Credit", "Balance"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 7, header, border=1, align="C")
        pdf.ln()

        # Transaction rows
        pdf.set_font("Helvetica", "", 8)
        for txn in sample["transactions"]:
            date, desc, debit, credit, balance = txn
            # Truncate description to fit
            if len(desc) > 40:
                desc = desc[:37] + "..."
            pdf.cell(col_widths[0], 6, date, border=1)
            pdf.cell(col_widths[1], 6, desc, border=1)
            pdf.cell(col_widths[2], 6, debit, border=1, align="R")
            pdf.cell(col_widths[3], 6, credit, border=1, align="R")
            pdf.cell(col_widths[4], 6, balance, border=1, align="R")
            pdf.ln()

        # Footer
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, "This is a computer-generated statement and does not require a signature.", ln=True, align="C")
        pdf.cell(0, 5, f"Generated for demo purposes - {sample['bank']}", ln=True, align="C")

        filepath = os.path.join(output_dir, sample["filename"])
        pdf.output(filepath)
        print(f"  Generated: {filepath}")

    return [s["filename"] for s in samples]


def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "data", "sample_statements")
    os.makedirs(output_dir, exist_ok=True)

    print("Generating sample bank statement PDFs...")
    print(f"Output directory: {output_dir}")

    if USE_FPDF:
        files = generate_with_fpdf(output_dir)
    elif USE_REPORTLAB:
        print("Using reportlab (install fpdf2 for lighter dependency: pip install fpdf2)")
        # Could implement reportlab version here
        sys.exit(1)
    else:
        print("Error: No PDF generation library found.")
        print("Install fpdf2: pip install fpdf2")
        sys.exit(1)

    print(f"\nGenerated {len(files)} sample PDFs:")
    print("  1. icici_statement_healthy.pdf  -> Expected: APPROVE (strong financials)")
    print("  2. sbi_statement_risky.pdf      -> Expected: REJECT  (bounced checks, gambling)")
    print("  3. axis_statement_borderline.pdf -> Expected: REVIEW  (mixed signals)")


if __name__ == "__main__":
    main()
