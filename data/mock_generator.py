import json
import random
import datetime

def generate_mock_data():
    """Generate mock GST data (Taxpayers, Invoices, Returns)."""
    
    taxpayers = [
        {"gstin": "27AAAAA0000A1Z5", "legal_name": "ABC Tech Solutions Pvt Ltd", "status": "Active"},
        {"gstin": "29BBBBB0000B1Z6", "legal_name": "XYZ Manufacturing Corp", "status": "Active"},
        {"gstin": "33CCCCC0000C1Z7", "legal_name": "Global Traders Ltd", "status": "Suspended"},
        {"gstin": "19DDDDD0000D1Z8", "legal_name": "Swift Logistics", "status": "Active"},
        {"gstin": "07EEEEE0000E1Z9", "legal_name": "Innovate IT Services", "status": "Active"}
    ]
    
    # Generate Invoices in Books (Purchase Register for 27AAAAA0000A1Z5)
    book_invoices = []
    for i in range(10):
        supplier = random.choice(taxpayers[1:])
        irn = f"irn_book_{i+1:03d}"
        inv_num = f"INV/2026/{i+1:03d}"
        date = f"2026-02-{random.randint(1, 25):02d}"
        taxable_val = random.randint(1000, 50000)
        tax_amount = round(taxable_val * 0.18, 2)
        
        book_invoices.append({
            "irn": irn,
            "inv_num": inv_num,
            "date": date,
            "taxable_val": taxable_val,
            "tax_amount": tax_amount,
            "supplier_gstin": supplier["gstin"],
            "recipient_gstin": "27AAAAA0000A1Z5",
            "source": "Books"
        })
        
    # Generate Invoices in GSTR-2B (Portal Data)
    # Some match, some don't
    portal_invoices = []
    # 7 match perfectly
    for i in range(7):
        inv = book_invoices[i].copy()
        inv["irn"] = f"irn_portal_{i+1:03d}"
        inv["source"] = "GSTR-2B"
        portal_invoices.append(inv)
        
    # 1 mismatch in amount
    inv = book_invoices[7].copy()
    inv["irn"] = f"irn_portal_008"
    inv["tax_amount"] += 10.50 # Mismatch
    inv["source"] = "GSTR-2B"
    portal_invoices.append(inv)
    
    # 2 missing in GSTR-2B (book_invoices[8], [9])
    
    # 2 Extra in GSTR-2B (not in books)
    for i in range(2):
        supplier = random.choice(taxpayers[1:])
        irn = f"irn_portal_extra_{i+1:03d}"
        inv_num = f"EXT/2026/{i+1:03d}"
        date = f"2026-02-{random.randint(1, 25):02d}"
        taxable_val = random.randint(1000, 10000)
        tax_amount = round(taxable_val * 0.18, 2)
        
        portal_invoices.append({
            "irn": irn,
            "inv_num": inv_num,
            "date": date,
            "taxable_val": taxable_val,
            "tax_amount": tax_amount,
            "supplier_gstin": supplier["gstin"],
            "recipient_gstin": "27AAAAA0000A1Z5",
            "source": "GSTR-2B"
        })
        
    # Generate Returns
    returns = [
        {"return_id": "rtn_001", "rtn_type": "GSTR-3B", "tax_period": "Feb-2026", "gstin": "27AAAAA0000A1Z5", "status": "Filed"},
        {"return_id": "rtn_002", "rtn_type": "GSTR-1", "tax_period": "Feb-2026", "gstin": "29BBBBB0000B1Z6", "status": "Filed"},
        {"return_id": "rtn_003", "rtn_type": "GSTR-1", "tax_period": "Feb-2026", "gstin": "19DDDDD0000D1Z8", "status": "Filed"}
    ]
    
    data = {
        "taxpayers": taxpayers,
        "book_invoices": book_invoices,
        "portal_invoices": portal_invoices,
        "returns": returns
    }
    
    with open("data/mock_gst_data.json", "w") as f:
        json.dump(data, f, indent=4)
    
    print("Mock data generated at data/mock_gst_data.json")

if __name__ == "__main__":
    generate_mock_data()
