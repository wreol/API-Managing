import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import apiClient from '../api/client';
import type { UsageSummary, UsageTrendPoint, KeyBreakdown } from '../types';

const COLORS = ['#5e6ad2', '#30a46c', '#f5a623', '#e5484d', '#6b6b6b', '#8b5cf6', '#06b6d4'];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [trend, setTrend] = useState<UsageTrendPoint[]>([]);
  const [topKeys, setTopKeys] = useState<KeyBreakdown[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        const [summaryRes, trendRes, keysRes] = await Promise.all([
          apiClient.get<UsageSummary>('/usage/summary'),
          apiClient.get<UsageTrendPoint[]>('/usage/trend'),
          apiClient.get<KeyBreakdown[]>('/usage/by-key'),
        ]);
        setSummary(summaryRes.data);
        setTrend(trendRes.data);
        setTopKeys(keysRes.data.slice(0, 10));
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setError(detail ?? 'Failed to load usage data.');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  function formatCost(n: number): string {
    return `$${n.toFixed(4)}`;
  }

  function formatNumber(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toLocaleString();
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  const hasData = summary && (summary.total_calls > 0 || summary.total_cost > 0);

  if (!hasData) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="empty-state-icon">#</div>
          <div className="empty-state-title">Add your first API Key to see usage data</div>
          <div className="empty-state-desc">
            Once you add an API key, we will start tracking calls, tokens, and costs for you.
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/keys')}>
            Go to Keys
          </button>
        </div>
      </div>
    );
  }

  const pieData = summary!.by_provider.map((p) => ({
    name: p.provider,
    value: p.cost,
  }));

  return (
    <div className="page-container">
      {/* Summary Cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Total Calls</div>
          <div className="stat-value">{formatNumber(summary!.total_calls)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Tokens</div>
          <div className="stat-value">{formatNumber(summary!.total_tokens)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Cost</div>
          <div className="stat-value">
            {formatCost(summary!.total_cost)}
            <span className="stat-unit">this month</span>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Cost by Provider</span>
          </div>
          <div className="chart-container">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => formatCost(value)}
                    contentStyle={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
                No provider data yet
              </div>
            )}
            {summary!.by_provider.length > 0 && (
              <div className="flex-row flex-wrap gap-8" style={{ justifyContent: 'center', marginTop: 8 }}>
                {summary!.by_provider.map((p, i) => (
                  <div key={p.provider} className="flex-row gap-8" style={{ fontSize: 12 }}>
                    <span style={{
                      width: 10, height: 10, borderRadius: 2,
                      background: COLORS[i % COLORS.length], display: 'inline-block',
                    }} />
                    <span style={{ color: 'var(--text-secondary)' }}>{p.provider}</span>
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{formatCost(p.cost)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Usage Trend (Calls)</span>
          </div>
          <div className="chart-container">
            {trend.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis
                    dataKey="period"
                    tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                    axisLine={{ stroke: 'var(--border-color)' }}
                  />
                  <YAxis
                    tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                    axisLine={{ stroke: 'var(--border-color)' }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius)',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="calls"
                    stroke={COLORS[0]}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: COLORS[0] }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
                No trend data yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Top Keys */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Top Keys by Cost</span>
        </div>
        {topKeys.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Provider</th>
                  <th>Calls</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {topKeys.map((k) => (
                  <tr key={k.key_id} className="clickable" onClick={() => navigate(`/keys/${k.key_id}`)}>
                    <td>{k.key_label}</td>
                    <td>{k.provider}</td>
                    <td>{formatNumber(k.calls)}</td>
                    <td>{formatNumber(k.tokens)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{formatCost(k.cost)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No key data yet
          </div>
        )}
      </div>
    </div>
  );
}
