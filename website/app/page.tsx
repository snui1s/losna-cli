import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import TerminalDemo from './components/TerminalDemo';
import BentoGrid from './components/BentoGrid';
import Benchmarks from './components/Benchmarks';
import Footer from './components/Footer';
import Link from 'next/link';
import { Terminal, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export default function Home() {
  return (
    <main style={{ minHeight: '100vh', position: 'relative' }}>
      <Navbar />
      
      <Hero />
      
      <TerminalDemo />
      
      <BentoGrid />
      
      <Benchmarks />

      {/* Pre-footer Call to Action */}
      <section style={{
        padding: '100px 24px',
        maxWidth: '1000px',
        margin: '0 auto',
        textAlign: 'center',
        position: 'relative',
      }}>
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '20px',
          padding: '60px 32px',
          position: 'relative',
        }}>
          <div style={{ position: 'relative', zIndex: 1 }}>
            <h2 style={{ fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '16px', lineHeight: 1.2 }}>
              Ready to Audit with Pure BYOK Freedom?
            </h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '580px', margin: '0 auto 36px', fontSize: '1.05rem', lineHeight: 1.6 }}>
              Run the one-line installer, plug in your OpenRouter API key, and experience deep terminal code analysis without limits.
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
              <Link href="/docs" className="btn-primary" style={{ padding: '14px 32px', fontSize: '1.05rem' }}>
                <Terminal size={19} />
                Get Started in 60 Seconds
                <ArrowRight size={17} />
              </Link>
              <a
                href="https://github.com/snui1s/losna-cli"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
                style={{ padding: '14px 28px', fontSize: '1.05rem' }}
              >
                <ShieldCheck size={19} style={{ color: 'var(--moon-gold)' }} />
                View Source on GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
