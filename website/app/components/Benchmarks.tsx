'use client';

import React from 'react';
import { Check, X, Shield, Zap } from 'lucide-react';

export default function Benchmarks() {
  const comparisons = [
    {
      feature: 'Pricing Model',
      losna: '100% BYOK (Zero Token Markup)',
      others: '$20–$40/mo + Marked up tokens',
      advantage: true,
    },
    {
      feature: 'Deep Reasoning Output',
      losna: 'Full, untruncated architecture analysis',
      others: 'Often truncated to preserve provider bandwidth',
      advantage: true,
    },
    {
      feature: 'Strict Read-Only Mode',
      losna: 'Schema & runtime locked (/readonly)',
      others: 'Prompt-only suggestion (can still execute writes)',
      advantage: true,
    },
    {
      feature: 'Destructive Shell Interception',
      losna: 'Interactive colored (y/n) confirmation gate',
      others: 'Unmonitored execution or rigid whitelist',
      advantage: true,
    },
    {
      feature: 'Chat & Memory Persistence',
      losna: 'Local SQLite (agent_data.db) + auto-compaction',
      others: 'Ephemeral or uploaded to 3rd party servers',
      advantage: true,
    },
    {
      feature: 'Open Skill System',
      losna: 'Native Markdown in ./skills/ & GitHub installer',
      others: 'Proprietary or closed extensions',
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
          Engineered Differently
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto', fontSize: '1rem' }}>
          See how Losna CLI prioritizes developer sovereignty, safety, and depth over restrictive closed ecosystems.
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
