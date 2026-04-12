// src/pages/AdminPage.jsx
import { useState } from 'react';
import { triggerScrape, getAdminJobs } from '../lib/api';

export default function AdminPage() {
  const [scrapeResult, setScrapeResult] = useState(null);
  const [scrapeLoading, setScrapeLoading] = useState(false);

  const handleScrape = async () => {
    setScrapeLoading(true);
    try {
      const result = await triggerScrape();
      setScrapeResult(result);
    } catch (err) {
      setScrapeResult({ status: 'error', message: err.message });
    } finally {
      setScrapeLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GeM Scraping */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">🔍 GeM Portal Scraping</h2>
          <p className="text-gray-600 mb-4">
            Manually trigger a scan of the GeM portal for new government orders.
          </p>
          <button
            onClick={handleScrape}
            disabled={scrapeLoading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {scrapeLoading ? '⏳ Scraping...' : '🚀 Start Scraping'}
          </button>

          {scrapeResult && (
            <div className={`mt-4 p-3 rounded-lg text-sm ${
              scrapeResult.status === 'success' 
                ? 'bg-green-50 text-green-700 border border-green-200' 
                : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
            }`}>
              <p>Status: {scrapeResult.status}</p>
              <p>{scrapeResult.message}</p>
              {scrapeResult.task_id && <p>Task ID: {scrapeResult.task_id}</p>}
            </div>
          )}
        </div>

        {/* System Info */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">ℹ️ System Information</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Backend</span>
              <span className="font-medium">FastAPI + Python</span>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Database</span>
              <span className="font-medium">PostgreSQL</span>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Task Queue</span>
              <span className="font-medium">Celery + Redis</span>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Blockchain</span>
              <span className="font-medium">Polygon (Mock)</span>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="text-gray-600">API Docs</span>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
                className="font-medium text-blue-600 hover:underline">
                Open Swagger UI →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}