import React, { useMemo, useState } from 'react';
import { HelpCircle, MessageCircle, Send, X } from 'lucide-react';
import { guideReply, resolveGuideTarget } from '../../guide/uiManifest.js';
import GuideOverlay from './GuideOverlay.jsx';

export default function GuideChat({ context, onAction }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([{ role: 'guide', text: 'Need a hand? Ask how to add evidence, verify a claim, or explore the map.' }]);
  const [target, setTarget] = useState(null);
  const submit = (event) => {
    event.preventDefault();
    if (!question.trim()) return;
    const reply = guideReply(question, context);
    setMessages((current) => [...current, { role: 'user', text: question }, { role: 'guide', ...reply }]);
    setQuestion('');
  };
  const act = (targetInfo) => { onAction?.(targetInfo.action); setTarget(null); setOpen(false); };
  return <><button className="tl-guide-launcher" onClick={() => setOpen(true)} aria-label="Open TrustLens guide"><HelpCircle className="h-4 w-4" />Guide</button>{open && <aside className="tl-guide-chat" aria-label="TrustLens guide chat"><header><div><MessageCircle className="h-4 w-4" /><strong>TrustLens guide</strong></div><button onClick={() => setOpen(false)} aria-label="Close guide"><X className="h-4 w-4" /></button></header><div className="tl-guide-messages">{messages.map((message, index) => <div key={index} className={`is-${message.role}`}><p>{message.text}</p>{message.target && resolveGuideTarget(message.target) && <button onClick={() => setTarget(message.target)}>Show me {resolveGuideTarget(message.target).label}</button>}</div>)}</div><form onSubmit={submit}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="How do I inspect this?" /><button aria-label="Send guide question"><Send className="h-4 w-4" /></button></form></aside>}<GuideOverlay targetId={target} onClose={() => setTarget(null)} onAct={act} /></>;
}
