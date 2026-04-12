// src/components/common/StatusBadge.jsx
const statusColors = {
  DETECTED: 'bg-gray-100 text-gray-800',
  CONTRACT_CREATED: 'bg-blue-100 text-blue-800',
  FUNDED: 'bg-purple-100 text-purple-800',
  PRODUCTION: 'bg-yellow-100 text-yellow-800',
  DELIVERED: 'bg-green-100 text-green-800',
  REPAID: 'bg-green-200 text-green-900',
  DEFAULTED: 'bg-red-100 text-red-800',
  healthy: 'bg-green-100 text-green-800',
  unhealthy: 'bg-red-100 text-red-800',
  degraded: 'bg-yellow-100 text-yellow-800',
};

export default function StatusBadge({ status }) {
  const colorClass = statusColors[status] || 'bg-gray-100 text-gray-800';

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${colorClass}`}>
      {status}
    </span>
  );
}