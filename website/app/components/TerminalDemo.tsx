'use client';

import React, { useState } from 'react';
import { Terminal, Shield, Search, GitCompare, Puzzle, Play } from 'lucide-react';

interface TerminalScenario {
  id: string;
  label: string;
  icon: React.ReactNode;
  prompt: string;
  output: React.ReactNode;
}

export default function TerminalDemo() {
  const [activeTab, setActiveTab] = useState<string>('readonly');

  const scenarios: TerminalScenario[] = [
    {
      id: 'readonly',
      label: '/readonly',
      icon: <Shield size={14} />,
      prompt: '/readonly',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <span style={{ color: '#fbbf24', fontWeight: 600 }}>[READONLY ACTIVE]</span>{' '}
            <span style={{ color: '#94a3b8' }}>All file-modifying tools (write, edit, replace, delete) are locked at runtime & schema level.</span>
          </div>
          <div style={{ color: '#64748b' }}>
            &gt; User asks: "Audit ./src/auth/jwt.py for signature validation flaws and patch it."
          </div>
          <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderLeft: '3px solid #ef4444', color: '#fca5a5' }}>
            <strong>Safety Intercept:</strong> Tool <code style={{ color: '#fff' }}>replace_file_content</code> blocked by Read-Only guard.
          </div>
          <div style={{ color: '#cbd5e1' }}>
            <strong>Analysis:</strong> In line 42, <code style={{ color: '#a78bfa' }}>jwt.decode(token, verify=False)</code> accepts unsigned tokens.
            Here is the recommended patch without modifying the live file:
          </div>
          <pre style={{
            background: 'rgba(0,0,0,0.5)',
            padding: '10px',
            borderRadius: '6px',
            color: '#86efac',
            fontSize: '0.82rem',
            overflowX: 'auto',
          }}>
{`+ decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
- decoded = jwt.decode(token, verify=False)`}
          </pre>
        </div>
      ),
    },
    {
      id: 'search',
      label: '/search & read_web',
      icon: <Search size={14} />,
      prompt: '/search "CVE-2025-fastapi-dependency-injection mitigation"',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ color: '#38bdf8' }}>
            🔍 Querying Tavily live search engine... [Found 4 high-authority citations]
          </div>
          <div style={{ color: '#a78bfa' }}>
            ⚡ Trafilatura parsing advisory bulletin from nvd.nist.gov...
          </div>
          <div style={{ color: '#f1f5f9', lineHeight: 1.5 }}>
            <strong>Findings:</strong> Affects FastAPI versions prior to 0.115.0 when using untyped Depends parameters.
            Your <code style={{ color: '#fbbf24' }}>pyproject.toml</code> currently specifies <code style={{ color: '#f87171' }}>fastapi = "^0.112.0"</code>.
          </div>
          <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Recommended action: Bump dependency to <code style={{ color: '#4ade80' }}>^0.115.2</code> and execute pytest evals.
          </div>
        </div>
      ),
    },
    {
      id: 'diff',
      label: '/diff memory',
      icon: <GitCompare size={14} />,
      prompt: '/diff session',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ color: '#94a3b8' }}>Comparing working SQLite memory against repository HEAD:</div>
          <pre style={{
            background: 'rgba(0,0,0,0.5)',
            padding: '10px',
            borderRadius: '6px',
            color: '#f8fafc',
            fontSize: '0.82rem',
            overflowX: 'auto',
          }}>
{`--- a/src/agent/core.py (disk)
+++ b/src/agent/core.py (session memory)
@@ -104,3 +104,7 @@
-    max_tool_calls = 10
+    max_tool_calls = 25  # Increased for deep multi-file tracing
+    readonly_enforced = True`}
          </pre>
          <div style={{ color: '#fbbf24', fontSize: '0.82rem' }}>
            ✓ 2 session memory alterations ready for export or rollback.
          </div>
        </div>
      ),
    },
    {
      id: 'plugin',
      label: '/plugin add',
      icon: <Puzzle size={14} />,
      prompt: '/plugin add https://github.com/snui1s/losna-plugins --skill security-auditor',
      output: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ color: '#a78bfa' }}>
            📦 Fetching remote skill repository from GitHub...
          </div>
          <div style={{ color: '#38bdf8' }}>
            ✓ Cloned into <code style={{ color: '#fff' }}>./skills/security-auditor/</code>
          </div>
          <div style={{ color: '#cbd5e1' }}>
            Loaded skill instructions: <strong>OWASP Top 10 API Security Checklist (v2025)</strong>
          </div>
          <div style={{ color: '#4ade80', fontSize: '0.85rem' }}>
            Skill enabled globally. Activate anytime with: <code style={{ color: '#fbbf24' }}>/security-auditor on</code>
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
          Raw Power Inside Your Terminal
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto', fontSize: '1rem' }}>
          Try switching between live CLI scenarios to see how Losna handles safety locks, web research, diffing, and dynamic skills.
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
              losna 🌒 ~ session: audit-42 [deepseek-v3]
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
          <div style={{ display: 'flex', gap: '16px' }}>
            <span>SQLite: <strong style={{ color: '#4ade80' }}>agent_data.db (Active)</strong></span>
            <span>Mode: <strong style={{ color: activeTab === 'readonly' ? '#ef4444' : '#fbbf24' }}>
              {activeTab === 'readonly' ? 'READ-ONLY' : 'AUDIT-MODE'}
            </strong></span>
          </div>
          <div>Press <strong>/help</strong> for all 24 commands</div>
        </div>
      </div>
    </section>
  );
}
