import React from 'react';
import { Clock, Cpu, Sparkles, CheckCheck } from 'lucide-react';

export default function TelemetryBar({ stats }) {
  if (!stats) return null;

  const metrics = [
    {
      label: 'FAISS Retrieval',
      value: stats.retrieval_ms ? `${stats.retrieval_ms} ms` : '—',
      icon: Cpu,
      color: 'text-trust-cyan'
    },
    {
      label: 'OpenAI Generation',
      value: stats.generation_ms ? `${(stats.generation_ms / 1000).toFixed(2)} s` : '—',
      icon: Sparkles,
      color: 'text-trust-accent'
    },
    {
      label: 'NLI Verification',
      value: stats.verification_ms ? `${stats.verification_ms} ms` : '—',
      icon: CheckCheck,
      color: 'text-trust-green'
    },
    {
      label: 'Total Pipeline Time',
      value: stats.total_ms ? `${(stats.total_ms / 1000).toFixed(2)} s` : '—',
      icon: Clock,
      color: 'text-gray-200'
    }
  ];

  return (
    <div className="glass-panel rounded-2xl p-4 border border-trust-border/80">
      <div className="text-[11px] font-mono uppercase tracking-wider text-trust-muted mb-3 flex items-center justify-between">
        <span>Execution Telemetry</span>
        <span>Low-latency CPU inference</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {metrics.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="p-3 rounded-xl bg-trust-surface/60 border border-trust-border/50">
              <div className="flex items-center space-x-1.5 text-xs text-trust-muted mb-1">
                <Icon className={`w-3.5 h-3.5 ${item.color}`} />
                <span className="truncate">{item.label}</span>
              </div>
              <div className="text-base font-mono font-bold text-white">
                {item.value}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
