import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL;

export default function MSMEPage() {
  const navigate = useNavigate();

  const [walletAddress, setWalletAddress] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [gstnNumber, setGstnNumber] = useState("");
  const [panNumber, setPanNumber] = useState("");
  const [email, setEmail] = useState("");

  const [list, setList] = useState([]);
  const [loadingList, setLoadingList] = useState(true);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadList = async () => {
    setLoadingList(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/msme/list`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to load MSME list");

      const items = Array.isArray(data) ? data : (data.items || []);
      setList(items);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        wallet_address: walletAddress,
        company_name: companyName,
        gstn_number: gstnNumber,
        pan_number: panNumber,
        email: email,
      };

      const res = await fetch(`${API}/api/msme/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || data.message || "MSME registration failed");

      setSuccess(`MSME registered successfully (id: ${data.msme_id || "created"})`);

      setWalletAddress("");
      setCompanyName("");
      setGstnNumber("");
      setPanNumber("");
      setEmail("");

      await loadList();

      // Optional: go to dashboard after a moment
      setTimeout(() => navigate("/dashboard"), 800);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">MSME Registration</h1>
        <p className="text-gray-600">Register your company and view registered MSMEs.</p>
      </div>

      {error && (
        <div className="p-3 rounded border border-red-300 bg-red-50 text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3 rounded border border-green-300 bg-green-50 text-green-700">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={submit} className="bg-white border rounded-lg p-4 space-y-3">
          <div className="font-semibold mb-1">Register Your Company</div>

          <div>
            <label className="block text-sm font-medium">Wallet Address</label>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              placeholder="0x..."
              value={walletAddress}
              onChange={(e) => setWalletAddress(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Company Name</label>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              placeholder="Enter company name"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">GSTN Number</label>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              placeholder="22AAAAA0000A1Z5"
              value={gstnNumber}
              onChange={(e) => setGstnNumber(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">PAN Number</label>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              placeholder="ABCDE1234F"
              value={panNumber}
              onChange={(e) => setPanNumber(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Email</label>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              placeholder="company@example.com"
              value={email}
              type="email"
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <button
            disabled={submitting}
            className="w-full mt-2 px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
          >
            {submitting ? "Registering..." : "Register MSME"}
          </button>
        </form>

        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="font-semibold">Registered MSMEs</div>
            <button
              onClick={loadList}
              className="px-3 py-1.5 rounded bg-gray-800 text-white"
            >
              Refresh
            </button>
          </div>

          {loadingList ? (
            <div className="text-gray-600">Loading list...</div>
          ) : list.length === 0 ? (
            <div className="text-gray-600">No MSMEs found. Register one to see it here.</div>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="py-2 pr-3">Company</th>
                    <th className="py-2 pr-3">Wallet</th>
                    <th className="py-2 pr-3">GSTN</th>
                    <th className="py-2 pr-3">Email</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((m) => (
                    <tr key={m.id || m.wallet_address} className="border-b">
                      <td className="py-2 pr-3">{m.company_name || "N/A"}</td>
                      <td className="py-2 pr-3">
                        <span className="font-mono text-xs">
                          {m.wallet_address ? `${m.wallet_address.slice(0, 6)}...${m.wallet_address.slice(-4)}` : "N/A"}
                        </span>
                      </td>
                      <td className="py-2 pr-3">{m.gstn_number || "N/A"}</td>
                      <td className="py-2 pr-3">{m.email || "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="text-xs text-gray-500 mt-3">
            Data source: <code>GET /api/msme/list</code>
          </div>
        </div>
      </div>
    </div>
  );
}