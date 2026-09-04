import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, AlertOctagon, TrendingUp, Award, ExternalLink, Globe } from 'lucide-react';

export default function VendorRiskCard({ assessment }) {
  if (!assessment) return null;

  const { vendor_profile, risk_assessment, report_narrative, qa_verification } = assessment;
  const score = risk_assessment?.risk_score ?? 25;
  const tier = risk_assessment?.risk_tier ?? 'Moderate';

  const getTierColor = (t) => {
    switch (t) {
      case 'Low':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          text: 'text-emerald-400',
          ring: 'stroke-emerald-400'
        };
      case 'Moderate':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          text: 'text-amber-400',
          ring: 'stroke-amber-400'
        };
      case 'High':
        return {
          bg: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
          text: 'text-orange-400',
          ring: 'stroke-orange-400'
        };
      default:
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          text: 'text-rose-400',
          ring: 'stroke-rose-400'
        };
    }
  };

  const colors = getTierColor(tier);
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="w-full bg-trust-card border border-trust-border rounded-2xl p-6 shadow-xl backdrop-blur-md mb-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
        {/* Left: Vendor Profile & Status */}
        <div className="lg:col-span-2">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="text-xs font-mono text-gray-400 flex items-center gap-1">
              <Globe className="w-3.5 h-3.5 text-trust-accent" />
              {vendor_profile?.domain}
            </span>
            <span className="text-gray-600">•</span>
            <span className="text-xs font-mono text-gray-400">{vendor_profile?.industry}</span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${colors.bg}`}>
              {vendor_profile?.data_tier}
            </span>
          </div>

          <h2 className="text-2xl font-black text-white tracking-tight mb-3 flex items-center gap-2">
            <span>{vendor_profile?.name}</span>
            {qa_verification?.trust_seal?.certified && (
              <span title="Grounding verified with NLI claim assurance">
                <ShieldCheck className="w-5 h-5 text-emerald-400 inline" />
              </span>
            )}
          </h2>

          <div className="p-4 rounded-xl bg-trust-surface/60 border border-trust-border/40 text-xs text-gray-200 leading-relaxed mb-4">
            <span className="font-mono text-[10px] uppercase text-trust-accent block mb-1">
              Executive Findings & Assessment Narrative:
            </span>
            <p className="font-sans">{report_narrative}</p>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-300">
            <div>
              <span className="text-gray-400">Security Rating: </span>
              <span className="font-bold text-emerald-400">{risk_assessment?.factors?.security_rating}/100</span>
            </div>
            <div className="text-gray-600">•</div>
            <div>
              <span className="text-gray-400">Critical CVEs: </span>
              <span className="font-bold text-white">{risk_assessment?.factors?.critical_cves ?? 0}</span>
            </div>
            <div className="text-gray-600">•</div>
            <div>
              <span className="text-gray-400">Breach Incidents: </span>
              <span className="font-bold text-white">{risk_assessment?.factors?.breach_count ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Right: Quantitative Risk Score Gauge */}
        <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-trust-surface/40 border border-trust-border/40">
          <div className="relative w-32 h-32 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 96 96">
              <circle
                cx="48"
                cy="48"
                r={radius}
                className="stroke-trust-border/40"
                strokeWidth="7"
                fill="none"
              />
              <motion.circle
                cx="48"
                cy="48"
                r={radius}
                className={colors.ring}
                strokeWidth="7"
                strokeDasharray={circumference}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset: offset }}
                transition={{ duration: 1.2, ease: 'easeOut' }}
                strokeLinecap="round"
                fill="none"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className={`text-2xl font-black font-mono tracking-tight ${colors.text}`}>
                {score}
              </span>
              <span className="text-[10px] font-mono text-gray-400 uppercase">Risk Score</span>
            </div>
          </div>

          <div className="mt-3 text-center">
            <span className={`text-xs font-mono font-bold px-3 py-1 rounded-full border ${colors.bg}`}>
              {tier} Residual Risk
            </span>
            <p className="text-[11px] text-gray-400 mt-2 max-w-[200px]">
              {risk_assessment?.recommendation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
