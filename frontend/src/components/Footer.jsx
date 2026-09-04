import React from 'react';
import { Shield, ExternalLink, Cpu } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="mt-20 border-t border-trust-border/80 bg-trust-surface/40 py-8">
      <div className="max-w-7xl mx-auto px-4 text-center sm:flex sm:items-center sm:justify-between text-xs text-trust-muted font-mono">
        <div className="flex items-center justify-center space-x-2 mb-3 sm:mb-0">
          <Shield className="w-4 h-4 text-trust-accent" />
          <span>TrustLens AI Reliability Platform</span>
          <span>•</span>
          <span className="text-gray-400">Production Demo</span>
        </div>

        <div className="flex items-center justify-center space-x-4">
          <span className="flex items-center space-x-1">
            <Cpu className="w-3.5 h-3.5 text-trust-cyan" />
            <span>MiniLM2-L6 NLI</span>
          </span>
          <span>•</span>
          <span>OpenAI Grounded Generation</span>
          <span>•</span>
          <a
            href="https://github.com/TopoVista/trustlens"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors inline-flex items-center space-x-1"
          >
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </footer>
  );
}
