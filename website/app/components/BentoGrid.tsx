'use client';

import React from 'react';
import { Key, ShieldAlert, Database, Globe, Cpu, Puzzle, AlertTriangle, FileCode, CheckCircle2, Languages, Clock, Sparkles } from 'lucide-react';

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
          Built to Talk for Hours — And Act When Asked
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '680px', margin: '0 auto', fontSize: '1.05rem', lineHeight: 1.6 }}>
          Most terminal AI tools lose their memory after 10 messages. Losna CLI is architected for marathon conversations that stay sharp all day, with a full set of workspace and coding tools ready whenever you need them.
        </p>
      </div>

      {/* Bento Grid layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(12, 1fr)',
        gap: '20px',
      }}>
        {/* Card 1: Memory & Compaction (Span 7) */}
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
              <Database size={22} />
            </div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>
              Chat That Never Forgets: SQLite Memory & Auto-Compaction
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '20px' }}>
              Have deep, winding conversations across hours or days. Losna automatically compacts message history into structured context summaries while saving facts into local SQLite (<code style={{ color: '#fbbf24' }}>~/.losna/agent_data.db</code>). Pin eternal rules with <code style={{ color: 'var(--moon-gold)' }}>/pin</code> that persist across restarts.
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
            <span>Multi-Turn Summary + Pinned Memory</span>
            <span style={{ color: '#4ade80' }}>Zero context amnesia</span>
          </div>
        </div>

        {/* Card 2: Prompt Caching & BYOK (Span 5) */}
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
              <Clock size={22} />
            </div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>
              Prompt Caching: Marathon Chats on a Budget
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
              Connect directly via OpenRouter. Static personas, project readmes, and pinned memories are prefix-cached for up to <strong style={{ color: 'var(--moon-gold)' }}>90% token discounts</strong>. Chat all day without worrying about API bills.
            </p>
          </div>

          <div style={{
            marginTop: '20px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(139, 92, 246, 0.1)',
            border: '1px solid rgba(139, 92, 246, 0.25)',
            color: '#c4b5fd',
            fontSize: '0.82rem',
            fontFamily: 'var(--font-mono)',
          }}>
            ⚡ Ephemeral Cache Control: 90% cheaper, sub-second TTFT
          </div>
        </div>

        {/* Card 3: Natural Language & Zero Bleed (Span 4) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 4',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'rgba(34, 197, 94, 0.12)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#4ade80',
              marginBottom: '18px',
            }}>
              <Languages size={20} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
              Natural Flow, Zero Bleed
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.55 }}>
              Strict language enforcement guarantees natural, fluent Thai and English. Strictly prevents random Chinese characters or thinking tokens from bleeding into your conversations.
            </p>
          </div>

          <div style={{
            marginTop: '16px',
            display: 'flex',
            gap: '6px',
            flexWrap: 'wrap',
          }}>
            <span className="badge-purple">100% Fluent Thai</span>
            <span className="badge-purple">Zero Chinese Bleed</span>
          </div>
        </div>

        {/* Card 4: And It Codes Too (Span 4) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 4',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8',
              marginBottom: '18px',
            }}>
              <FileCode size={20} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
              And It Codes Too
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.55 }}>
              Ready to code? Full tool capabilities: file edits, terminal commands with safety gates, <code style={{ color: '#38bdf8' }}>/readonly</code> mode for safe discussions, and diff reviews.
            </p>
          </div>

          <div style={{
            marginTop: '16px',
            display: 'flex',
            gap: '6px',
            flexWrap: 'wrap',
          }}>
            <span className="badge-purple">/readonly</span>
            <span className="badge-purple">Interactive (y/n)</span>
            <span className="badge-purple">File Tools</span>
          </div>
        </div>

        {/* Card 5: Live Web Research & Trafilatura (Span 4) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 4',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--moon-amber)',
              marginBottom: '18px',
            }}>
              <Globe size={20} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
              Trafilatura & Live Search
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.55 }}>
              Fetch RFCs, docs, and news on the fly with <code style={{ color: '#fbbf24' }}>/search</code> via Tavily. Trafilatura strips ads and popups to bring pure markdown straight into the conversation.
            </p>
          </div>

          <div style={{
            marginTop: '16px',
            display: 'flex',
            gap: '6px',
            flexWrap: 'wrap',
          }}>
            <span className="badge-purple">/search</span>
            <span className="badge-purple">read_web_page</span>
            <span className="badge-purple">Ad-Free Markdown</span>
          </div>
        </div>

        {/* Card 6: Smart @file Mentions & GitHub Plugin System (Span 12) */}
        <div className="glass-panel" style={{
          gridColumn: 'span 12',
          padding: '30px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '24px',
        }}>
          <div style={{ maxWidth: '650px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: 'rgba(34, 197, 94, 0.12)',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#4ade80',
              }}>
                <Puzzle size={18} />
              </div>
              <h3 style={{ fontSize: '1.25rem' }}>
                Smart <code style={{ color: 'var(--moon-amber)' }}>@file</code> Context & GitHub-Powered Skill Plugins
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.6 }}>
              Mention any file with <code style={{ color: '#fbbf24' }}>@path/to/file</code> directly in your prompt to inject its code into context without manual copy-pasting. 
              Extend agent capabilities with custom markdown skills in <code style={{ color: '#fff' }}>./skills/</code> or install open-source skills straight from GitHub using <code style={{ color: '#4ade80' }}>/plugin add &lt;url&gt;</code>.
            </p>
          </div>

          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
          }}>
            <div style={{
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '10px 14px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
            }}>
              @src/agent/logger.py review
            </div>
            <div style={{
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '10px 14px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
              color: '#4ade80',
            }}>
              /plugin add &lt;github-repo&gt;
            </div>
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
