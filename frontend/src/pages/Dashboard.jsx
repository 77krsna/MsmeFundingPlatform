// src/pages/Dashboard.jsx
import { useEffect, useState } from 'react';
import { getHealth, getStatus, getOrderStats } from '../lib/api';
import StatCard from '../components/common/StatCard';
import StatusBadge from '../components/common/StatusBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [status, setStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, statusData, statsData] = await Promise.all([
        getHealth(),
        getStatus(),
        getOrderStats(),
      ]);
      setHealth(healthData);
      setStatus(statusData);
      setStats(statsData);
    } catch (err) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingSpinner message="Loading dashboard..." />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  const platform = status?.platform || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">MSME Finance Platform Overview</p>
        </div>
        <div className="flex items-center space-x-3">
          <StatusBadge status={health?.status || 'unknown'} />
          <button
            onClick={fetchData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Orders"
          value={platform.total_orders || 0}
          icon="📋"
          color="blue"
        />
        <StatCard
          title="Active Orders"
          value={platform.active_orders || 0}
          icon="🔄"
          color="yellow"
        />
        <StatCard
          title="Total Volume"
          value={`₹${(stats?.total_volume || 0).toLocaleString('en-IN')}`}
          icon="💰"
          color="green"
        />
        <StatCard
          title="Total MSMEs"
          value={platform.total_msmes || 0}
          icon="🏭"
          color="purple"
        />
      </div>

      {/* Services Status */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">System Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium">Database</p>
              <p className="text-sm text-gray-500">PostgreSQL</p>
            </div>
            <StatusBadge status={health?.services?.database || 'unknown'} />
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium">Blockchain</p>
              <p className="text-sm text-gray-500">Polygon (Mock)</p>
            </div>
            <StatusBadge status={health?.services?.blockchain || 'unknown'} />
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium">Oracle</p>
              <p className="text-sm text-gray-500">GeM Monitoring</p>
            </div>
            <StatusBadge status="healthy" />
          </div>
        </div>
      </div>

      {/* Order Status Breakdown */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Order Status Breakdown</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {stats && Object.entries(stats.by_status || {}).map(([statusName, count]) => (
            <div key={statusName} className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{count}</p>
              <StatusBadge status={statusName} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}