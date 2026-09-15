'use client';

import React from 'react';
import { Key, ShieldAlert, Database, Globe, Cpu, Puzzle, Sparkles } from 'lucide-react';

export default function BentoGrid() {
  return (
    <section id="features" style={{
      padding: '80px 24px',
      maxWidth: '1200px',
      margin: '0 auto',
      position: 'relative',
    }}>
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <h2 style={{ fontSize: 'clamp(1.8rem, 3.5vw, 2.6rem)', marginBottom: '14px' }}>
          Built for Deep Work, Not Shallow Chat
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '620px', margin: '0 auto', fontSize: '1.05rem' }}>
          Every feature in Losna CLI is engineered to give engineers full control, safety, and deep context when analyzing complex systems.
        </p>
      </div>

      {/* Bento Grid layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(12, 1fr)',
        gap: '20px',
      }}>
        {/* Card 1: BYOK (Span 7) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 7',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--moon-amber)',
              marginBottom: '20px',
            }}>
              <Key size={22} />
            </div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>
              Bring Your Own Key (BYOK) & Zero Token Markup
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '20px' }}>
              Connect directly to OpenRouter. No token taxes, no rate-limiting middleman, and no black-box routing. 
              Switch effortlessly between DeepSeek V3, DeepSeek R1, Claude 3.5 Sonnet, and GPT-4o via <code style={{ color: 'var(--moon-gold)' }}>/model</code>.
            </p>
          </div>

          <div style={{
            background: 'rgba(0, 0, 0, 0.35)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
          }}>
            <span>~/.losnarc local config</span>
            <span style={{ color: '#4ade80' }}>100% Private to your machine</span>
          </div>
        </div>

        {/* Card 2: Read-Only Safety (Span 5) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 5',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(139, 92, 246, 0.15)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--lunar-violet)',
              marginBottom: '20px',
            }}>
              <ShieldAlert size={22} />
            </div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>
              Strict Read-Only Mode
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
              Safe for live auditing and production codebases. File writing, edits, and deletions are blocked at both schema definition and runtime levels. Destructive commands trigger an explicit <code style={{ color: '#fbbf24' }}>(y/n)</code> gate.
            </p>
          </div>

          <div style={{
            marginTop: '20px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#fca5a5',
            fontSize: '0.82rem',
            fontFamily: 'var(--font-mono)',
          }}>
            🔒 Write operations completely neutralized
          </div>
        </div>

        {/* Card 3: SQLite Multi-Session & Auto-Compaction (Span 5) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 5',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--moon-amber)',
              marginBottom: '20px',
            }}>
              <Database size={22} />
            </div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>
              Multi-Session SQLite Persistence
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
              Independent chat sessions backed by local <code style={{ color: '#fbbf24' }}>agent_data.db</code>. 
              Automatically compresses long conversation histories to preserve tokens while keeping critical memory intact.
            </p>
          </div>

          <div style={{
            marginTop: '20px',
            display: 'flex',
            gap: '8px',
            flexWrap: 'wrap',
          }}>
            <span className="badge-purple">/new session</span>
            <span className="badge-purple">/switch</span>
            <span className="badge-purple">/pin rule</span>
          </div>
        </div>

        {/* Card 4: Web Intelligence & Trafilatura (Span 7) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 7',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8',
              marginBottom: '20px',
            }}>
              <Globe size={22} />
            </div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>
              Trafilatura Article Scraper & Tavily Search
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '16px' }}>
              Feed documentation URLs, RFC specs, or technical blog posts directly to the agent using <code style={{ color: '#38bdf8' }}>read_web_page</code>. It automatically strips ads, navigation bars, and cookie banners to extract pure markdown.
            </p>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid var(--border-subtle)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.82rem',
          }}>
            <span style={{ color: '#38bdf8' }}>→</span>
            <span style={{ color: 'var(--text-secondary)' }}>Clean markdown extracted from any web URL in milliseconds</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        @media (max-width: 900px) {
          .glass-panel {
            grid-column: span 12 !important;
          }
        }
      `}</style>
    </section>
  );
}
