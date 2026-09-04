import React from 'react';
import { ShieldCheck, Sparkles, BookOpen, Github } from 'lucide-react';

export default function Header({ onOpenArchitecture, isHealthy }) {
  return (
    <header className="border-b border-trust-border/80 bg-trust-bg/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-trust-accent to-trust-cyan flex items-center justify-center shadow-lg shadow-trust-accent/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">TrustLens</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-trust-accent/20 text-trust-accent border border-trust-accent/30">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-trust-muted leading-none hidden sm:block">AI Reliability & RAG Verification</p>
          </div>
        </div>

        {/* Engine status indicator & actions */}
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded-full bg-trust-surface border border-trust-border text-xs text-gray-300">
            <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-trust-green animate-pulse' : 'bg-trust-amber'}`}></span>
            <span className="font-mono text-[11px]">{isHealthy ? 'Engine Online' : 'Engine Ready'}</span>
          </div>

          <button
            onClick={onOpenArchitecture}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-trust-card hover:bg-trust-border/50 border border-trust-border text-xs text-gray-200 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5 text-trust-cyan" />
            <span>Architecture</span>
          </button>

          <a
            href="https://github.com/TopoVista/trustlens"
            target="_blank"
            rel="noopener noreferrer"
            className="text-trust-muted hover:text-white transition-colors p-1.5"
            title="GitHub Repository"
          >
            <Github className="w-4 h-4" />
          </a>
        </div>
      </div>
    </header>
  );
}
