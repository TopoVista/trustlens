import React, { useEffect, useState } from 'react';
import { ArrowUpRight, MoveUpRight, X } from 'lucide-react';
import { resolveGuideTarget } from '../../guide/uiManifest.js';

export default function GuideOverlay({ targetId, onClose, onAct }) {
  const [rect, setRect] = useState(null);
  const [placement, setPlacement] = useState('below');
  const target = resolveGuideTarget(targetId);

  useEffect(() => {
    if (!target) return undefined;
    const update = () => {
      const element = document.querySelector(target.selector);
      const nextRect = element ? element.getBoundingClientRect() : null;
      setRect(nextRect);
      if (nextRect) setPlacement(nextRect.bottom + 174 > window.innerHeight ? 'above' : 'below');
    };
    update();
    window.addEventListener('resize', update);
    window.addEventListener('scroll', update, true);
    return () => {
      window.removeEventListener('resize', update);
      window.removeEventListener('scroll', update, true);
    };
  }, [target]);

  if (!target || !rect) return null;
  const cardTop = placement === 'below'
    ? Math.min(window.innerHeight - 164, rect.bottom + 22)
    : Math.max(12, rect.top - 174);
  const cardLeft = Math.max(12, Math.min(window.innerWidth - 300, rect.left));

  return (
    <div className="tl-guide-overlay" role="dialog" aria-label="TrustLens guide">
      <div className="tl-guide-spotlight" style={{ top: rect.top - 6, left: rect.left - 6, width: rect.width + 12, height: rect.height + 12 }} />
      <div className={`tl-guide-card is-${placement}`} style={{ top: cardTop, left: cardLeft }}>
        <span className="tl-guide-connector" aria-hidden="true"><MoveUpRight className="h-4 w-4" /></span>
        <button onClick={onClose} aria-label="Close guide"><X className="h-4 w-4" /></button>
        <p className="editorial-kicker">TrustLens guide</p>
        <strong>{target.label}</strong>
        <p>This highlighted control is the next step. You remain in control of every action.</p>
        <div>
          <span className="tl-guide-target-note">Pointing to control</span>
          <button onClick={() => onAct(target)}><ArrowUpRight className="h-3.5 w-3.5" />Take me there</button>
        </div>
      </div>
    </div>
  );
}
