import React, { useEffect, useState } from 'react';
import { ArrowUpRight, X } from 'lucide-react';
import { resolveGuideTarget } from '../../guide/uiManifest.js';

export default function GuideOverlay({ targetId, onClose, onAct }) {
  const [rect, setRect] = useState(null);
  const target = resolveGuideTarget(targetId);
  useEffect(() => {
    if (!target) return undefined;
    const update = () => {
      const element = document.querySelector(target.selector);
      setRect(element ? element.getBoundingClientRect() : null);
    };
    update();
    window.addEventListener('resize', update);
    window.addEventListener('scroll', update, true);
    return () => { window.removeEventListener('resize', update); window.removeEventListener('scroll', update, true); };
  }, [target]);
  if (!target || !rect) return null;
  return <div className="tl-guide-overlay" role="dialog" aria-label="TrustLens guide"><div className="tl-guide-spotlight" style={{ top: rect.top - 6, left: rect.left - 6, width: rect.width + 12, height: rect.height + 12 }} /><div className="tl-guide-card" style={{ top: Math.min(window.innerHeight - 150, rect.bottom + 14), left: Math.max(12, Math.min(window.innerWidth - 300, rect.left)) }}><button onClick={onClose} aria-label="Close guide"><X className="h-4 w-4" /></button><p className="editorial-kicker">TrustLens guide</p><strong>{target.label}</strong><p>This is the control you need. You remain in control of every action.</p><div><span className="tl-guide-arrow">↗</span><button onClick={() => onAct(target)}><ArrowUpRight className="h-3.5 w-3.5" />Take me there</button></div></div></div>;
}
