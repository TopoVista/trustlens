import React, { useState } from 'react';
import { 
  ShieldCheck, 
  PlusCircle, 
  Sliders, 
  Lock, 
  Sparkles, 
  CheckCircle2, 
  Trash2,
  Bookmark
} from 'lucide-react';

export default function SemanticRulesManager({
  rules = [],
  onAddRule,
  activeWorkspace
}) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [ruleType, setRuleType] = useState('AUTHORITY_POLICY');
  const [ruleKey, setRuleKey] = useState('');
  const [ruleValue, setRuleValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ruleKey.trim() || !ruleValue.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onAddRule({
        rule_type: ruleType,
        rule_key: ruleKey.trim(),
        rule_value: ruleValue.trim()
      });
      setRuleKey('');
      setRuleValue('');
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to add semantic rule:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 my-6 space-y-4">
      <div className="p-6 rounded-2xl bg-trust-card border border-trust-border/80 shadow-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-trust-border/60">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-trust-accent" />
              Semantic Memory Rules & Verification Policies
            </h3>
            <p className="text-xs text-trust-muted font-mono">
              Deterministic guidelines enforced by the Analysis Planner & Specialists
            </p>
          </div>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-trust-accent hover:bg-trust-accent-hover text-white text-xs font-semibold shadow-md shadow-trust-accent/25 transition-all"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Add Verification Rule</span>
          </button>
        </div>

        {/* Add Rule Inline Form */}
        {showAddForm && (
          <form onSubmit={handleSubmit} className="p-4 mb-4 rounded-xl bg-trust-surface border border-trust-border space-y-3 animate-in fade-in">
            <h4 className="text-xs font-bold text-white">Define New Verification Policy</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-mono text-gray-400 mb-1">Rule Type</label>
                <select
                  value={ruleType}
                  onChange={(e) => setRuleType(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-trust-card border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                >
                  <option value="AUTHORITY_POLICY">AUTHORITY_POLICY</option>
                  <option value="CONTRADICTION_POLICY">CONTRADICTION_POLICY</option>
                  <option value="CITATION_CONSTRAINT">CITATION_CONSTRAINT</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-gray-400 mb-1">Target Entity / Topic</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q3 Financials, Launch Schedule"
                  value={ruleKey}
                  onChange={(e) => setRuleKey(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-trust-card border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-gray-400 mb-1">Policy Directive</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Treat official audit report as ground truth"
                  value={ruleValue}
                  onChange={(e) => setRuleValue(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-trust-card border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-3 py-1.5 text-xs text-gray-400 hover:text-white rounded-xl bg-trust-card border border-trust-border"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-1.5 text-xs font-semibold text-white rounded-xl bg-trust-accent hover:bg-trust-accent-hover"
              >
                {isSubmitting ? 'Saving...' : 'Save Rule'}
              </button>
            </div>
          </form>
        )}

        {/* Existing Rules List */}
        {rules.length === 0 ? (
          <p className="text-xs text-trust-muted font-mono py-6 text-center">
            No active semantic rules defined in this workspace. Default verification policies apply.
          </p>
        ) : (
          <div className="grid gap-2.5">
            {rules.map((r, idx) => (
              <div
                key={r.id || idx}
                className="p-3.5 rounded-xl bg-trust-surface/70 border border-trust-border flex items-center justify-between gap-3"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-1.5 rounded-lg bg-trust-accent/20 border border-trust-accent/30 text-trust-accent">
                    <Bookmark className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-white">{r.rule_key}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-trust-card border border-trust-border text-trust-cyan">
                        {r.rule_type}
                      </span>
                    </div>
                    <p className="text-xs text-gray-300 mt-0.5">{r.rule_value}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-trust-green bg-trust-green-bg px-2 py-0.5 rounded border border-trust-green/30">
                    ACTIVE
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
