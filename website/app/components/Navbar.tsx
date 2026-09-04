'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Terminal, BookOpen, Menu, X, ShieldCheck } from 'lucide-react';
import GithubIcon from './icons/GithubIcon';

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 50,
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      background: 'rgba(10, 7, 20, 0.92)',
      borderBottom: '1px solid var(--border-subtle)',
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0 24px',
        height: '68px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        {/* Brand */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '9px',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.15rem',
          }}>
            🌒
          </div>
          <span style={{
            fontSize: '1.2rem',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            losna
            <span style={{
              fontSize: '0.7rem',
              fontWeight: 500,
              padding: '2px 7px',
              borderRadius: '9999px',
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              color: 'var(--moon-amber)',
            }}>
              v0.1.0
            </span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav style={{
          display: 'none',
          alignItems: 'center',
          gap: '32px',
          fontSize: '0.9rem',
          color: 'var(--text-secondary)',
        }} className="desktop-nav">
          <a href="/#features" style={{ transition: 'color 0.2s' }} className="nav-link">Features</a>
          <a href="/#terminal" style={{ transition: 'color 0.2s' }} className="nav-link">Interactive CLI</a>
          <a href="/#benchmarks" style={{ transition: 'color 0.2s' }} className="nav-link">Benchmarks</a>
          <Link href="/docs" style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--moon-gold)', fontWeight: 500 }}>
            <BookOpen size={16} />
            Documentation
          </Link>
        </nav>

        {/* Action buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <a
            href="https://github.com/snui1s/losna-cli"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--text-secondary)',
              fontSize: '0.9rem',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              background: 'rgba(255,255,255,0.02)',
              transition: 'all 0.2s',
            }}
            className="github-btn"
          >
            <GithubIcon size={16} />
            <span className="hide-mobile">GitHub</span>
          </a>

          <Link href="/docs" className="btn-primary hide-mobile" style={{ padding: '8px 16px', fontSize: '0.88rem' }}>
            <Terminal size={15} />
            Quickstart
          </Link>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            style={{
              color: 'var(--text-secondary)',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
            }}
            className="mobile-menu-btn"
            aria-label="Toggle Menu"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div style={{
          background: 'rgba(15, 14, 22, 0.95)',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '20px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}>
          <a href="/#features" onClick={() => setMobileOpen(false)}>Features</a>
          <a href="/#terminal" onClick={() => setMobileOpen(false)}>Interactive CLI</a>
          <a href="/#benchmarks" onClick={() => setMobileOpen(false)}>Benchmarks</a>
          <Link href="/docs" onClick={() => setMobileOpen(false)} style={{ color: 'var(--moon-gold)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={16} />
            Documentation
          </Link>
          <Link href="/docs" className="btn-primary" style={{ textAlign: 'center', marginTop: '8px' }}>
            Get Started
          </Link>
        </div>
      )}

      <style jsx>{`
        @media (min-width: 768px) {
          .desktop-nav {
            display: flex !important;
          }
          .mobile-menu-btn {
            display: none !important;
          }
        }
        @media (max-width: 767px) {
          .hide-mobile {
            display: none !important;
          }
        }
        .nav-link:hover {
          color: var(--text-primary);
        }
        .github-btn:hover {
          color: #ffffff;
          border-color: rgba(255,255,255,0.2);
          background: rgba(255,255,255,0.06);
        }
      `}</style>
    </header>
  );
}
