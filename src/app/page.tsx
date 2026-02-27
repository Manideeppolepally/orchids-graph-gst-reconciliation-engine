"use client";

import { useState, useEffect } from "react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell 
} from "recharts";
import { 
  Search, ShieldAlert, CheckCircle2, AlertTriangle, Info, 
  ArrowRight, Filter, Download, User, Building2, FileText
} from "lucide-react";

export default function GSTDashboard() {
  const [taxpayers, setTaxpayers] = useState([]);
  const [selectedGstin, setSelectedGstin] = useState("");
  const [reconData, setReconData] = useState(null);
  const [vendorRisk, setVendorRisk] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/proxy/taxpayers")
      .then(res => res.json())
      .then(data => {
        setTaxpayers(data);
        if (data.length > 0) setSelectedGstin(data[0].gstin);
      });
  }, []);

  useEffect(() => {
    if (selectedGstin) {
      setLoading(true);
      Promise.all([
        fetch(`/api/proxy/reconcile/${selectedGstin}`).then(res => res.json()),
        fetch(`/api/proxy/vendor-risk/${selectedGstin}`).then(res => res.json())
      ]).then(([recon, risk]) => {
        setReconData(recon);
        setVendorRisk(risk);
        setLoading(false);
      });
    }
  }, [selectedGstin]);

  const COLORS = ['#10b981', '#ef4444', '#f59e0b', '#3b82f6'];

  const getPieData = () => {
    if (!reconData) return [];
    return [
      { name: 'Matched', value: reconData.matched.length },
      { name: 'Supplier Missing', value: reconData.mismatch_supplier_missing.length },
      { name: 'Recipient Missing', value: reconData.mismatch_recipient_missing.length },
      { name: 'Amount Mismatch', value: reconData.mismatch_amount.length },
    ];
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans">
      <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Intelligent GST Reconciliation</h1>
          <p className="text-slate-500">Knowledge Graph-based ITC Validation & Risk Intelligence</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <select 
              value={selectedGstin}
              onChange={(e) => setSelectedGstin(e.target.value)}
              className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
            >
              {taxpayers.map(tp => (
                <option key={tp.gstin} value={tp.gstin}>{tp.legal_name} ({tp.gstin})</option>
              ))}
            </select>
          </div>
          <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow-sm font-medium">
            <Download className="w-4 h-4" />
            Export Audit Trail
          </button>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : reconData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Summary Stats */}
          <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-xs font-medium text-slate-400">Matched</span>
              </div>
              <p className="text-2xl font-bold">{reconData.matched.length}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span className="text-xs font-medium text-slate-400">Value Mismatch</span>
              </div>
              <p className="text-2xl font-bold text-amber-600">{reconData.mismatch_amount.length}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <ShieldAlert className="w-5 h-5 text-rose-500" />
                <span className="text-xs font-medium text-slate-400">Missing in 2B</span>
              </div>
              <p className="text-2xl font-bold text-rose-600">{reconData.mismatch_supplier_missing.length}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <Info className="w-5 h-5 text-blue-500" />
                <span className="text-xs font-medium text-slate-400">Missing in Books</span>
              </div>
              <p className="text-2xl font-bold text-blue-600">{reconData.mismatch_recipient_missing.length}</p>
            </div>
          </div>

          {/* Vendor Compliance Score */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Vendor Risk Profile</h3>
            <div className="flex items-center gap-4 mb-6">
              <div className={`text-3xl font-bold px-4 py-2 rounded-lg ${
                vendorRisk?.risk_score > 80 ? 'bg-emerald-100 text-emerald-700' : 
                vendorRisk?.risk_score > 50 ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700'
              }`}>
                {vendorRisk?.risk_score}
              </div>
              <div>
                <p className="font-medium text-slate-900">{vendorRisk?.legal_name}</p>
                <p className="text-xs text-slate-500">Compliance Probability</p>
              </div>
            </div>
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Explainable Audit Trail</h4>
              {vendorRisk?.explanation.map((e, i) => (
                <div key={i} className="flex gap-2 items-start text-sm text-slate-600">
                  <ArrowRight className="w-3 h-3 mt-1 text-slate-400 flex-shrink-0" />
                  <span>{e}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reconciliation Chart */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-2">
            <h3 className="text-lg font-semibold mb-6">ITC Leakage Analysis</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={getPieData()}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {getPieData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend verticalAlign="bottom" height={36}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Mismatch Classification List */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-3">
            <h3 className="text-lg font-semibold mb-4">Mismatch Classification (Root Cause Analysis)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3">Invoice #</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Classification</th>
                    <th className="px-4 py-3">Risk Factor</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {reconData.mismatch_supplier_missing.map((inv, idx) => (
                    <tr key={`sm-${idx}`} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-4 font-medium text-slate-900">{inv.inv_num}</td>
                      <td className="px-4 py-4">₹{inv.taxable_val.toLocaleString()}</td>
                      <td className="px-4 py-4">
                        <span className="bg-rose-100 text-rose-700 px-2 py-1 rounded text-xs font-medium">Missing in GSTR-2B</span>
                      </td>
                      <td className="px-4 py-4 text-rose-600 font-medium">High - ITC Loss</td>
                      <td className="px-4 py-4">
                        <button className="text-blue-600 hover:underline">Follow up</button>
                      </td>
                    </tr>
                  ))}
                  {reconData.mismatch_amount.map((inv, idx) => (
                    <tr key={`am-${idx}`} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-4 font-medium text-slate-900">{inv.inv_num}</td>
                      <td className="px-4 py-4">₹{inv.portal_val.toLocaleString()}</td>
                      <td className="px-4 py-4">
                        <span className="bg-amber-100 text-amber-700 px-2 py-1 rounded text-xs font-medium">Value Mismatch</span>
                      </td>
                      <td className="px-4 py-4 text-amber-600 font-medium">Medium - Potential Notice</td>
                      <td className="px-4 py-4">
                        <button className="text-blue-600 hover:underline">Verify</button>
                      </td>
                    </tr>
                  ))}
                  {reconData.mismatch_recipient_missing.map((inv, idx) => (
                    <tr key={`rm-${idx}`} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-4 font-medium text-slate-900">{inv.inv_num}</td>
                      <td className="px-4 py-4">₹{inv.taxable_val.toLocaleString()}</td>
                      <td className="px-4 py-4">
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">Missing in Books</span>
                      </td>
                      <td className="px-4 py-4 text-blue-600 font-medium">Low - Unclaimed ITC</td>
                      <td className="px-4 py-4">
                        <button className="text-blue-600 hover:underline">Add to Books</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
