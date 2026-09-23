'use client';

import React, { useState } from 'react';
import { Terminal, Shield, Search, GitCompare, Puzzle, AlertTriangle, FileText, MessageSquare, Database, FileCode } from 'lucide-react';

interface TerminalScenario {
  id: string;
  label: string;
  icon: React.ReactNode;
  prompt: string;
  output: React.ReactNode;
}

export default function TerminalDemo() {
  const [activeTab, setActiveTab] = useState<string>('chat');

  const scenarios: TerminalScenario[] = [
    {
      id: 'chat',
      label: 'Marathon Chat',
      icon: <MessageSquare size={14} />,
      prompt: 'Looking back at our architecture discussion earlier, which approach makes the most sense?',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            [Session: architecture-review • Turn #28 • Auto-compaction active • OpenRouter Cache Hit (92% savings)]
          </div>
          <div style={{ color: '#cbd5e1', lineHeight: 1.6 }}>
            Based on our trade-off analysis over the past 20 turns, here is the clear recommendation:
          </div>
          <div style={{ padding: '10px 14px', background: 'rgba(245, 158, 11, 0.08)', borderLeft: '3px solid #f59e0b', color: '#fef3c7', fontSize: '0.88rem', lineHeight: 1.5 }}>
            <strong>1. Option A (Clean Monolith):</strong> Best fit for right now — 3-person team, zero distributed transaction overhead, and ships weeks earlier.<br />
            <strong>2. Option B (Microservices):</strong> Revisit in Q3 after traffic crosses 50k req/s.
          </div>
          <div style={{ color: '#4ade80', fontSize: '0.84rem' }}>
            ✓ Context from hours ago remains intact without memory drift or token blowup.
          </div>
        </div>
      ),
    },
    {
      id: 'memory',
      label: '/pin & Memory',
      icon: <Database size={14} />,
      prompt: '/pin Always use Python async/await, enforce strict type hints, and keep explanations concise.',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ color: '#fbbf24', fontWeight: 600 }}>
            📌 [IMMORTAL MEMORY PINNED]
          </div>
          <div style={{ color: '#cbd5e1' }}>
            Saved rule to SQLite database (<code style={{ color: '#fff' }}>~/.losna/agent_data.db</code>):
          </div>
          <pre style={{
            background: 'rgba(0,0,0,0.5)',
            padding: '10px',
            borderRadius: '6px',
            color: '#86efac',
            fontSize: '0.82rem',
            overflowX: 'auto',
          }}>
{`INSERT INTO pinned_memory (fact, created_at)
VALUES ("Prefers Python async/await, strict type hints, concise explanations", 1774338000);`}
          </pre>
          <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            This rule is permanently persisted and automatically injected into every future session, even after terminal restarts.
          </div>
        </div>
      ),
    },
    {
      id: 'code',
      label: 'Codes on Demand',
      icon: <FileCode size={14} />,
      prompt: "Great, let's build it. Generate scripts/fetch_metrics.py based on our discussion and run pytest.",
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ color: '#38bdf8' }}>
            ⚙️ Tool Call: <code style={{ color: '#fff' }}>write_to_file("scripts/fetch_metrics.py")</code>
          </div>
          <div style={{ padding: '8px 12px', background: 'rgba(34, 197, 94, 0.08)', borderLeft: '3px solid #22c55e', color: '#bbf7d0', fontSize: '0.82rem' }}>
            ✓ Created <strong>scripts/fetch_metrics.py</strong> (conforming to pinned async/await + type hint rules)
          </div>
          <div style={{ color: '#a78bfa' }}>
            ⚡ Tool Call: <code style={{ color: '#fff' }}>execute_shell_command("pytest tests/test_metrics.py")</code>
          </div>
          <pre style={{
            background: 'rgba(0,0,0,0.5)',
            padding: '8px 12px',
            borderRadius: '6px',
            color: '#86efac',
            fontSize: '0.8rem',
            overflowX: 'auto',
          }}>
{`tests/test_metrics.py .... [100%]
===================== 4 passed in 0.42s =====================`}
          </pre>
          <div style={{ color: '#cbd5e1', fontSize: '0.86rem' }}>
            Done! Script generated and all test suites passed cleanly.
          </div>
        </div>
      ),
    },
    {
      id: 'readonly',
      label: '/readonly Guard',
      icon: <Shield size={14} />,
      prompt: '/readonly',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <span style={{ color: '#fbbf24', fontWeight: 600 }}>[READONLY ACTIVE]</span>{' '}
            <span style={{ color: '#94a3b8' }}>Schema & runtime safety locks engaged</span>
          </div>
          <div style={{ color: '#64748b' }}>
            &gt; User: "Can you modify this configuration directly?"
          </div>
          <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderLeft: '3px solid #ef4444', color: '#fca5a5' }}>
            <strong>Safety Intercept:</strong> File-modifying tools and shell execution are neutralized. You can safely explore, discuss, and inspect code without accidental edits.
          </div>
          <div style={{ color: '#cbd5e1' }}>
            Ready to analyze architecture and provide non-destructive diff suggestions.
          </div>
        </div>
      ),
    },
    {
      id: 'search',
      label: '/search & Web',
      icon: <Search size={14} />,
      prompt: '/search "OpenRouter prompt caching latency and pricing 2026"',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ color: '#38bdf8' }}>
            🔍 Querying live documentation via Tavily Search API...
          </div>
          <div style={{ color: '#a78bfa' }}>
            ⚡ Trafilatura parsed clean Markdown bulletin (ads & banners stripped)
          </div>
          <div style={{ color: '#f1f5f9', lineHeight: 1.5 }}>
            <strong>Key Finding:</strong> OpenRouter prefix caching discounts reach up to 90% for Anthropic and DeepSeek models, keeping continuous terminal conversations fast (&lt;1s TTFT) and remarkably cost-effective.
          </div>
        </div>
      ),
    },
  ];

  const currentScenario = scenarios.find((s) => s.id === activeTab) || scenarios[0];

  return (
    <section id="terminal" style={{
      padding: '80px 24px',
      maxWidth: '1100px',
      margin: '0 auto',
      position: 'relative',
    }}>
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <h2 style={{ fontSize: 'clamp(1.8rem, 3.5vw, 2.5rem)', marginBottom: '12px' }}>
          A Real Companion in Your Terminal
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '640px', margin: '0 auto', fontSize: '1rem' }}>
          Talk for hours, bounce architectural ideas, save immortal preferences with <code style={{ color: 'var(--moon-amber)' }}>/pin</code> — and call on coding tools whenever you need them.
        </p>
      </div>

      {/* Terminal Container */}
      <div style={{
        background: 'var(--bg-secondary)',
        borderRadius: '16px',
        border: '1px solid var(--border-violet)',
        overflow: 'hidden',
      }}>
        {/* Terminal Header Bar */}
        <div style={{
          background: '#12111c',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          {/* Traffic lights + Title */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              <span style={{ width: '11px', height: '11px', borderRadius: '50%', background: '#ff5f56', display: 'inline-block' }} />
              <span style={{ width: '11px', height: '11px', borderRadius: '50%', background: '#ffbd2e', display: 'inline-block' }} />
              <span style={{ width: '11px', height: '11px', borderRadius: '50%', background: '#27c93f', display: 'inline-block' }} />
            </div>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              losna 🌒 ~ session: deep-chat [deepseek-v3]
            </span>
          </div>

          {/* Scenario Tabs */}
          <div style={{ display: 'flex', gap: '6px', overflowX: 'auto' }}>
            {scenarios.map((scenario) => {
              const isActive = scenario.id === activeTab;
              return (
                <button
                  key={scenario.id}
                  onClick={() => setActiveTab(scenario.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 500,
                    transition: 'all 0.15s ease',
                    background: isActive ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    color: isActive ? 'var(--moon-amber)' : 'var(--text-muted)',
                    border: isActive ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid transparent',
                  }}
                >
                  {scenario.icon}
                  <span>{scenario.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Terminal Body */}
        <div style={{
          padding: '24px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.88rem',
          minHeight: '260px',
          lineHeight: 1.6,
          background: '#090713',
        }}>
          {/* Active Prompt Line */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <span style={{ color: 'var(--moon-gold)', fontWeight: 600 }}>losna 🌒</span>
            <span style={{ color: 'var(--text-muted)' }}>&gt;</span>
            <span style={{ color: '#fff', fontWeight: 500 }}>{currentScenario.prompt}</span>
            <span style={{
              width: '8px',
              height: '16px',
              background: 'var(--moon-amber)',
              display: 'inline-block',
              animation: 'pulseGlow 1.2s infinite',
            }} />
          </div>

          {/* Scenario Output */}
          <div style={{ marginTop: '12px' }}>
            {currentScenario.output}
          </div>
        </div>

        {/* Terminal Status Footer */}
        <div style={{
          background: '#0e0d16',
          padding: '8px 18px',
          borderTop: '1px solid rgba(255, 255, 255, 0.04)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
        }}>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <span>SQLite: <strong style={{ color: '#4ade80' }}>agent_data.db</strong></span>
            <span>Logs: <strong style={{ color: '#38bdf8' }}>~/.losna/logs/losna.log</strong></span>
            <span>Mode: <strong style={{ color: activeTab === 'readonly' ? '#ef4444' : '#fbbf24' }}>
              {activeTab === 'readonly' ? 'READ-ONLY' : 'AUDIT-MODE'}
            </strong></span>
          </div>
          <div>Press <strong>/help</strong> for all 30+ commands</div>
        </div>
      </div>
    </section>
  );
}
