const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getDashboard() {
  const res = await fetch(`${BASE}/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load dashboard");
  return res.json();
}

export async function getTopCustomers(limit = 50, risk = "high") {
  const res = await fetch(`${BASE}/customers?limit=${limit}&risk=${risk}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load customers");
  return res.json();
}

export async function getCustomer(id: string) {
  const res = await fetch(`${BASE}/customers/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Customer not found");
  return res.json();
}

export async function runAgent(id: string) {
  const res = await fetch(`${BASE}/customers/${id}/agent`, {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Agent failed");
  return res.json();
}