"use client";
import { useState } from "react";
import Overview from "@/components/Overview";
import Drilldown from "@/components/Drilldown";
import Agent from "@/components/Agent";

const TABS = [
  { id: "overview",  label: "📊  Risk Overview" },
  { id: "drilldown", label: "🔍  Customer Drill-down" },
  { id: "agent",     label: "🤖  Retention Agent" },
];

export default function Home() {
  const [tab, setTab] = useState("overview");

  return (
    <main className="max-w-[1400px] mx-auto px-8 py-8">

      {/* Hero */}
      <div className="glass mb-8 p-10"
        style={{ background: "linear-gradient(135deg, rgba(139,92,246,0.2), rgba(59,130,246,0.12), rgba(16,185,129,0.08))",
                 border: "1px solid rgba(139,92,246,0.3)" }}>
        <span className="inline-block text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-4"
          style={{ background: "rgba(139,92,246,0.25)", border: "1px solid rgba(139,92,246,0.5)", color: "#c4b5fd" }}>
          Live Demo · Telco Dataset · 7,043 Customers
        </span>
        <h1 className="text-4xl font-bold text-white mb-2">📉 ChurnIQ</h1>
        <p className="text-white/50 text-base leading-relaxed">
          Predicts which customers will leave &nbsp;·&nbsp; Explains exactly why &nbsp;·&nbsp;
          Drafts personalized retention emails in seconds
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 mb-8 rounded-2xl w-fit"
        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className="px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
            style={tab === t.id
              ? { background: "rgba(139,92,246,0.4)", color: "white" }
              : { color: "rgba(255,255,255,0.45)" }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "overview"  && <Overview />}
      {tab === "drilldown" && <Drilldown />}
      {tab === "agent"     && <Agent />}
    </main>
  );
}