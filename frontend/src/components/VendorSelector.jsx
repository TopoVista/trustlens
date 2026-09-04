import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Building2, ShieldCheck, Database, BarChart3, CreditCard, Sliders, ChevronRight } from 'lucide-react';

const BENCHMARK_VENDORS = [
  {
    id: 'snowflake',
    name: 'Snowflake Data Cloud',
    domain: 'snowflake.com',
    industry: 'Cloud Data Warehousing',
    tier: 'Tier 1 (Critical)',
    tierColor: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    icon: Database,
    description: 'Enterprise cloud analytics, Tri-Secret Secure customer-managed keys, SOC 2 Type II.',
    rating: 94
  },
  {
    id: 'datadog',
    name: 'Datadog Observability',
    domain: 'datadoghq.com',
    industry: 'Cloud Monitoring & APM',
    tier: 'Tier 2 (High)',
    tierColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    icon: BarChart3,
    description: 'Infrastructure telemetry, distributed tracing, SAML 2.0 SSO, ISO 27001 certified.',
    rating: 91
  },
  {
    id: 'stripe',
    name: 'Stripe Payments',
    domain: 'stripe.com',
    industry: 'Financial Infrastructure',
    tier: 'Tier 1 (Critical)',
    tierColor: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    icon: CreditCard,
    description: 'PCI-DSS Level 1 tokenized vaults, Zero Trust hardware keys, automated CSIRT response.',
    rating: 98
  }
];

export default function VendorSelector({ selectedVendor, onSelectVendor, onAssess, isLoading }) {
  const [isCustom, setIsCustom] = useState(false);
  const [customName, setCustomName] = useState('');
  const [customDomain, setCustomDomain] = useState('');
  const [customIndustry, setCustomIndustry] = useState('SaaS / Cloud Software');
  const [customTier, setCustomTier] = useState('Tier 2 (High)');
  const [customAttestation, setCustomAttestation] = useState('');

  const handleBenchmarkSelect = (v) => {
    setIsCustom(false);
    onSelectVendor({ id: v.id, name: v.name, domain: v.domain });
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (!customName.trim()) return;
    const vendorData = {
      name: customName.trim(),
      domain: customDomain.trim() || 'custom-vendor.io',
      industry: customIndustry,
      data_tier: customTier,
      documents_text: customAttestation.trim()
    };
    onSelectVendor(vendorData);
  };

  return (
    <div className="w-full max-w-5xl mx-auto mb-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Building2 className="w-5 h-5 text-trust-accent" />
            Vendor Security Assessment Target
          </h2>
          <p className="text-xs text-gray-400">
            Select an enterprise benchmark vendor or enter a custom vendor profile to initiate multi-agent assessment
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsCustom(!isCustom)}
          className="text-xs font-mono px-3 py-1.5 rounded-lg border border-trust-border/50 bg-trust-surface/60 hover:bg-trust-surface text-trust-accent hover:text-white transition-all flex items-center gap-1.5"
        >
          <Sliders className="w-3.5 h-3.5" />
          {isCustom ? 'Use Benchmark Vendors' : '+ Custom Vendor Profile'}
        </button>
      </div>

      {!isCustom ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {BENCHMARK_VENDORS.map((v) => {
            const isSelected = selectedVendor?.id === v.id;
            const IconComponent = v.icon;
            return (
              <motion.div
                key={v.id}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleBenchmarkSelect(v)}
                className={`p-4 rounded-xl cursor-pointer transition-all border text-left flex flex-col justify-between ${
                  isSelected
                    ? 'bg-trust-accent/10 border-trust-accent shadow-lg shadow-trust-accent/10'
                    : 'bg-trust-card/60 hover:bg-trust-card border-trust-border/40 hover:border-trust-border'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between mb-2">
                    <div className="p-2 rounded-lg bg-trust-surface border border-trust-border/30 text-trust-accent">
                      <IconComponent className="w-5 h-5" />
                    </div>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${v.tierColor}`}>
                      {v.tier}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-0.5">{v.name}</h3>
                  <p className="text-xs text-gray-400 font-mono mb-2">{v.domain}</p>
                  <p className="text-xs text-gray-300 leading-relaxed mb-3">{v.description}</p>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-trust-border/20 text-xs">
                  <span className="text-gray-400 font-mono">Security Rating:</span>
                  <span className="font-semibold text-emerald-400 font-mono">{v.rating}/100</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <motion.form
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleCustomSubmit}
          className="p-5 rounded-xl border border-trust-border/60 bg-trust-card/80 backdrop-blur-md"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-mono text-gray-300 mb-1">Vendor Legal Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Acme Corp"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full text-xs font-mono px-3 py-2 rounded-lg bg-trust-surface border border-trust-border/60 text-white focus:outline-none focus:border-trust-accent"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-gray-300 mb-1">Vendor Domain</label>
              <input
                type="text"
                placeholder="e.g. acme.com"
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
                className="w-full text-xs font-mono px-3 py-2 rounded-lg bg-trust-surface border border-trust-border/60 text-white focus:outline-none focus:border-trust-accent"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-gray-300 mb-1">Industry Classification</label>
              <input
                type="text"
                value={customIndustry}
                onChange={(e) => setCustomIndustry(e.target.value)}
                className="w-full text-xs font-mono px-3 py-2 rounded-lg bg-trust-surface border border-trust-border/60 text-white focus:outline-none focus:border-trust-accent"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-gray-300 mb-1">Data Criticality Tier</label>
              <select
                value={customTier}
                onChange={(e) => setCustomTier(e.target.value)}
                className="w-full text-xs font-mono px-3 py-2 rounded-lg bg-trust-surface border border-trust-border/60 text-white focus:outline-none focus:border-trust-accent"
              >
                <option value="Tier 1 (Critical)">Tier 1 (Critical) — PII / Financial Data</option>
                <option value="Tier 2 (High)">Tier 2 (High) — Internal Operational Data</option>
                <option value="Tier 3 (Medium)">Tier 3 (Medium) — Non-Confidential Data</option>
              </select>
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-xs font-mono text-gray-300 mb-1">
              Vendor Self-Attestations or Policy Snippets (optional)
            </label>
            <textarea
              rows={3}
              placeholder="e.g. encryption_at_rest: AES-256 with KMS keys&#10;access_control: MFA mandatory for all engineers"
              value={customAttestation}
              onChange={(e) => setCustomAttestation(e.target.value)}
              className="w-full text-xs font-mono p-3 rounded-lg bg-trust-surface border border-trust-border/60 text-white focus:outline-none focus:border-trust-accent resize-none"
            />
          </div>
          <button
            type="submit"
            className="text-xs font-semibold px-4 py-2 rounded-lg bg-trust-accent text-white hover:bg-trust-accent/90 transition-all flex items-center gap-1.5"
          >
            Apply Custom Vendor Profile
          </button>
        </motion.form>
      )}

      <div className="mt-4 flex justify-end">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onAssess}
          disabled={isLoading || !selectedVendor}
          className={`px-6 py-2.5 rounded-xl font-semibold text-xs tracking-wide flex items-center gap-2 shadow-lg transition-all ${
            isLoading || !selectedVendor
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-trust-accent to-cyan-500 text-white hover:shadow-cyan-500/20'
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Multi-Agent Swarm Orchestrating...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" />
              <span>Execute Multi-Agent Assessment</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </>
          )}
        </motion.button>
      </div>
    </div>
  );
}
