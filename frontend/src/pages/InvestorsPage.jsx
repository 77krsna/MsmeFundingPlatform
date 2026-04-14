import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL;

export default function InvestorsPage() {
  const [items, setItems] = useState([]);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  const load = async () => {
    setError(null);
    const res = await fetch(`${API}/api/investors/opportunities`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || "Failed to load opportunities");
    setItems(Array.isArray(data) ? data : (data.items || []));
  };

  const investNow = async (o) => {
    setBusyId(o.order_id);
    setError(null);
    try {
      const res = await fetch(`${API}/api/investors/invest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: o.order_id, eth_wei: 1 }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || data.error || `Invest failed (${res.status})`);

      alert(`Invest success!\nTX: ${data.tx_hash}\nStatus: ${data.new_status}`);
      await load();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusyId(null);
    }
  };

  useEffect(() => {
    load().catch((e) => setError(String(e.message || e)));
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Investment Opportunities</h1>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded"
          onClick={() => load().catch((e) => setError(String(e)))}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 border border-red-300 bg-red-50 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((o) => {
          const isFunded = ["FUNDED", "REPAID", "DEFAULTED"].includes(o.status);
          return (
            <div key={o.order_id} className="border rounded p-4 bg-white">
              <div className="font-semibold">{o.gem_order_id}</div>
              <div className="text-2xl font-bold mt-1">
                ₹{Number(o.order_amount || 0).toLocaleString("en-IN")}
              </div>
              <div className="text-sm text-gray-600 mt-2">Status: {o.status}</div>
              <div className="text-sm text-gray-600">Risk: {o.risk_score}/10</div>
              <div className="text-sm text-gray-600">Est Return: {o.estimated_return}%</div>

              <button
                className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
                disabled={isFunded || busyId === o.order_id}
                onClick={() => investNow(o)}
              >
                {isFunded ? "Already Funded" : busyId === o.order_id ? "Investing..." : "Invest Now"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}