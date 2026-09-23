'use client';

import React from 'react';
import { Check, X, Shield, Zap } from 'lucide-react';

export default function Benchmarks() {
  const comparisons = [
    {
      feature: 'Chat & Memory Persistence',
      losna: 'Local SQLite (~/.losna) + /pin immortal memory',
      others: 'Ephemeral or lost after closing terminal',
      advantage: true,
    },
    {
      feature: 'Context Endurance',
      losna: 'Auto-compaction (multi-turn summary + fact extraction)',
      others: 'Abrupt context overflow or amnesia after ~15 turns',
      advantage: true,
    },
    {
      feature: 'Pricing & Token Efficiency',
      losna: '100% BYOK + OpenRouter Prefix Caching (up to 90% off)',
      others: '$20–$40/mo subscription + marked-up tokens',
      advantage: true,
    },
    {
      feature: 'Language Naturalness',
      losna: 'Strict language matching (100% Thai, 0% Chinese bleed)',
      others: 'Random thinking bleed & awkward translations',
      advantage: true,
    },
    {
      feature: 'Code & Execution Tools',
      losna: 'Full workspace suite + strict /readonly safety gate',
      others: 'Chat-only or unrestricted dangerous shell',
      advantage: true,
    },
    {
      feature: 'Crash Diagnostics & Logs',
      losna: '5MB rotating logs (~/.losna/logs) + TTFT ping test',
      others: 'Opaque silent crashes with zero local trace',
      advantage: true,
    },
    {
      feature: 'Extensibility',
      losna: 'Markdown skills in ./skills/ & GitHub /plugin installer',
      others: 'Proprietary or closed extension ecosystem',
      advantage: true,
    },
  ];

  return (
    <section id="benchmarks" style={{
      padding: '80px 24px',
      maxWidth: '1100px',
      margin: '0 auto',
      position: 'relative',
    }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h2 style={{ fontSize: 'clamp(1.8rem, 3.5vw, 2.5rem)', marginBottom: '14px' }}>
          Engineered for Marathon Sessions
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '640px', margin: '0 auto', fontSize: '1rem' }}>
          Compare how Losna CLI stays sharp across hours of conversation compared to typical ephemeral AI wrappers.
        </p>
      </div>

      {/* Comparison Table */}
      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '16px',
        overflow: 'hidden',
      }}>
        {/* Table Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 3fr 3fr',
          padding: '18px 24px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderBottom: '1px solid var(--border-subtle)',
          fontSize: '0.85rem',
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}>
          <div>Capability</div>
          <div style={{ color: 'var(--moon-gold)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>🌒 Losna CLI</span>
          </div>
          <div>Standard Cloud Assistants</div>
        </div>

        {/* Table Rows */}
        {comparisons.map((item, index) => (
          <div
            key={index}
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 3fr 3fr',
              padding: '18px 24px',
              borderBottom: index < comparisons.length - 1 ? '1px solid rgba(255, 255, 255, 0.04)' : 'none',
              alignItems: 'center',
              fontSize: '0.92rem',
              transition: 'background 0.2s',
            }}
            className="table-row"
          >
            <div style={{ fontWeight: 600, color: '#f1f5f9' }}>
              {item.feature}
            </div>

            <div style={{
              color: '#f8fafc',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: 500,
            }}>
              <span style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: 'rgba(245, 158, 11, 0.15)',
                color: 'var(--moon-amber)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <Check size={13} strokeWidth={3} />
              </span>
              <span>{item.losna}</span>
            </div>

            <div style={{
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <span style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.05)',
                color: '#64748b',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <X size={13} strokeWidth={2.5} />
              </span>
              <span>{item.others}</span>
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .table-row:hover {
          background: rgba(255, 255, 255, 0.02);
        }
        @media (max-width: 768px) {
          .table-row, div[style*="gridTemplateColumns"] {
            grid-template-columns: 1fr !important;
            gap: 10px;
          }
        }
      `}</style>
    </section>
  );
}
