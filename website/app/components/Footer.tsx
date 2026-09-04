import React from 'react';
import Link from 'next/link';

export default function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border-subtle)',
      background: 'rgba(8, 8, 12, 0.95)',
      padding: '60px 24px 40px',
      position: 'relative',
      zIndex: 10,
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '40px',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '30px',
        }}>
          {/* Brand & Mission */}
          <div style={{ maxWidth: '380px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <span style={{ fontSize: '1.4rem' }}>🌒</span>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em' }}>losna-cli</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              An all-around, deep AI terminal assistant for code comprehension, architecture inspection, 
              and security auditing. Built with pure BYOK freedom.
            </p>
          </div>

          {/* Links Grid */}
          <div style={{ display: 'flex', gap: '60px', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--moon-gold)', textTransform: 'uppercase', marginBottom: '14px', letterSpacing: '0.05em' }}>
                Navigation
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <li><Link href="/" style={{ transition: 'color 0.2s' }}>Home</Link></li>
                <li><Link href="/docs" style={{ transition: 'color 0.2s' }}>Documentation</Link></li>
                <li><a href="/#features" style={{ transition: 'color 0.2s' }}>Features</a></li>
                <li><a href="/#benchmarks" style={{ transition: 'color 0.2s' }}>Benchmarks</a></li>
              </ul>
            </div>

            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--lunar-violet)', textTransform: 'uppercase', marginBottom: '14px', letterSpacing: '0.05em' }}>
                Ecosystem
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <li><a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer">OpenRouter Models</a></li>
                <li><a href="https://tavily.com" target="_blank" rel="noopener noreferrer">Tavily Web Search</a></li>
                <li><a href="https://github.com/snui1s/losna-cli" target="_blank" rel="noopener noreferrer">GitHub Repository</a></li>
                <li><a href="https://github.com/snui1s/losna-cli/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">Apache 2.0 License</a></li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div style={{
          paddingTop: '24px',
          borderTop: '1px solid rgba(255, 255, 255, 0.04)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          fontSize: '0.82rem',
          color: 'var(--text-muted)',
        }}>
          <div>
            © {new Date().getFullYear()} Losna CLI. Open source under Apache 2.0 License.
          </div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span>Privacy First (BYOK)</span>
            <span>•</span>
            <span>Zero Telemetry</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
