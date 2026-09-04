import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, XCircle, Shield, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export default function ComplianceMatrix({ complianceFindings = [], complianceRate = 0 }) {
  const [selectedFramework, setSelectedFramework] = useState('ALL');
  const [expandedControl, setExpandedControl] = useState(null);

  const frameworks = ['ALL', 'SOC 2 Type II', 'ISO 27001:2022', 'NIST CSF v2.0'];

  const filteredFindings = selectedFramework === 'ALL'
    ? complianceFindings
    : complianceFindings.filter((f) => f.framework.toLowerCase().includes(selectedFramework.toLowerCase().replace(' v2.0', '')));

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Satisfied':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            Satisfied
          </span>
        );
      case 'Partial':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" />
            Partial
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" />
            Gap
          </span>
        );
    }
  };

  return (
    <div className="w-full bg-trust-card border border-trust-border rounded-2xl p-6 shadow-xl backdrop-blur-md mb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-5 border-b border-trust-border/40">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-1.5 rounded-lg bg-trust-accent/10 border border-trust-accent/30 text-trust-accent">
              <Shield className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Compliance Framework Audit Matrix
            </h3>
          </div>
          <p className="text-xs text-gray-400">
            Automated alignment against standard audit frameworks performed by Compliance Mapping Agent
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">Compliance Rate</div>
            <div className="text-xl font-extrabold font-mono text-emerald-400">{complianceRate}%</div>
          </div>

          <div className="flex items-center gap-1 bg-trust-surface/80 p-1 rounded-xl border border-trust-border/50">
            {frameworks.map((fw) => (
              <button
                key={fw}
                onClick={() => setSelectedFramework(fw)}
                className={`text-xs font-mono px-2.5 py-1 rounded-lg transition-all ${
                  selectedFramework === fw
                    ? 'bg-trust-accent text-white font-semibold shadow-sm'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {fw === 'ALL' ? 'All Standards' : fw.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-2.5">
        {filteredFindings.length === 0 ? (
          <div className="py-8 text-center text-gray-500 text-xs font-mono">
            No compliance controls matched for the current filter.
          </div>
        ) : (
          filteredFindings.map((ctrl, idx) => {
            const isExpanded = expandedControl === `${ctrl.control_id}_${idx}`;
            return (
              <div
                key={`${ctrl.control_id}_${idx}`}
                className="border border-trust-border/30 rounded-xl overflow-hidden bg-trust-surface/30 hover:bg-trust-surface/50 transition-colors"
              >
                <div
                  onClick={() => setExpandedControl(isExpanded ? null : `${ctrl.control_id}_${idx}`)}
                  className="p-3.5 flex items-center justify-between cursor-pointer gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-mono text-xs font-bold text-trust-accent bg-trust-accent/10 px-2 py-1 rounded border border-trust-accent/20">
                      {ctrl.control_id}
                    </span>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white truncate">{ctrl.title}</div>
                      <div className="text-[10px] font-mono text-gray-400">{ctrl.framework}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {getStatusBadge(ctrl.status)}
                    <span className="text-gray-500">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </span>
                  </div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="px-4 pb-4 pt-1 text-xs border-t border-trust-border/20 bg-trust-surface/40"
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                        <div>
                          <span className="text-[10px] font-mono uppercase text-gray-400 block mb-1">
                            Framework Requirement:
                          </span>
                          <p className="text-gray-300 leading-relaxed bg-black/20 p-2.5 rounded-lg border border-trust-border/20">
                            {ctrl.requirement}
                          </p>
                        </div>
                        <div>
                          <span className="text-[10px] font-mono uppercase text-trust-accent flex items-center gap-1 mb-1">
                            <FileText className="w-3 h-3" />
                            Matched Vendor Evidence:
                          </span>
                          <p className="text-gray-300 leading-relaxed bg-black/20 p-2.5 rounded-lg border border-trust-border/20">
                            {ctrl.matched_evidence}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
