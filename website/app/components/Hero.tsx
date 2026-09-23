'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Copy, Check, Terminal, Shield, ArrowRight, ExternalLink } from 'lucide-react';
import GithubIcon from './icons/GithubIcon';

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
      paddingTop: '135px',
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
        {/* Version & Tagline Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          borderRadius: '9999px',
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          fontSize: '0.82rem',
          color: 'var(--moon-amber)',
          marginBottom: '26px',
        }}>
          <span style={{ fontWeight: 600 }}>🌒 Losna CLI</span>
          <span style={{ opacity: 0.5 }}>•</span>
          <span style={{ color: 'var(--text-secondary)' }}>Built for Long Conversations (And It Codes Too)</span>
        </div>

        {/* Hero Title */}
        <h1 style={{
          fontSize: 'clamp(2.5rem, 5.5vw, 4.2rem)',
          lineHeight: 1.15,
          fontWeight: 800,
          letterSpacing: '-0.03em',
          maxWidth: '960px',
          margin: '0 auto 24px',
        }}>
          Built for{' '}
          <span style={{
            background: 'linear-gradient(135deg, #fbbf24 0%, #f97316 45%, #c084fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'inline-block',
          }}>
            Long Conversations
          </span>
          .<br />
          <span style={{ fontSize: '0.62em', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginTop: '6px' }}>
            (It Just Happens to Code Too.)
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p style={{
          fontSize: 'clamp(1.05rem, 2vw, 1.25rem)',
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          maxWidth: '680px',
          margin: '0 auto 36px',
          fontWeight: 400,
        }}>
          A terminal AI companion built to talk for hours without losing context — backed by persistent SQLite memory and prompt caching. And when you need to code, the tools are already there.
        </p>

        {/* Install Box */}
        <div style={{
          maxWidth: '680px',
          margin: '0 auto 16px',
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
              Self-contained in ~/.losna
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

        {/* Install note */}
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '40px', fontFamily: 'var(--font-mono)' }}>
          Launch anytime in any directory by typing <code style={{ color: 'var(--moon-amber)' }}>losna</code>
        </p>

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
            <GithubIcon size={18} />
            GitHub Repository
            <ExternalLink size={14} style={{ opacity: 0.6 }} />
          </a>
        </div>

        {/* Quick Highlights Strip */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          maxWidth: '960px',
          margin: '0 auto',
        }}>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: 'var(--moon-amber)', fontWeight: 700, fontSize: '1.2rem', marginBottom: '2px' }}>Marathon Sessions</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Auto-compaction summarizes earlier turns so conversations never break.</div>
          </div>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: 'var(--moon-gold)', fontWeight: 700, fontSize: '1.2rem', marginBottom: '2px' }}>SQLite Memory</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Multi-session history in agent_data.db with /pin immortal memory.</div>
          </div>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: 'var(--lunar-violet)', fontWeight: 700, fontSize: '1.2rem', marginBottom: '2px' }}>Prompt Caching</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>OpenRouter prefix caching cuts token cost by ~90% for endless chats.</div>
          </div>
          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left', borderRadius: '12px' }}>
            <div style={{ color: '#38bdf8', fontWeight: 700, fontSize: '1.2rem', marginBottom: '2px' }}>And It Codes Too</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>@file mentions, file editing, shell commands & /readonly mode on demand.</div>
          </div>
        </div>
      </div>
    </section>
  );
}
