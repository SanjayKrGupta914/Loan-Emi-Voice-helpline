"""
Seed script for SteadyHome Loan EMI Voice Helpline
Generates 25+ rich fictional customer and loan records covering all boundary conditions,
status states, payment modes, and test scenarios.
Simulated Clock Reference: 2026-11-10 09:00:00
"""

import sys
import os
from datetime import datetime, date

# Ensure database package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.schema import Base, Borrower, Loan, EMI, Payment, Escalation, InteractionLog, get_engine, sessionmaker

def seed_database(db_path=None):
    engine = get_engine(db_path)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # 25+ Fictional Borrowers
    # Scenarios:
    # 1. SH-BOR-1001: Rajesh Sharma (Standard Active, Loan Active, Due 2026-11-15, AutoDebit)
    # 2. SH-BOR-1002: Priya Venkat (BLOCKED status -> Triggers human agent transfer on verification)
    # 3. SH-BOR-1003: Amit Patel (Active, Overdue 3 days [2026-11-07] -> 2% late fee)
    # 4. SH-BOR-1004: Sunita Rao (Active, Overdue exactly 5 days [2026-11-05] -> exactly 2% boundary)
    # 5. SH-BOR-1005: Vikram Malhotra (Active, Overdue 15 days [2026-10-26] -> 4% late fee)
    # 6. SH-BOR-1006: Neha Kulkarni (Active, Overdue exactly 30 days [2026-10-11] -> exactly 4% boundary)
    # 7. SH-BOR-1007: Rohan Gupta (Active, Overdue 35 days [2026-10-06] -> >30 days, human escalation required)
    # 8. SH-BOR-1008: Ananya Iyer (Active, CLOSED loan -> part payment triggers human escalation)
    # 9. SH-BOR-1009: Deepak Verma (Active, DEFAULT loan -> part payment triggers human escalation)
    # 10. SH-BOR-1010: Kavita Nair (Active, UNKNOWN loan status -> technical error + human escalation)
    # 11. SH-BOR-1011: Suresh Menon (Active, Already Paid EMI -> 0 late fee)
    # 12. SH-BOR-1012: Pooja Joshi (Active, Branch Cash Desk payment on 2026-12-31 -> Supported)
    # 13. SH-BOR-1013: Manish Pandey (Active, Branch Cash Desk payment on 2027-01-01 -> Unsupported, Human escalation)
    # 14. SH-BOR-1014: Divya Chawla (Active, NetPay payment on 2026-11-20 -> NetPay supported)
    # 15. SH-BOR-1015: Arvind Swaminathan (Active, NetPay payment on 2027-01-10 -> NetPay Plus supported)
    # 16. SH-BOR-1016: Sneha Kapoor (Active, KiteWallet payment mode -> Discontinued, Human escalation)
    # 17. SH-BOR-1017: Tarun Saxena (Active, Part-payment ₹500 exact boundary -> Accepted)
    # 18. SH-BOR-1018: Meera Nambiar (Active, Part-payment ₹499 boundary -> Rejected)
    # 19. SH-BOR-1019: Harish Reddy (Active, Multiple active loans)
    # 20. SH-BOR-1020: Shruti Sen (Active, Zero days overdue, due today 2026-11-10 -> 0% fee)
    # 21. SH-BOR-1021: Nitin Deshmukh (Active, High EMI home loan ₹85,000)
    # 22. SH-BOR-1022: Ritu Bhatia (Active, Affordable housing loan ₹12,500 EMI)
    # 23. SH-BOR-1023: Alok Chatterjee (Active, Senior citizen borrower, DOB 1958)
    # 24. SH-BOR-1024: Farah Khan (Active, Joint borrower loan)
    # 25. SH-BOR-1025: Karthik Subramanian (Active, Advance prepaid EMI)

    borrowers_data = [
        ("SH-BOR-1001", "Rajesh Sharma", "1985-06-15", "+91-9820011001", "rajesh.sharma@example.com", "ACTIVE", "Flat 402, Lotus Heights, Andheri West, Mumbai, MH"),
        ("SH-BOR-1002", "Priya Venkat", "1990-03-22", "+91-9820011002", "priya.venkat@example.com", "BLOCKED", "Plot 14, Defence Colony, Indiranagar, Bengaluru, KA"),
        ("SH-BOR-1003", "Amit Patel", "1982-11-04", "+91-9820011003", "amit.patel@example.com", "ACTIVE", "B-12, Shanti Niketan, Navrangpura, Ahmedabad, GJ"),
        ("SH-BOR-1004", "Sunita Rao", "1987-09-18", "+91-9820011004", "sunita.rao@example.com", "ACTIVE", "Flat 101, Green Meadows, Banjara Hills, Hyderabad, TS"),
        ("SH-BOR-1005", "Vikram Malhotra", "1979-01-30", "+91-9820011005", "vikram.m@example.com", "ACTIVE", "C-88, South Extension Part II, New Delhi, DL"),
        ("SH-BOR-1006", "Neha Kulkarni", "1992-07-12", "+91-9820011006", "neha.k@example.com", "ACTIVE", "15, Mayur Colony, Kothrud, Pune, MH"),
        ("SH-BOR-1007", "Rohan Gupta", "1984-04-25", "+91-9820011007", "rohan.gupta@example.com", "ACTIVE", "House 24, Sector 15, Noida, UP"),
        ("SH-BOR-1008", "Ananya Iyer", "1989-12-08", "+91-9820011008", "ananya.iyer@example.com", "ACTIVE", "A-304, Palm Grove, Adyar, Chennai, TN"),
        ("SH-BOR-1009", "Deepak Verma", "1978-08-14", "+91-9820011009", "deepak.verma@example.com", "ACTIVE", "72, Civil Lines, Jaipur, RJ"),
        ("SH-BOR-1010", "Kavita Nair", "1991-05-19", "+91-9820011010", "kavita.nair@example.com", "ACTIVE", "Villa 9, Marine Drive, Kochi, KL"),
        ("SH-BOR-1011", "Suresh Menon", "1983-02-10", "+91-9820011011", "suresh.menon@example.com", "ACTIVE", "Flat 502, Lakeview Apartments, Thane West, MH"),
        ("SH-BOR-1012", "Pooja Joshi", "1986-10-05", "+91-9820011012", "pooja.joshi@example.com", "ACTIVE", "Flat 204, Silver Arch, Viman Nagar, Pune, MH"),
        ("SH-BOR-1013", "Manish Pandey", "1980-08-28", "+91-9820011013", "manish.p@example.com", "ACTIVE", "102, Gomti Nagar, Lucknow, UP"),
        ("SH-BOR-1014", "Divya Chawla", "1993-04-16", "+91-9820011014", "divya.chawla@example.com", "ACTIVE", "D-45, Rajouri Garden, New Delhi, DL"),
        ("SH-BOR-1015", "Arvind Swaminathan", "1975-09-03", "+91-9820011015", "arvind.s@example.com", "ACTIVE", "42, Anna Nagar West, Chennai, TN"),
        ("SH-BOR-1016", "Sneha Kapoor", "1994-01-21", "+91-9820011016", "sneha.kapoor@example.com", "ACTIVE", "Flat 801, Sky High Towers, Gurugram, HR"),
        ("SH-BOR-1017", "Tarun Saxena", "1988-11-11", "+91-9820011017", "tarun.saxena@example.com", "ACTIVE", "56, Alkapuri, Vadodara, GJ"),
        ("SH-BOR-1018", "Meera Nambiar", "1981-03-14", "+91-9820011018", "meera.nambiar@example.com", "ACTIVE", "K-12, Panampilly Nagar, Ernakulam, KL"),
        ("SH-BOR-1019", "Harish Reddy", "1985-07-29", "+91-9820011019", "harish.reddy@example.com", "ACTIVE", "Plot 54, Jubilee Hills, Hyderabad, TS"),
        ("SH-BOR-1020", "Shruti Sen", "1990-10-10", "+91-9820011020", "shruti.sen@example.com", "ACTIVE", "Flat 3A, Salt Lake Sector 2, Kolkata, WB"),
        ("SH-BOR-1021", "Nitin Deshmukh", "1976-12-05", "+91-9820011021", "nitin.d@example.com", "ACTIVE", "84, Shivaji Park, Dadar, Mumbai, MH"),
        ("SH-BOR-1022", "Ritu Bhatia", "1995-02-17", "+91-9820011022", "ritu.bhatia@example.com", "ACTIVE", "Sector 21, Chandigarh, CH"),
        ("SH-BOR-1023", "Alok Chatterjee", "1958-04-12", "+91-9820011023", "alok.c@example.com", "ACTIVE", "18/2, Ballygunge Circular Rd, Kolkata, WB"),
        ("SH-BOR-1024", "Farah Khan", "1987-08-20", "+91-9820011024", "farah.khan@example.com", "ACTIVE", "Flat 12, Bandra Hill Road, Mumbai, MH"),
        ("SH-BOR-1025", "Karthik Subramanian", "1991-11-25", "+91-9820011025", "karthik.sub@example.com", "ACTIVE", "77, Besant Nagar, Chennai, TN"),
    ]

    for b in borrowers_data:
        borrower = Borrower(
            borrower_id=b[0],
            name=b[1],
            date_of_birth=b[2],
            phone=b[3],
            email=b[4],
            status=b[5],
            address=b[6],
            created_at="2025-01-10T10:00:00"
        )
        session.add(borrower)

    # 25+ Loans
    # Loan IDs correspond to borrowers, with last 4 digits easily identifiable
    # E.g. SH-LN-1001 has last four digits '1001'
    loans_data = [
        # (loan_id, borrower_id, loan_amount, status, tenure, interest, emi, next_due, sanction)
        ("SH-LN-1001", "SH-BOR-1001", 4500000.0, "ACTIVE", 240, 8.50, 39052.0, "2026-11-15", "2023-01-15"),
        ("SH-LN-1002", "SH-BOR-1002", 3200000.0, "ACTIVE", 180, 8.75, 32014.0, "2026-11-20", "2023-05-10"),
        ("SH-LN-1003", "SH-BOR-1003", 5500000.0, "ACTIVE", 240, 8.40, 47368.0, "2026-11-07", "2022-08-20"), # Overdue 3 days
        ("SH-LN-1004", "SH-BOR-1004", 2800000.0, "ACTIVE", 180, 8.65, 27815.0, "2026-11-05", "2023-09-05"), # Overdue exactly 5 days
        ("SH-LN-1005", "SH-BOR-1005", 6000000.0, "ACTIVE", 240, 8.50, 52070.0, "2026-10-26", "2022-04-12"), # Overdue 15 days
        ("SH-LN-1006", "SH-BOR-1006", 4000000.0, "ACTIVE", 240, 8.50, 34713.0, "2026-10-11", "2023-02-18"), # Overdue exactly 30 days
        ("SH-LN-1007", "SH-BOR-1007", 5000000.0, "ACTIVE", 240, 8.60, 43708.0, "2026-10-06", "2022-11-30"), # Overdue 35 days (>30)
        ("SH-LN-1008", "SH-BOR-1008", 2500000.0, "CLOSED", 120, 8.50, 31000.0, "2026-05-15", "2021-05-15"), # Closed loan
        ("SH-LN-1009", "SH-BOR-1009", 4800000.0, "DEFAULT", 240, 9.25, 43980.0, "2026-08-10", "2020-08-10"), # Defaulted loan
        ("SH-LN-1010", "SH-BOR-1010", 3500000.0, "UNKNOWN", 180, 8.50, 34466.0, "2026-11-18", "2023-11-18"), # Unknown loan status
        ("SH-LN-1011", "SH-BOR-1011", 3800000.0, "ACTIVE", 240, 8.50, 32978.0, "2026-10-10", "2023-03-10"), # Paid EMI
        ("SH-LN-1012", "SH-BOR-1012", 4200000.0, "ACTIVE", 240, 8.50, 36449.0, "2026-12-31", "2023-06-15"), # Cash desk supported
        ("SH-LN-1013", "SH-BOR-1013", 5100000.0, "ACTIVE", 240, 8.55, 44430.0, "2027-01-01", "2023-07-20"), # Cash desk unsupported
        ("SH-LN-1014", "SH-BOR-1014", 3000000.0, "ACTIVE", 180, 8.50, 29542.0, "2026-11-20", "2023-04-10"), # NetPay
        ("SH-LN-1015", "SH-BOR-1015", 4600000.0, "ACTIVE", 240, 8.50, 39920.0, "2027-01-10", "2023-08-15"), # NetPay Plus
        ("SH-LN-1016", "SH-BOR-1016", 3600000.0, "ACTIVE", 180, 8.50, 35451.0, "2026-11-25", "2023-09-12"), # KiteWallet (unsupported)
        ("SH-LN-1017", "SH-BOR-1017", 4000000.0, "ACTIVE", 240, 8.50, 34713.0, "2026-11-15", "2023-01-20"), # Part-pay ₹500
        ("SH-LN-1018", "SH-BOR-1018", 4000000.0, "ACTIVE", 240, 8.50, 34713.0, "2026-11-15", "2023-01-20"), # Part-pay ₹499
        ("SH-LN-1019", "SH-BOR-1019", 6500000.0, "ACTIVE", 240, 8.35, 55800.0, "2026-11-12", "2022-03-10"),
        ("SH-LN-1020", "SH-BOR-1020", 3500000.0, "ACTIVE", 180, 8.50, 34466.0, "2026-11-10", "2023-11-10"), # Due today
        ("SH-LN-1021", "SH-BOR-1021", 9500000.0, "ACTIVE", 240, 8.25, 81000.0, "2026-11-14", "2022-01-10"),
        ("SH-LN-1022", "SH-BOR-1022", 1500000.0, "ACTIVE", 180, 8.90, 15124.0, "2026-11-16", "2024-02-15"),
        ("SH-LN-1023", "SH-BOR-1023", 2200000.0, "ACTIVE", 120, 8.60, 27400.0, "2026-11-08", "2021-08-10"),
        ("SH-LN-1024", "SH-BOR-1024", 5200000.0, "ACTIVE", 240, 8.50, 45127.0, "2026-11-22", "2023-10-05"),
        ("SH-LN-1025", "SH-BOR-1025", 4800000.0, "ACTIVE", 240, 8.45, 41512.0, "2026-11-28", "2023-11-28"),
    ]

    for l in loans_data:
        loan = Loan(
            loan_id=l[0],
            borrower_id=l[1],
            loan_amount=l[2],
            loan_status=l[3],
            loan_tenure_months=l[4],
            interest_rate=l[5],
            emi_amount=l[6],
            next_due_date=l[7],
            sanction_date=l[8]
        )
        session.add(loan)

    # 25+ EMIs with accurate overdue and late fee calculated against 2026-11-10
    # Overdue rules:
    # 0 days: 0%
    # 1-5 days: 2%
    # 6-30 days: 4%
    # >30 days: online blocked, escalate
    # Paid: 0%
    emis_data = [
        # (emi_id, loan_id, borrower_id, amount, due_date, status, mode, days_overdue, late_fee, paid_date)
        ("EMI-1001", "SH-LN-1001", "SH-BOR-1001", 39052.0, "2026-11-15", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1002", "SH-LN-1002", "SH-BOR-1002", 32014.0, "2026-11-20", "PENDING", "NetPay", 0, 0.0, None),
        ("EMI-1003", "SH-LN-1003", "SH-BOR-1003", 47368.0, "2026-11-07", "OVERDUE", "NetPay", 3, round(47368.0 * 0.02), None), # 3 days -> 2% = 947
        ("EMI-1004", "SH-LN-1004", "SH-BOR-1004", 27815.0, "2026-11-05", "OVERDUE", "AutoDebit", 5, round(27815.0 * 0.02), None), # 5 days exact -> 2% = 556
        ("EMI-1005", "SH-LN-1005", "SH-BOR-1005", 52070.0, "2026-10-26", "OVERDUE", "AutoDebit", 15, round(52070.0 * 0.04), None), # 15 days -> 4% = 2083
        ("EMI-1006", "SH-LN-1006", "SH-BOR-1006", 34713.0, "2026-10-11", "OVERDUE", "Branch Cash Desk", 30, round(34713.0 * 0.04), None), # 30 days exact -> 4% = 1389
        ("EMI-1007", "SH-LN-1007", "SH-BOR-1007", 43708.0, "2026-10-06", "OVERDUE", "AutoDebit", 35, 0.0, None), # 35 days (>30) -> No online processing
        ("EMI-1008", "SH-LN-1008", "SH-BOR-1008", 31000.0, "2026-05-15", "PAID", "NetPay", 0, 0.0, "2026-05-14"),
        ("EMI-1009", "SH-LN-1009", "SH-BOR-1009", 43980.0, "2026-08-10", "OVERDUE", "Branch Cash Desk", 92, 0.0, None),
        ("EMI-1010", "SH-LN-1010", "SH-BOR-1010", 34466.0, "2026-11-18", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1011", "SH-LN-1011", "SH-BOR-1011", 32978.0, "2026-10-10", "PAID", "AutoDebit", 0, 0.0, "2026-10-09"), # Already paid
        ("EMI-1012", "SH-LN-1012", "SH-BOR-1012", 36449.0, "2026-12-31", "PENDING", "Branch Cash Desk", 0, 0.0, None), # Valid cash desk
        ("EMI-1013", "SH-LN-1013", "SH-BOR-1013", 44430.0, "2027-01-01", "PENDING", "Branch Cash Desk", 0, 0.0, None), # Invalid cash desk (after 31-12-2026)
        ("EMI-1014", "SH-LN-1014", "SH-BOR-1014", 29542.0, "2026-11-20", "PENDING", "NetPay", 0, 0.0, None), # NetPay
        ("EMI-1015", "SH-LN-1015", "SH-BOR-1015", 39920.0, "2027-01-10", "PENDING", "NetPay", 0, 0.0, None), # NetPay Plus
        ("EMI-1016", "SH-LN-1016", "SH-BOR-1016", 35451.0, "2026-11-25", "PENDING", "KiteWallet", 0, 0.0, None), # KiteWallet
        ("EMI-1017", "SH-LN-1017", "SH-BOR-1017", 34713.0, "2026-11-15", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1018", "SH-LN-1018", "SH-BOR-1018", 34713.0, "2026-11-15", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1019", "SH-LN-1019", "SH-BOR-1019", 55800.0, "2026-11-12", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1020", "SH-LN-1020", "SH-BOR-1020", 34466.0, "2026-11-10", "PENDING", "NetPay", 0, 0.0, None), # Due today (0 days overdue)
        ("EMI-1021", "SH-LN-1021", "SH-BOR-1021", 81000.0, "2026-11-14", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1022", "SH-LN-1022", "SH-BOR-1022", 15124.0, "2026-11-16", "PENDING", "NetPay", 0, 0.0, None),
        ("EMI-1023", "SH-LN-1023", "SH-BOR-1023", 27400.0, "2026-11-08", "OVERDUE", "AutoDebit", 2, round(27400.0 * 0.02), None),
        ("EMI-1024", "SH-LN-1024", "SH-BOR-1024", 45127.0, "2026-11-22", "PENDING", "AutoDebit", 0, 0.0, None),
        ("EMI-1025", "SH-LN-1025", "SH-BOR-1025", 41512.0, "2026-11-28", "PENDING", "AutoDebit", 0, 0.0, None),
    ]

    for e in emis_data:
        emi = EMI(
            emi_id=e[0],
            loan_id=e[1],
            borrower_id=e[2],
            emi_amount=e[3],
            due_date=e[4],
            payment_status=e[5],
            payment_mode=e[6],
            days_overdue=e[7],
            late_fee=e[8],
            paid_date=e[9]
        )
        session.add(emi)

    # 15+ Payments sample history
    payments_data = [
        ("PMT-9001", "EMI-1008", 31000.0, "2026-05-14", "NetPay", "SUCCESS", "TXN872391012", "Regular EMI clearance"),
        ("PMT-9002", "EMI-1011", 32978.0, "2026-10-09", "AutoDebit", "SUCCESS", "TXN918237194", "NACH AutoDebit clearance"),
        ("PMT-9003", "EMI-1001", 39052.0, "2026-10-14", "AutoDebit", "SUCCESS", "TXN827391823", "Previous month clearance"),
        ("PMT-9004", "EMI-1002", 32014.0, "2026-10-19", "NetPay", "SUCCESS", "TXN738291039", "Previous month clearance"),
        ("PMT-9005", "EMI-1003", 47368.0, "2026-10-06", "NetPay", "SUCCESS", "TXN928301928", "Previous month clearance"),
        ("PMT-9006", "EMI-1004", 27815.0, "2026-10-04", "AutoDebit", "SUCCESS", "TXN637281920", "Previous month clearance"),
        ("PMT-9007", "EMI-1005", 52070.0, "2026-09-25", "AutoDebit", "SUCCESS", "TXN839201938", "September clearance"),
        ("PMT-9008", "EMI-1017", 5000.0, "2026-10-20", "NetPay", "SUCCESS", "TXN839210482", "Part-payment towards principal"),
        ("PMT-9009", "EMI-1019", 55800.0, "2026-10-11", "AutoDebit", "SUCCESS", "TXN928371029", "Previous month clearance"),
        ("PMT-9010", "EMI-1020", 34466.0, "2026-10-10", "NetPay", "SUCCESS", "TXN839201984", "Previous month clearance"),
    ]

    for p in payments_data:
        pmt = Payment(
            payment_id=p[0],
            emi_id=p[1],
            amount=p[2],
            payment_date=p[3],
            payment_mode=p[4],
            payment_status=p[5],
            reference_no=p[6],
            notes=p[7]
        )
        session.add(pmt)

    # Escalations (Historical & baseline test cases)
    escalations_data = [
        ("ESC-001", "SH-BOR-1002", "DUE_DATE_ENQUIRY", "Borrower status is BLOCKED in core banking system.", "NetPay", "Caller attempted verification; system flagged account as BLOCKED. Handed off to Senior Fraud and Account Recovery Specialist.", "INITIATED", "2026-11-09T14:32:00"),
        ("ESC-002", "SH-BOR-1007", "LATE_FEE_ENQUIRY", "EMI overdue by 35 days (exceeds 30-day online resolution policy).", "AutoDebit", "Caller requested online payment options for loan overdue by 35 days. Disallowed by policy; handed off to Collections Specialist.", "INITIATED", "2026-11-09T16:45:00"),
        ("ESC-003", "SH-BOR-1009", "PART_PAYMENT", "Loan status is DEFAULT.", "Branch Cash Desk", "Caller attempted ₹10,000 part-payment on a defaulted loan account. Transferred to Legal & Recovery Desk.", "ASSIGNED", "2026-11-08T11:20:00"),
        ("ESC-004", "SH-BOR-1013", "PAYMENT_MODE_DISCONTINUED", "Branch Cash Desk requested for date 2027-01-01 (discontinued post 31-Dec-2026).", "Branch Cash Desk", "Customer requested branch cash desk payment for January 2027. Transferred to Agent for alternate channel advisory.", "RESOLVED", "2026-11-07T10:15:00"),
        ("ESC-005", "SH-BOR-1016", "PAYMENT_MODE_DISCONTINUED", "KiteWallet payment mode requested (permanently discontinued).", "KiteWallet", "Customer requested payment via KiteWallet. Transferred to customer support representative.", "RESOLVED", "2026-11-06T13:40:00"),
    ]

    for esc in escalations_data:
        escalation = Escalation(
            escalation_id=esc[0],
            borrower_id=esc[1],
            intent=esc[2],
            reason=esc[3],
            payment_mode=esc[4],
            conversation_summary=esc[5],
            transfer_status=esc[6],
            timestamp=esc[7]
        )
        session.add(escalation)

    # Initial interaction logs
    logs_data = [
        ("SESS-INIT-01", "SH-BOR-1001", "VERIFICATION", "Root Agent", '{"status": "SUCCESS", "borrower_id": "SH-BOR-1001", "message": "Identity verified successfully"}', "2026-11-09T10:00:00"),
        ("SESS-INIT-01", "SH-BOR-1001", "INTENT_DETECTED", "Root Agent", '{"intent": "DUE_DATE_ENQUIRY", "confidence": 0.98}', "2026-11-09T10:00:15"),
        ("SESS-INIT-01", "SH-BOR-1001", "AGENT_HANDOFF", "Root Agent", '{"from": "Root Agent", "to": "EMI Service Sub-Agent", "intent": "DUE_DATE_ENQUIRY"}', "2026-11-09T10:00:18"),
        ("SESS-INIT-01", "SH-BOR-1001", "TOOL_CALLED", "EMI Service Sub-Agent", '{"tool": "lookup_loan", "borrower_id": "SH-BOR-1001", "result": "SH-LN-1001"}', "2026-11-09T10:00:20"),
    ]

    for log in logs_data:
        entry = InteractionLog(
            session_id=log[0],
            borrower_id=log[1],
            event_type=log[2],
            agent_name=log[3],
            details=log[4],
            timestamp=log[5]
        )
        session.add(entry)

    session.commit()
    session.close()
    print(f"Database seeded successfully with {len(borrowers_data)} borrowers, {len(loans_data)} loans, {len(emis_data)} EMIs, {len(payments_data)} payments, and {len(escalations_data)} escalations.")

if __name__ == "__main__":
    seed_database()

