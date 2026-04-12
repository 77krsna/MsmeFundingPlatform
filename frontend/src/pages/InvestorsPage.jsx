// src/pages/InvestorsPage.jsx
import { useEffect, useState } from 'react';
import { getOpportunities } from '../lib/api';
import StatusBadge from '../components/common/StatusBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function InvestorsPage() {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getOpportunities();
        setOpportunities(data || []);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingSpinner message="Loading opportunities..." />;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Investment Opportunities</h1>
      <p className="text-gray-500">Fund MSME government orders and earn returns</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {opportunities.map((opp) => (
          <div key={opp.order_id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-semibold text-lg">{opp.gem_order_id}</h3>
              <StatusBadge status={opp.status} />
            </div>
            
            <p className="text-2xl font-bold text-green-600 mb-2">
              ₹{Number(opp.order_amount).toLocaleString('en-IN')}
            </p>
            
            <div className="space-y-2 text-sm text-gray-600">
              <p>🏢 {opp.buyer_organization}</p>
              <p>📦 {opp.product_category}</p>
              <p>📅 Deadline: {new Date(opp.delivery_deadline).toLocaleDateString('en-IN')}</p>
              <p>📈 Est. Return: <span className="text-green-600 font-semibold">{opp.estimated_return}%</span></p>
              <p>⚠️ Risk Score: {opp.risk_score}/10</p>
            </div>

            <button className="w-full mt-4 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors">
              Invest Now
            </button>
          </div>
        ))}

        {opportunities.length === 0 && (
          <div className="col-span-3 text-center py-12 text-gray-500">
            No investment opportunities available right now.
          </div>
        )}
      </div>
    </div>
  );
}