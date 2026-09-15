'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Copy, Check, Terminal, Shield, Sparkles, ArrowRight, ExternalLink } from 'lucide-react';

export default function Hero() {
  const [os, setOs] = useState<'win' | 'unix'>('win');
  const [copied, setCopied] = useState(false);

  const installCommands = {
    win: 'irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex',
    unix: 'curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash',
  };

  const currentCommand = installCommands[os];

  const handleCopy = () => {
    navigator.clipboard.writeText(currentCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <section style={{
      position: 'relative',
      paddingTop: '140px',
      paddingBottom: '80px',
      overflow: 'hidden',
    }}>
      <div style={{
        maxWidth: '1100px',
        margin: '0 auto',
        padding: '0 24px',
        textAlign: 'center',
        position: 'relative',
        zIndex: 1,
      }}>
        {/* Hero Title */}
        <h1 style={{
          fontSize: 'clamp(2.5rem, 5.5vw, 4.2rem)',
          lineHeight: 1.12,
          fontWeight: 800,
          letterSpacing: '-0.03em',
          maxWidth: '960px',
          margin: '0 auto 24px',
        }}>
          Deep Code Comprehension,{' '}
          <span style={{
            background: 'linear-gradient(135deg, #fbbf24 0%, #f97316 45%, #c084fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'inline-block',
          }}>
            Zero Truncation
          </span>,{' '}
          True BYOK Freedom.
        </h1>

        {/* Hero Subtitle */}
        <p style={{
          fontSize: 'clamp(1.05rem, 2vw, 1.25rem)',
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          maxWidth: '740px',
          margin: '0 auto 40px',
          fontWeight: 400,
        }}>
          A minimalist terminal agent built for developers and security auditors. 
          Audit architecture, detect vulnerabilities with DeepSeek V4 & Claude 3.5, 
          and retain full control with strict <strong style={{ color: 'var(--moon-gold)' }}>Read-Only Mode</strong>.
        </p>

        {/* Install Box */}
        <div style={{
          maxWidth: '680px',
          margin: '0 auto 36px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '14px',
          padding: '8px',
        }}>
          {/* OS Switcher Tabs */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 12px 10px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            fontSize: '0.82rem',
          }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setOs('win')}
                style={{
                  padding: '4px 12px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  transition: 'all 0.2s',
                  background: os === 'win' ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
                  color: os === 'win' ? 'var(--moon-amber)' : 'var(--text-muted)',
                  border: os === 'win' ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid transparent',
                }}
              >
                Windows (PowerShell)
              </button>
              <button
                onClick={() => setOs('unix')}
                style={{
                  padding: '4px 12px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  transition: 'all 0.2s',
                  background: os === 'unix' ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                  color: os === 'unix' ? 'var(--lunar-violet)' : 'var(--text-muted)',
                  border: os === 'unix' ? '1px solid rgba(139, 92, 246, 0.3)' : '1px solid transparent',
                }}
              >
                macOS / Linux (Bash)
              </button>
            </div>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
              1-step installer
            </span>
          </div>

          {/* Command display & Copy button */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 14px',
            gap: '12px',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              overflowX: 'auto',
              whiteSpace: 'nowrap',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.88rem',
              color: '#f1f5f9',
            }}>
              <span style={{ color: os === 'win' ? 'var(--moon-amber)' : 'var(--lunar-violet)', userSelect: 'none' }}>
                $
              </span>
              <span style={{ userSelect: 'all' }}>{currentCommand}</span>
            </div>

            <button
              onClick={handleCopy}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                flexShrink: 0,
                transition: 'all 0.2s',
                background: copied ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 255, 255, 0.08)',
                color: copied ? '#4ade80' : 'var(--text-primary)',
                border: copied ? '1px solid rgba(34, 197, 94, 0.4)' : '1px solid rgba(255, 255, 255, 0.12)',
              }}
              title="Copy to clipboard"
            >
              {copied ? (
                <>
                  <Check size={14} />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Action CTAs */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          flexWrap: 'wrap',
          marginBottom: '50px',
        }}>
          <Link href="/docs" className="btn-primary" style={{ padding: '12px 28px', fontSize: '1rem' }}>
            <Terminal size={18} />
            Explore Documentation
            <ArrowRight size={16} />
          </Link>

          <a
            href="https://github.com/snui1s/losna-cli"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
            style={{ padding: '12px 24px', fontSize: '1rem' }}
          >
            <Shield size={18} style={{ color: 'var(--lunar-violet)' }} />
            Audit Safety Model
            <ExternalLink size={14} style={{ opacity: 0.6 }} />
          </a>
        </div>

        {/* Quick Highlights Strip */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          maxWidth: '900px',
          margin: '0 auto',
        }}>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: 'var(--moon-amber)', fontWeight: 700, fontSize: '1.25rem', marginBottom: '2px' }}>0% Markup</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Bring Your Own Key (OpenRouter). Zero token tax.</div>
          </div>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: 'var(--lunar-violet)', fontWeight: 700, fontSize: '1.25rem', marginBottom: '2px' }}>Read-Only Guard</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Strict schema & runtime locks for safe production audits.</div>
          </div>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: 'var(--moon-gold)', fontWeight: 700, fontSize: '1.25rem', marginBottom: '2px' }}>SQLite Memory</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Multi-session tabs with auto-compaction & rule pinning.</div>
          </div>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: '#38bdf8', fontWeight: 700, fontSize: '1.25rem', marginBottom: '2px' }}>Web Intelligence</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Trafilatura article extraction & live Tavily search.</div>
          </div>
        </div>
      </div>
    </section>
  );
}
