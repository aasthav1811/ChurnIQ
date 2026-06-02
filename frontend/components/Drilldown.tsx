"use client";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from "recharts";
import { getTopCustomers, getCustomer } from "@/lib/api";

const RISK_COLOR: Record<string,string> = { low:"#34d399", medium:"#fbbf24", high:"#f87171" };

export default function Drilldown() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedId, setSelectedId]   = useState<string>("");
  const [detail, setDetail]   = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getTopCustomers(100, "high").then((data) => {
      setCustomers(data);
      if (data.length > 0) setSelectedId(data[0].customerID);
    });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    setDetail(null);
    getCustomer(selectedId)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [selectedId]);

  const p = detail?.profile;
  const rc = p ? RISK_COLOR[p.risk_band] : "#fff";

  return (
    <div className="space-y-5">
      {/* Selector */}
      <div className="glass p-5 flex items-center gap-4">
        <span className="text-white/40 text-sm font-medium uppercase tracking-wider">Customer</span>
        <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
          className="flex-1 max-w-xs rounded-xl px-4 py-2.5 text-sm font-medium text-white outline-none cursor-pointer"
          style={{ background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.14)" }}>
          {customers.map(c => (
            <option key={c.customerID} value={c.customerID} style={{ background:"#1e1b4b" }}>
              {c.customerID} — {(c.churn_probability*100).toFixed(0)}% risk
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="glass p-10 text-center text-white/40 text-sm animate-pulse">
          Loading customer data...
        </div>
      )}

      {detail && p && (
        <>
          {/* Profile card */}
          <div className="glass p-7">
            <div className="flex items-center gap-4 mb-6 flex-wrap">
              <span className="text-xl font-bold text-white">{p.customerID}</span>
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase"
                style={{ background:`${rc}22`, color:rc, border:`1px solid ${rc}44` }}>
                {p.risk_band} risk
              </span>
              <span className="text-white/40 text-sm">{p.segment}</span>
              <div className="ml-auto flex items-baseline gap-2">
                <span className="text-4xl font-black" style={{ color:rc }}>
                  {(p.churn_probability*100).toFixed(1)}%
                </span>
                <span className="text-white/35 text-sm">churn probability</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                ["Tenure",          `${p.tenure} months`],
                ["Monthly Charges", `$${p.MonthlyCharges.toFixed(2)}`],
                ["Contract",        p.Contract],
                ["Internet Service",p.InternetService],
                ["Payment Method",  p.PaymentMethod],
                ["Total Charges",   `$${p.TotalCharges.toFixed(2)}`],
              ].map(([k,v]) => (
                <div key={k} className="rounded-xl p-3.5"
                  style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)" }}>
                  <div className="text-xs uppercase tracking-wider mb-1 font-medium" style={{ color:"rgba(255,255,255,0.38)" }}>{k}</div>
                  <div className="text-white font-semibold">{v}</div>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP chart */}
          <div className="glass p-7">
            <div className="section-heading">Why is this customer at risk?</div>
            <ResponsiveContainer width="100%" height={360}>
              <BarChart
                data={detail.shap_drivers}
                layout="vertical"
                margin={{ top:5, right:20, left:180, bottom:5 }}>
                <XAxis type="number" tick={{ fill:"rgba(255,255,255,0.4)", fontSize:11 }}
                  tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="feature" width={175}
                  tick={{ fill:"rgba(255,255,255,0.6)", fontSize:11 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background:"rgba(15,12,41,0.95)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:10, color:"white", fontSize:12 }}
                  formatter={(v: any) => [v.toFixed(4), "Impact"]} />
                <Bar dataKey="shap_value" radius={[0,4,4,0]}>
                  {detail.shap_drivers.map((d: any, i: number) => (
                    <Cell key={i} fill={d.shap_value > 0 ? "#f87171" : "#34d399"} fillOpacity={0.82} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs mt-3" style={{ color:"rgba(255,255,255,0.3)" }}>
              🔴 Red bars push this customer toward churning &nbsp;·&nbsp; 🟢 Green bars protect against it
            </p>
          </div>
        </>
      )}
    </div>
  );
}