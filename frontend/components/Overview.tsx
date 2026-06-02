"use client";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
         ScatterChart, Scatter, Cell } from "recharts";
import { getDashboard } from "@/lib/api";

const RISK_COLOR: Record<string,string> = {
  low: "#34d399", medium: "#fbbf24", high: "#f87171"
};
const SEG_COLOR: Record<string,string> = {
  "VIP at risk":"#f87171","High risk":"#fb923c","New & uncertain":"#fbbf24",
  "Watch list":"#60a5fa","Healthy":"#34d399","Other":"#9ca3af"
};

function KPI({ label, value, sub, color }: any) {
  return (
    <div className="glass glass-hover p-6 text-center cursor-default"
      style={{ border: "1px solid rgba(255,255,255,0.13)" }}>
      <div className="text-xs uppercase tracking-widest font-medium mb-2" style={{ color: "rgba(255,255,255,0.45)" }}>{label}</div>
      <div className="text-3xl font-bold" style={{ color }}>{value}</div>
      <div className="text-xs mt-1.5" style={{ color: "rgba(255,255,255,0.35)" }}>{sub}</div>
    </div>
  );
}

const CT = { fill: "rgba(0,0,0,0)", stroke: "none" };
const AxisStyle = { fill: "rgba(255,255,255,0.4)", fontSize: 11 };
const GridLine  = "rgba(255,255,255,0.06)";

export default function Overview() {
  const [data, setData] = useState<any>(null);

  useEffect(() => { getDashboard().then(setData).catch(console.error); }, []);

  if (!data) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-white/40 text-sm animate-pulse">Loading dashboard...</div>
    </div>
  );

  const { kpis, histogram, segment_counts, contract_risk, scatter_sample, top20 } = data;
  const segData = Object.entries(segment_counts).map(([name, count]) => ({ name, count }));
  const contractData = Object.entries(contract_risk).map(([name, value]) => ({ name, value: Math.round((value as number)*100) }));

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-5">
        <KPI label="Total Customers"      value={kpis.total_customers.toLocaleString()}  sub="Active accounts"              color="#a78bfa" />
        <KPI label="Predicted to Churn"   value={kpis.high_risk_count.toLocaleString()}  sub={`${(kpis.high_risk_pct*100).toFixed(1)}% of base`} color="#f87171" />
        <KPI label="Monthly Revenue at Risk" value={`$${kpis.revenue_at_risk.toLocaleString()}`} sub="High-risk accounts"   color="#fbbf24" />
        <KPI label="Healthy Customers"    value={kpis.low_risk_count.toLocaleString()}   sub="Low churn probability"        color="#34d399" />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-2 gap-5">
        <div className="glass p-6">
          <div className="section-heading">Churn Probability Distribution</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={histogram} margin={{ top:10, right:10, left:-10, bottom:0 }}>
              <XAxis dataKey="bucket" tick={AxisStyle} />
              <YAxis tick={AxisStyle} />
              <Tooltip contentStyle={{ background:"rgba(15,12,41,0.9)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, color:"white", fontSize:12 }} />
              <Bar dataKey="count" radius={[4,4,0,0]}>
                {histogram.map((h: any, i: number) => <Cell key={i} fill={RISK_COLOR[h.risk]} fillOpacity={0.8} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-6">
          <div className="section-heading">Customer Segments</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={segData} margin={{ top:10, right:10, left:-10, bottom:40 }}>
              <XAxis dataKey="name" tick={{ ...AxisStyle, fontSize:10 }} angle={-20} textAnchor="end" />
              <YAxis tick={AxisStyle} />
              <Tooltip contentStyle={{ background:"rgba(15,12,41,0.9)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, color:"white", fontSize:12 }} />
              <Bar dataKey="count" radius={[4,4,0,0]}>
                {segData.map((s: any, i: number) => <Cell key={i} fill={SEG_COLOR[s.name] || "#9ca3af"} fillOpacity={0.85} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-2 gap-5">
        <div className="glass p-6">
          <div className="section-heading">Tenure vs Monthly Charges</div>
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart margin={{ top:10, right:10, left:-10, bottom:0 }}>
              <XAxis dataKey="tenure" name="Tenure (mo)" tick={AxisStyle} label={{ value:"Tenure (months)", fill:"rgba(255,255,255,0.3)", fontSize:11, position:"insideBottom", offset:-2 }} />
              <YAxis dataKey="MonthlyCharges" name="Monthly ($)" tick={AxisStyle} />
              <Tooltip cursor={{ strokeDasharray:"3 3", stroke:"rgba(255,255,255,0.2)" }}
                contentStyle={{ background:"rgba(15,12,41,0.9)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, color:"white", fontSize:12 }} />
              <Scatter data={scatter_sample} fillOpacity={0.6}>
                {scatter_sample.map((p: any, i: number) => <Cell key={i} fill={RISK_COLOR[p.risk_band]} />)}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-6">
          <div className="section-heading">Avg Churn Risk by Contract Type</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={contractData} margin={{ top:10, right:10, left:-10, bottom:0 }}>
              <XAxis dataKey="name" tick={AxisStyle} />
              <YAxis tick={AxisStyle} tickFormatter={v => `${v}%`} />
              <Tooltip contentStyle={{ background:"rgba(15,12,41,0.9)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, color:"white", fontSize:12 }}
                formatter={(v: any) => [`${v}%`, "Churn Risk"]} />
              <Bar dataKey="value" radius={[4,4,0,0]}>
                {contractData.map((c: any, i: number) => (
                  <Cell key={i} fill={c.value > 40 ? "#f87171" : c.value > 20 ? "#fbbf24" : "#34d399"} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top 20 table */}
      <div className="glass p-6">
        <div className="section-heading">🚨 Top 20 Customers Most Likely to Churn</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.08)" }}>
                {["Customer ID","Tenure","Monthly $","Contract","Internet","Churn Risk","Risk","Segment"]
                  .map(h => <th key={h} className="text-left py-3 px-3 text-xs uppercase tracking-wider font-medium" style={{ color:"rgba(255,255,255,0.4)" }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {top20.map((c: any, i: number) => (
                <tr key={i} className="transition-colors duration-150"
                  style={{ borderBottom:"1px solid rgba(255,255,255,0.04)" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                  <td className="py-3 px-3 font-medium text-white/80">{c.customerID}</td>
                  <td className="py-3 px-3 text-white/60">{c.tenure} mo</td>
                  <td className="py-3 px-3 text-white/60">${c.MonthlyCharges}</td>
                  <td className="py-3 px-3 text-white/60">{c.Contract}</td>
                  <td className="py-3 px-3 text-white/60">{c.InternetService}</td>
                  <td className="py-3 px-3 font-bold" style={{ color: RISK_COLOR[c.risk_band] }}>
                    {(c.churn_probability*100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded-full text-xs font-bold uppercase"
                      style={{ background: `${RISK_COLOR[c.risk_band]}22`, color: RISK_COLOR[c.risk_band], border:`1px solid ${RISK_COLOR[c.risk_band]}44` }}>
                      {c.risk_band}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-white/50 text-xs">{c.segment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}