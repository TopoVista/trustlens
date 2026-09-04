import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Send, Bot, User, Bookmark, Loader2, Sparkles } from 'lucide-react';
import { askVendorQuestion } from '../api';

export default function InteractiveQABot({ vendorProfile }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Hello! I am the User Q&A Agent. Ask me any question about ${vendorProfile?.name || 'this vendor'}'s security controls, encryption, compliance frameworks, or incident response protocols.`,
      citations: []
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const sampleQuestions = [
    'What encryption standards are enforced for data at rest?',
    'Does the vendor comply with SOC 2 Type II or ISO 27001?',
    'What are the disaster recovery and multi-region failover policies?'
  ];

  const handleSend = async (queryText = question) => {
    const q = queryText.trim();
    if (!q || isLoading) return;

    setQuestion('');
    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setIsLoading(true);

    try {
      const response = await askVendorQuestion(vendorProfile, q);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: response.answer,
          citations: response.citations || []
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Error retrieving answer: ${err.message}`,
          citations: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full bg-trust-card border border-trust-border rounded-2xl p-6 shadow-xl backdrop-blur-md mb-8">
      <div className="flex items-center justify-between gap-4 mb-4 pb-4 border-b border-trust-border/40">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Interactive Vendor Q&A Agent
            </h3>
            <p className="text-xs text-gray-400">
              Direct evidence-grounded conversational inquiry for risk analysts
            </p>
          </div>
        </div>

        <div className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-trust-surface border border-trust-border/40 text-gray-300 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-trust-accent" />
          <span>Vendor Context: {vendorProfile?.name || 'Active Vendor'}</span>
        </div>
      </div>

      {/* Suggested prompts */}
      <div className="flex flex-wrap gap-2 mb-4">
        {sampleQuestions.map((sq, i) => (
          <button
            key={i}
            onClick={() => handleSend(sq)}
            className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-trust-surface/60 hover:bg-trust-surface border border-trust-border/40 text-gray-300 hover:text-white transition-all text-left"
          >
            "{sq}"
          </button>
        ))}
      </div>

      {/* Messages Feed */}
      <div className="max-h-[300px] overflow-y-auto space-y-3 p-3 rounded-xl bg-black/20 border border-trust-border/30 mb-4 font-sans text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-2.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.role === 'assistant' && (
              <div className="w-6 h-6 rounded-lg bg-trust-surface border border-trust-border flex items-center justify-center text-trust-accent shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}
            <div
              className={`p-3 rounded-xl max-w-[85%] leading-relaxed ${
                m.role === 'user'
                  ? 'bg-trust-accent text-white font-medium ml-8'
                  : 'bg-trust-surface/80 text-gray-200 border border-trust-border/40'
              }`}
            >
              <p>{m.text}</p>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-trust-border/30 flex flex-wrap gap-1.5">
                  {m.citations.map((c, ci) => (
                    <span
                      key={ci}
                      className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-black/30 text-trust-accent border border-trust-accent/20"
                    >
                      <Bookmark className="w-2.5 h-2.5" />
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {m.role === 'user' && (
              <div className="w-6 h-6 rounded-lg bg-trust-accent/30 border border-trust-accent flex items-center justify-center text-white shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-gray-400 font-mono py-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-trust-accent" />
            <span>Consulting vendor disclosures and vector knowledgebase...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={`Ask about ${vendorProfile?.name || 'vendor'} security, controls, or certifications...`}
          className="flex-1 text-xs font-mono px-3.5 py-2.5 rounded-xl bg-trust-surface border border-trust-border/60 text-white placeholder-gray-500 focus:outline-none focus:border-trust-accent"
        />
        <button
          type="submit"
          disabled={isLoading || !question.trim()}
          className="p-2.5 rounded-xl bg-trust-accent hover:bg-trust-accent/90 disabled:bg-gray-700 text-white transition-all"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
