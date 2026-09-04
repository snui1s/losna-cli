'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import {
  Search,
  Terminal,
  Shield,
  BookOpen,
  Copy,
  Check,
  ChevronRight,
  Puzzle,
  Database,
  ArrowLeft,
  Key,
  Flame,
} from 'lucide-react';

interface CommandItem {
  command: string;
  category: 'Session' | 'Security' | 'Memory' | 'Plugin' | 'System';
  description: string;
}

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(text);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const commands: CommandItem[] = [
    { command: '/help', category: 'System', description: 'Show all available commands and active loaded skills.' },
    { command: '/new <title>', category: 'Session', description: 'Start a new chat session with an optional custom title.' },
    { command: '/rename [id] <title>', category: 'Session', description: 'Rename the active or specified chat session.' },
    { command: '/sessions', category: 'Session', description: 'List all saved chat sessions with IDs and timestamps.' },
    { command: '/switch <id>', category: 'Session', description: 'Switch to a different chat session by ID.' },
    { command: '/delete_session <id>', category: 'Session', description: 'Permanently remove a chat session and associated history.' },
    { command: '/history [id]', category: 'Session', description: 'View full conversation logs and tool execution events.' },
    { command: '/model [model_id]', category: 'System', description: 'View current OpenRouter model or switch models on the fly.' },
    { command: '/readonly', category: 'Security', description: 'Toggle Read-Only Mode (locks file modifications & shell commands).' },
    { command: '/diff [file|session]', category: 'Security', description: 'View colored syntax-highlighted git diff for modified files or memory state.' },
    { command: '/enter2confirm', category: 'System', description: 'Toggle double-Enter requirement before sending prompts to the AI.' },
    { command: '/pin <text>', category: 'Memory', description: 'Pin a custom rule or fact to Core Memory (remembered across all sessions forever).' },
    { command: '/pins', category: 'Memory', description: 'List all pinned Core Memory rules with their database IDs.' },
    { command: '/unpin <id>', category: 'Memory', description: 'Remove a pinned Core Memory rule by database ID.' },
    { command: '/export [path]', category: 'Session', description: 'Export active conversation log into a structured Markdown file.' },
    { command: '/clear', category: 'System', description: 'Clear terminal screen and re-render header banner.' },
    { command: '/ls [path]', category: 'System', description: 'List directory files and folders in a clean formatted view.' },
    { command: '/cd <path>', category: 'System', description: 'Change working directory (supports "..", "~", and "-").' },
    { command: '/init-ai', category: 'System', description: 'Generate a starter "ai.txt" blueprint file for project auto-detection.' },
    { command: '/max_tool_calls [n]', category: 'System', description: 'View or set maximum allowed tool call iterations per turn.' },
    { command: '/plugin add <url>', category: 'Plugin', description: 'Download and install all skills from a remote GitHub repository.' },
    { command: '/plugin add <url> --skill <name>', category: 'Plugin', description: 'Download and install a specific skill from a GitHub repository.' },
    { command: '/plugin remove <name>', category: 'Plugin', description: 'Uninstall and remove a custom skill plugin.' },
    { command: '/plugin list', category: 'Plugin', description: 'List all installed skill plugins and their activation status.' },
    { command: '/plugin enable <name>', category: 'Plugin', description: 'Enable a previously disabled skill plugin globally.' },
    { command: '/plugin disable <name>', category: 'Plugin', description: 'Disable an active skill plugin globally.' },
    { command: '/<skill> on|off|status', category: 'Plugin', description: 'Quick toggle or inspect status for any loaded skill.' },
  ];

  const categories = ['All', 'Session', 'Security', 'Memory', 'Plugin', 'System'];

  const filteredCommands = commands.filter((cmd) => {
    const matchesCategory = selectedCategory === 'All' || cmd.category === selectedCategory;
    const matchesSearch =
      cmd.command.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cmd.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <Navbar />

      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '110px 24px 80px',
        display: 'grid',
        gridTemplateColumns: '260px 1fr',
        gap: '40px',
      }}>
        {/* Sticky Sidebar */}
        <aside style={{
          position: 'sticky',
          top: '90px',
          height: 'fit-content',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
        }} className="docs-sidebar">
          <Link href="/" style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            color: 'var(--moon-amber)',
            fontSize: '0.88rem',
            fontWeight: 500,
          }}>
            <ArrowLeft size={16} />
            Back to Overview
          </Link>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Documentation Index
            </div>
            <a href="#quickstart" className="sidebar-link active">1. Quickstart & Install</a>
            <a href="#setup" className="sidebar-link">2. API Configuration (BYOK)</a>
            <a href="#readonly-guide" className="sidebar-link">3. Read-Only Safety Guard</a>
            <a href="#commands" className="sidebar-link">4. Slash Commands Directory</a>
            <a href="#plugins" className="sidebar-link">5. Plugin & Skill Development</a>
            <a href="#architecture" className="sidebar-link">6. SQLite Memory Architecture</a>
          </div>

          <div style={{
            background: 'rgba(245, 158, 11, 0.06)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: '12px',
            padding: '16px',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
          }}>
            <div style={{ color: 'var(--moon-gold)', fontWeight: 600, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Key size={14} /> BYOK Privacy
            </div>
            Keys are saved strictly to <code style={{ color: '#fff' }}>~/.losnarc</code> on your local disk. No server relay.
          </div>
        </aside>

        {/* Main Content Area */}
        <main style={{ maxWidth: '880px' }}>
          {/* Header */}
          <div style={{ marginBottom: '40px' }}>
            <h1 style={{ fontSize: '2.5rem', marginBottom: '14px', letterSpacing: '-0.02em' }}>
              Losna CLI Documentation & Manual
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.6 }}>
              Complete guide to installing, configuring, securing, and extending your terminal AI auditing companion.
            </p>
          </div>

          {/* Section 1: Quickstart */}
          <section id="quickstart" style={{ marginBottom: '60px', scrollMarginTop: '100px' }}>
            <h2 style={{ fontSize: '1.7rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Terminal size={22} style={{ color: 'var(--moon-amber)' }} />
              1. Quickstart & Installation
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '20px' }}>
              Losna CLI installs in a completely isolated environment inside <code style={{ color: '#fbbf24' }}>~/.losna/</code>. 
              No system Python packages are overwritten or modified.
            </p>

            {/* Prerequisites */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '16px 20px',
              marginBottom: '20px',
            }}>
              <div style={{ fontWeight: 600, marginBottom: '8px', fontSize: '0.92rem' }}>Prerequisites:</div>
              <ul style={{ listStyle: 'disc', paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <li>Git installed and in system PATH</li>
                <li>Python 3.10 or newer (tested up to Python 3.13)</li>
              </ul>
            </div>

            {/* Windows Install */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Windows (PowerShell):
              </div>
              <div style={{
                background: '#09080e',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: '10px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
              }}>
                <span style={{ color: '#f1f5f9' }}>irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex</span>
                <button
                  onClick={() => handleCopy('irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex')}
                  style={{ color: copiedCmd ? '#4ade80' : 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  {copiedCmd ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
            </div>

            {/* Unix Install */}
            <div style={{ marginBottom: '24px' }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                macOS / Linux (Bash):
              </div>
              <div style={{
                background: '#09080e',
                border: '1px solid rgba(139, 92, 246, 0.25)',
                borderRadius: '10px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
              }}>
                <span style={{ color: '#f1f5f9' }}>curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash</span>
                <button
                  onClick={() => handleCopy('curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash')}
                  style={{ color: copiedCmd ? '#4ade80' : 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  {copiedCmd ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              After the script finishes, restart your terminal and run <code style={{ color: 'var(--moon-gold)', background: 'rgba(245,158,11,0.1)', padding: '2px 6px', borderRadius: '4px' }}>losna</code> to start.
            </p>
          </section>

          {/* Section 2: Setup */}
          <section id="setup" style={{ marginBottom: '60px', scrollMarginTop: '100px' }}>
            <h2 style={{ fontSize: '1.7rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Key size={22} style={{ color: 'var(--lunar-violet)' }} />
              2. API Configuration (BYOK)
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
              On first launch, Losna CLI prompts you to save your API keys to <code style={{ color: '#fff' }}>~/.losnarc</code>.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="glass-panel" style={{ padding: '20px' }}>
                <h4 style={{ color: 'var(--moon-amber)', marginBottom: '8px' }}>OpenRouter API Key (Required)</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                  Gives you access to DeepSeek V3, DeepSeek R1, Claude 3.5 Sonnet, and GPT-4o with zero token markup.
                </p>
              </div>
              <div className="glass-panel" style={{ padding: '20px' }}>
                <h4 style={{ color: '#38bdf8', marginBottom: '8px' }}>Tavily API Key (Optional)</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                  Enables real-time web search for online CVE lookups and documentation verification.
                </p>
              </div>
            </div>
          </section>

          {/* Section 3: Read-Only Safety Guide */}
          <section id="readonly-guide" style={{ marginBottom: '60px', scrollMarginTop: '100px' }}>
            <h2 style={{ fontSize: '1.7rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Shield size={22} style={{ color: '#ef4444' }} />
              3. Read-Only Safety Guard
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '20px' }}>
              When auditing sensitive or production repositories, activate Read-Only mode with <code style={{ color: '#fbbf24' }}>/readonly</code>.
            </p>

            <div style={{
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '12px',
              padding: '20px',
              color: '#fca5a5',
              lineHeight: 1.6,
              fontSize: '0.92rem',
            }}>
              <strong style={{ color: '#fff' }}>How Safety Works at the Engine Level:</strong>
              <ol style={{ paddingLeft: '20px', marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <li><strong>Schema Filter:</strong> Modifying tools (<code style={{ color: '#fff' }}>write_to_file</code>, <code style={{ color: '#fff' }}>replace_file_content</code>, etc.) are omitted from the model schema entirely.</li>
                <li><strong>Runtime Gate:</strong> Any attempt to invoke file mutation or arbitrary shell commands returns a hard runtime block.</li>
                <li><strong>Interactive Interception:</strong> In normal mode, destructive commands pause and require a terminal <code style={{ color: '#fff' }}>(y/n)</code> confirmation.</li>
              </ol>
            </div>
          </section>

          {/* Section 4: Slash Commands Directory */}
          <section id="commands" style={{ marginBottom: '60px', scrollMarginTop: '100px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
              <div>
                <h2 style={{ fontSize: '1.7rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Terminal size={22} style={{ color: 'var(--moon-gold)' }} />
                  4. Slash Commands Directory
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                  Complete reference of all 24 built-in slash commands.
                </p>
              </div>

              {/* Search Bar */}
              <div style={{
                position: 'relative',
                minWidth: '260px',
              }}>
                <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Filter commands..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px 8px 36px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    background: 'rgba(255, 255, 255, 0.04)',
                    color: '#fff',
                    fontSize: '0.88rem',
                    fontFamily: 'var(--font-mono)',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            {/* Category Filter Chips */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', overflowX: 'auto', paddingBottom: '6px' }}>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: '4px 12px',
                    borderRadius: '6px',
                    fontSize: '0.78rem',
                    fontWeight: 500,
                    transition: 'all 0.15s',
                    background: selectedCategory === cat ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                    color: selectedCategory === cat ? 'var(--moon-amber)' : 'var(--text-muted)',
                    border: selectedCategory === cat ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid var(--border-subtle)',
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Commands Table */}
            <div style={{
              background: 'rgba(15, 14, 22, 0.7)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              overflow: 'hidden',
            }}>
              {filteredCommands.length === 0 ? (
                <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No slash commands match your search query.
                </div>
              ) : (
                filteredCommands.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 18px',
                      borderBottom: idx < filteredCommands.length - 1 ? '1px solid rgba(255, 255, 255, 0.04)' : 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '16px',
                      transition: 'background 0.15s',
                    }}
                    className="cmd-row"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
                      <code style={{
                        color: 'var(--moon-gold)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.88rem',
                        fontWeight: 600,
                        background: 'rgba(245, 158, 11, 0.08)',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: '1px solid rgba(245, 158, 11, 0.18)',
                      }}>
                        {item.command}
                      </code>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                        {item.description}
                      </span>
                    </div>

                    <span style={{
                      fontSize: '0.72rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-muted)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      flexShrink: 0,
                    }}>
                      {item.category}
                    </span>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Section 5: Plugins & Skills */}
          <section id="plugins" style={{ marginBottom: '60px', scrollMarginTop: '100px' }}>
            <h2 style={{ fontSize: '1.7rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Puzzle size={22} style={{ color: 'var(--moon-amber)' }} />
              5. Plugin & Skill Development
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
              Skills in Losna CLI are simple folders containing instructions in <code style={{ color: '#fff' }}>SKILL.md</code>.
              You can create your own in <code style={{ color: '#fbbf24' }}>./skills/&lt;skill-name&gt;/</code> or install them directly from GitHub:
            </p>

            <pre style={{
              background: '#09080e',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '16px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              color: '#f8fafc',
              marginBottom: '16px',
              overflowX: 'auto',
            }}>
{`# Install a plugin bundle directly from GitHub:
losna > /plugin add https://github.com/snui1s/losna-plugins

# Or install a specific skill only:
losna > /plugin add https://github.com/snui1s/losna-plugins --skill security-auditor`}
            </pre>
          </section>

          {/* Section 6: SQLite Architecture */}
          <section id="architecture" style={{ marginBottom: '60px', scrollMarginTop: '100px' }}>
            <h2 style={{ fontSize: '1.7rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Database size={22} style={{ color: 'var(--lunar-violet)' }} />
              6. SQLite Memory Architecture
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
              All chat history, token compaction stats, and core rules are stored in a local SQLite file: <code style={{ color: '#fbbf24' }}>agent_data.db</code>.
            </p>
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                <div>
                  <h4 style={{ color: '#f8fafc', fontSize: '0.95rem', marginBottom: '6px' }}>Auto-Compaction</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    Summarizes older message turns when token count grows high, ensuring low latency.
                  </p>
                </div>
                <div>
                  <h4 style={{ color: '#f8fafc', fontSize: '0.95rem', marginBottom: '6px' }}>Core Memory Pinning</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    <code style={{ color: '#fbbf24' }}>/pin &lt;fact&gt;</code> stores persistent facts injected into every future conversation turn.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>

      <Footer />

      <style jsx>{`
        .sidebar-link {
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 0.88rem;
          color: var(--text-secondary);
          transition: all 0.15s ease;
          display: block;
        }
        .sidebar-link:hover {
          color: #fff;
          background: rgba(255, 255, 255, 0.04);
        }
        .cmd-row:hover {
          background: rgba(255, 255, 255, 0.025);
        }
        @media (max-width: 900px) {
          div[style*="gridTemplateColumns: '260px 1fr'"] {
            grid-template-columns: 1fr !important;
          }
          .docs-sidebar {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
