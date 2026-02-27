from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import networkx as nx
import pandas as pd
import os
import json
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from knowledge_graph import GSTKnowledgeGraph

app = FastAPI(title="GST Knowledge Graph Reconciliation API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kg = GSTKnowledgeGraph()

def load_data():
    """Load mock data into the Knowledge Graph."""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/mock_gst_data.json")
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}")
        return
        
    with open(data_path, "r") as f:
        data = json.load(f)
        
    for tp in data["taxpayers"]:
        kg.add_taxpayer(tp["gstin"], tp["legal_name"], tp.get("status", "Active"))
        
    for inv in data["book_invoices"]:
        kg.add_invoice(
            inv["irn"], inv["inv_num"], inv["date"], 
            inv["taxable_val"], inv["tax_amount"], 
            inv["supplier_gstin"], inv["recipient_gstin"], source="Books"
        )
        
    for inv in data["portal_invoices"]:
        kg.add_invoice(
            inv["irn"], inv["inv_num"], inv["date"], 
            inv["taxable_val"], inv["tax_amount"], 
            inv["supplier_gstin"], inv["recipient_gstin"], source="GSTR-2B"
        )
        
    for rtn in data["returns"]:
        kg.add_return(rtn["return_id"], rtn["rtn_type"], rtn["tax_period"], rtn["gstin"], rtn.get("status", "Filed"))

# Initial data load
load_data()

@app.get("/")
async def root():
    return {"message": "GST Knowledge Graph API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "nodes": kg.G.number_of_nodes(), "edges": kg.G.number_of_edges()}

@app.get("/reconcile/{gstin}")
async def reconcile_taxpayer(gstin: str, period: str = "Feb-2026"):
    try:
        results = kg.reconcile(gstin, period)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vendor-risk/{gstin}")
async def vendor_risk(gstin: str):
    try:
        if gstin not in kg.G:
             raise HTTPException(status_code=404, detail="Taxpayer not found")
             
        score = kg.get_vendor_compliance_score(gstin)
        # Explainable audit trail
        explanation = []
        node_data = kg.G.nodes[gstin]
        if node_data.get("status") != "Active":
            explanation.append(f"Vendor status is '{node_data.get('status')}'.")
        
        # Check for unfiled invoices
        total_issued = 0
        missing_returns = 0
        for n, data in kg.G.nodes(data=True):
            if data.get("label") == "Invoice":
                # Check if issued by this vendor
                # In MultiDiGraph, edges are (u, v)
                # Our schema: ISSUED_BY goes from Invoice to Taxpayer
                if kg.G.has_edge(n, gstin):
                    total_issued += 1
                    # Check if reported in GSTR-1 (from Invoice to Return)
                    has_return = False
                    for _, target, edge_data in kg.G.out_edges(n, data=True):
                        if edge_data.get("type") == "REPORTED_IN":
                            has_return = True
                            break
                    if not has_return:
                        missing_returns += 1
        
        if missing_returns > 0:
            explanation.append(f"{missing_returns} out of {total_issued} invoices issued by vendor are not reported in GSTR-1.")
        else:
            explanation.append(f"All {total_issued} invoices issued by vendor are reported in GSTR-1.")

        return {
            "gstin": gstin,
            "legal_name": node_data.get("legal_name"),
            "risk_score": score,
            "explanation": explanation
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/taxpayers")
async def get_taxpayers():
    return [{"gstin": n, "legal_name": d.get("legal_name"), "status": d.get("status")} 
            for n, d in kg.G.nodes(data=True) if d.get("label") == "Taxpayer"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
