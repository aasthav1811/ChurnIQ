"use client";
import { useEffect, useState } from "react";
import { getTopCustomers, runAgent } from "@/lib/api";

const RISK_COLOR: Record<string,string> = { low:"#34d399", medium:"#fbbf24", high:"#f87171" };

export default function Agent() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [result, setResult]   = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<any>(null);

  useEffect(() => {
    getTopCustomers(50, "high").then(data => {
      setCustomers(data);
      if (data.length) { setSelectedId(data[0].customerID); setPreview(data[0]); }
    });
  }, []);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setResult(null);
    setPreview(customers.find(c => c.customerID === id));
  };

  const handleGenerate = async () => {
    setLoading(true);
    setResult(null);
    try { setResult(await runAgent(selectedId)); }
    catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  const rc = preview ? RISK_COLOR[preview.risk_band] : "#fff";

  return (
    <div className="glass p-7 space-y-6">
      <div>
        <div className="section-heading">AI Retention Agent</div>
        <p className="text-sm" style={{ color:"rgba(255,255,255,0.45)", lineHeight:1.7 }}>
          Pick a high-risk customer. The agent reads their churn drivers, selects the best
          offers, and writes a personalized retention email — grounded in data, not templates.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left: selector + snapshot */}
        <div className="space-y-4">
          <select value={selectedId} onChange={e => handleSelect(e.target.value)}
            className="w-full rounded-xl px-4 py-2.5 text-sm font-medium text-white outline-none cursor-pointer"
            style={{ background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.14)" }}>
            {customers.map(c => (
              <option key={c.customerID} value={c.customerID} style={{ background:"#1e1b4b" }}>
                {c.customerID} — {(c.churn_probability*100).toFixed(0)}% risk
              </option>
            ))}
          </select>

          {preview && (
            <div className="rounded-2xl p-5 space-y-3"
              style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)" }}>
              <div className="text-xs uppercase tracking-wider font-medium mb-2" style={{ color:"rgba(255,255,255,0.38)" }}>
                Customer Snapshot
              </div>
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-3xl font-black" style={{ color:rc }}>
                  {(preview.churn_probability*100).toFixed(0)}%
                </span>
                <span className="text-xs" style={{ color:"rgba(255,255,255,0.35)" }}>churn probability</span>
              </div>
              {[["Tenure", `${preview.tenure} months`],
                ["Monthly Charges", `$${preview.MonthlyCharges?.toFixed(2)}`],
                ["Segment", preview.segment]
              ].map(([k,v]) => (
                <div key={k}>
                  <div className="text-xs uppercase tracking-wider" style={{ color:"rgba(255,255,255,0.35)" }}>{k}</div>
                  <div className="font-semibold text-white text-sm">{v}</div>
                </div>
              ))}
            </div>
          )}

          <button onClick={handleGenerate} disabled={loading || !selectedId}
            className="w-full py-3 px-5 rounded-xl font-semibold text-sm text-white transition-all duration-200 disabled:opacity-50"
            style={{ background:"linear-gradient(135deg,#7c3aed,#4f46e5)",
                     boxShadow:"0 4px 20px rgba(124,58,237,0.4)" }}>
            {loading ? "✨ Generating..." : "✍️  Generate Retention Email"}
          </button>
        </div>

        {/* Right: results */}
        <div className="col-span-2">
          {loading && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center space-y-3">
                <div className="text-4xl animate-bounce">🤖</div>
                <div className="text-white/40 text-sm animate-pulse">
                  Analyzing risk drivers and drafting email...
                </div>
              </div>
            </div>
          )}

          {!loading && !result && (
            <div className="h-full min-h-80 flex flex-col items-center justify-center rounded-2xl"
              style={{ border:"1px dashed rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.02)" }}>
              <div className="text-5xl mb-4">🤖</div>
              <div className="text-sm text-center leading-relaxed" style={{ color:"rgba(255,255,255,0.4)" }}>
                Select a customer and click<br />
                <span style={{ color:"#a78bfa" }} className="font-semibold">Generate Retention Email</span>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Email */}
              <div>
                <div className="text-xs uppercase tracking-wider font-semibold mb-3" style={{ color:"rgba(255,255,255,0.4)" }}>
                  📧 Personalized Email Draft
                </div>
                <div className="rounded-xl p-5 text-sm leading-7 whitespace-pre-wrap"
                  style={{ background:"rgba(255,255,255,0.04)",
                           border:"1px solid rgba(255,255,255,0.08)",
                           borderLeft:"3px solid #8b5cf6",
                           color:"rgba(255,255,255,0.82)" }}>
                  {result.email}
                </div>
              </div>

              {/* Interventions */}
              <div>
                <div className="text-xs uppercase tracking-wider font-semibold mb-3" style={{ color:"rgba(255,255,255,0.4)" }}>
                  🎯 Selected Interventions
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.interventions.map((i: string, idx: number) => (
                    <span key={idx} className="px-3 py-1.5 rounded-full text-sm font-medium"
                      style={{ background:"rgba(139,92,246,0.18)", border:"1px solid rgba(139,92,246,0.35)", color:"#c4b5fd" }}>
                      {i}
                    </span>
                  ))}
                </div>
              </div>

              {/* SHAP drivers */}
              <div>
                <div className="text-xs uppercase tracking-wider font-semibold mb-3" style={{ color:"rgba(255,255,255,0.4)" }}>
                  🔍 Risk Drivers the Email Was Based On
                </div>
                <div className="space-y-2">
                  {result.shap_drivers.map((d: any, i: number) => {
                    const pct = Math.min(Math.abs(d.shap_value) * 300, 100);
                    const col = d.shap_value > 0 ? "#f87171" : "#34d399";
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-xs w-48 truncate" style={{ color:"rgba(255,255,255,0.55)" }} title={d.feature}>
                          {d.feature}
                        </span>
                        <div className="flex-1 rounded-full h-1.5" style={{ background:"rgba(255,255,255,0.06)" }}>
                          <div className="h-full rounded-full transition-all duration-500"
                            style={{ width:`${pct}%`, background:col, opacity:0.8 }} />
                        </div>
                        <span className="text-xs font-mono w-16 text-right" style={{ color:col }}>
                          {d.shap_value > 0 ? "+" : ""}{d.shap_value.toFixed(4)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}