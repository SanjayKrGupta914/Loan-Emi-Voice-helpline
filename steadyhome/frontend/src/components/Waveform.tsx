import React from 'react';

interface WaveformProps {
  active: boolean;
  type?: 'listening' | 'speaking' | 'idle';
}

export const Waveform: React.FC<WaveformProps> = ({ active, type = 'idle' }) => {
  const bars = [14, 24, 38, 52, 68, 85, 64, 46, 32, 20, 36, 58, 72, 88, 60, 42, 25, 16];

  return (
    <div className="flex items-center justify-center gap-1 h-12 px-4 py-2 bg-background-secondary rounded-lg border border-borderCustom">
      {bars.map((height, i) => {
        let dynamicHeight = active ? Math.max(12, height * (0.4 + ((i % 5) * 0.15))) : 8;
        return (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-200 ${
              !active
                ? 'bg-secondaryText/30 h-2'
                : type === 'speaking'
                ? 'bg-brand-blue animate-pulse'
                : 'bg-brand-green animate-bounce'
            }`}
            style={{
              height: `${active ? dynamicHeight : 8}px`,
              animationDelay: `${(i * 60) % 600}ms`,
              animationDuration: active ? (type === 'speaking' ? '800ms' : '650ms') : '0ms',
            }}
          />
        );
      })}
    </div>
  );
};

