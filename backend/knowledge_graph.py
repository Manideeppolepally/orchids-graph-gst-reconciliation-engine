import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Optional
import datetime

class GSTKnowledgeGraph:
    def __init__(self):
        self.G = nx.MultiDiGraph()
        self.mismatch_logs = []

    def add_taxpayer(self, gstin: str, legal_name: str, status: str = "Active", filing_frequency: str = "Monthly"):
        """Add a Taxpayer node to the graph."""
        self.G.add_node(gstin, 
                         label="Taxpayer", 
                         gstin=gstin, 
                         legal_name=legal_name, 
                         status=status, 
                         filing_frequency=filing_frequency)

    def add_invoice(self, irn: str, inv_num: str, date: str, taxable_val: float, tax_amount: float, supplier_gstin: str, recipient_gstin: str, source: str = "Books"):
        """Add an Invoice node and link to Supplier and Recipient."""
        self.G.add_node(irn, 
                         label="Invoice", 
                         irn=irn, 
                         inv_num=inv_num, 
                         date=date, 
                         taxable_val=taxable_val, 
                         tax_amount=tax_amount,
                         source=source)
        
        # Link Invoice to Supplier
        if self.G.has_node(supplier_gstin):
            self.G.add_edge(irn, supplier_gstin, type="ISSUED_BY")
        
        # Link Recipient to Invoice
        if self.G.has_node(recipient_gstin):
            self.G.add_edge(recipient_gstin, irn, type="RECIPIENT_OF")

    def add_return(self, return_id: str, rtn_type: str, tax_period: str, gstin: str, status: str = "Filed"):
        """Add a Return node and link to Taxpayer."""
        self.G.add_node(return_id, 
                         label="Return", 
                         rtn_type=rtn_type, 
                         tax_period=tax_period, 
                         status=status)
        
        if self.G.has_node(gstin):
            self.G.add_edge(gstin, return_id, type="FILED_RETURN")

    def link_invoice_to_return(self, irn: str, return_id: str):
        """Link an Invoice to a Return (e.g., reported in GSTR-1)."""
        if self.G.has_node(irn) and self.G.has_node(return_id):
            self.G.add_edge(irn, return_id, type="REPORTED_IN")

    def reconcile(self, my_gstin: str, period: str):
        """Perform reconciliation for a specific taxpayer and period."""
        results = {
            "matched": [],
            "mismatch_supplier_missing": [], # In Books but not in GSTR-2B
            "mismatch_recipient_missing": [], # In GSTR-2B but not in Books
            "mismatch_amount": [], # Values don't match
            "risk_score": 0.0
        }
        
        # 1. Get all invoices where this taxpayer is the Recipient in Books
        book_invoices = []
        for n, data in self.G.nodes(data=True):
            if data.get("label") == "Invoice" and data.get("source") == "Books":
                # Check if this taxpayer is a recipient of this invoice
                if self.G.has_edge(my_gstin, n):
                    book_invoices.append(n)
        
        # 2. Get all invoices in GSTR-2B for this taxpayer
        # Actually GSTR-2B is a Return node, let's find invoices reported in it
        portal_invoices = {}
        for n, data in self.G.nodes(data=True):
            if data.get("label") == "Invoice" and data.get("source") == "GSTR-2B":
                if self.G.has_edge(my_gstin, n):
                    portal_invoices[data["inv_num"]] = n

        # Match by Invoice Number (simplification for this example)
        book_inv_nums = {self.G.nodes[irn]["inv_num"]: irn for irn in book_invoices}
        
        # In Books but NOT in 2B
        for inv_num, irn in book_inv_nums.items():
            if inv_num not in portal_invoices:
                results["mismatch_supplier_missing"].append({
                    "inv_num": inv_num,
                    "taxable_val": self.G.nodes[irn]["taxable_val"],
                    "reason": "Supplier has not uploaded invoice in GSTR-1"
                })
            else:
                # Potential amount mismatch
                portal_irn = portal_invoices[inv_num]
                book_val = self.G.nodes[irn]["tax_amount"]
                portal_val = self.G.nodes[portal_irn]["tax_amount"]
                
                if abs(book_val - portal_val) > 0.01:
                    results["mismatch_amount"].append({
                        "inv_num": inv_num,
                        "book_val": book_val,
                        "portal_val": portal_val,
                        "reason": "Tax amount mismatch"
                    })
                else:
                    results["matched"].append(inv_num)

        # In 2B but NOT in Books
        for inv_num, irn in portal_invoices.items():
            if inv_num not in book_inv_nums:
                results["mismatch_recipient_missing"].append({
                    "inv_num": inv_num,
                    "taxable_val": self.G.nodes[irn]["taxable_val"],
                    "reason": "Invoice present in portal but not recorded in purchase register"
                })

        return results

    def get_vendor_compliance_score(self, vendor_gstin: str):
        """Predict vendor risk using graph patterns."""
        # Multi-hop traversal: Check if vendor's invoices are consistently reported in returns
        # Check if vendor has filed GSTR-3B for previous periods
        # Check for circular patterns (A -> B -> A)
        
        score = 100
        # Placeholder for complex logic:
        # 1. Filing frequency of vendor
        vendor_data = self.G.nodes[vendor_gstin]
        if vendor_data.get("status") != "Active":
            score -= 50
            
        # 2. Count invoices issued by vendor that are NOT in a filed return
        total_issued = 0
        missing_returns = 0
        for irn in self.G.nodes:
            if self.G.nodes[irn].get("label") == "Invoice":
                if self.G.has_edge(irn, vendor_gstin): # ISSUED_BY
                    total_issued += 1
                    # Check if reported in GSTR-1
                    has_return = False
                    for _, target, edge_data in self.G.out_edges(irn, data=True):
                        if edge_data.get("type") == "REPORTED_IN":
                            has_return = True
                            break
                    if not has_return:
                        missing_returns += 1
        
        if total_issued > 0:
            score -= (missing_returns / total_issued) * 30
            
        return max(0, score)
