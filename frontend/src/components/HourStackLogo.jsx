import React, { useState, useEffect } from 'react';

/**
 * HourStack logo — C2 Electric Green neon, live-ticking clock.
 * Hands update every second using real system time.
 */
export default function HourStackLogo({ size = 38 }) {
  const [time, setTime] = useState(new Date());
  const faceBg = '#020600';

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const cx = 24, cy = 24;

  // Angles in degrees, 0 = 12 o'clock
  const secs    = time.getSeconds();
  const mins    = time.getMinutes();
  const hours   = time.getHours() % 12;

  const secDeg  = secs * 6;                          // 360/60
  const minDeg  = mins * 6 + secs * 0.1;             // smooth
  const hourDeg = hours * 30 + mins * 0.5;           // smooth

  const hand = (deg, length) => {
    const rad = (deg - 90) * (Math.PI / 180);
    return {
      x2: cx + length * Math.cos(rad),
      y2: cy + length * Math.sin(rad),
    };
  };

  const h = hand(hourDeg, 6.5);
  const m = hand(minDeg,  9);
  const s = hand(secDeg,  9.5);

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="HourStack live clock logo"
    >
      <defs>
        <filter id="hs-glow">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Outer dashed orbit ring */}
      <circle cx={cx} cy={cy} r="21"
        stroke="#00ff41" strokeWidth="1"
        strokeDasharray="4 3" fill="none"
        opacity="0.25" filter="url(#hs-glow)" />

      {/* Main glowing ring */}
      <circle cx={cx} cy={cy} r="17"
        stroke="#00ff41" strokeWidth="2.5"
        fill="rgba(0,255,65,0.05)"
        filter="url(#hs-glow)" />

      {/* Inner clock face */}
      <circle cx={cx} cy={cy} r="11"
        fill={faceBg} stroke="#00ff41" strokeWidth="0.8" />

      {/* 4 cardinal hour markers */}
      <circle cx="24" cy="8"  r="1.2" fill="#00ff41" opacity="0.85" />
      <circle cx="24" cy="40" r="1.2" fill="#00ff41" opacity="0.85" />
      <circle cx="8"  cy="24" r="1.2" fill="#00ff41" opacity="0.85" />
      <circle cx="40" cy="24" r="1.2" fill="#00ff41" opacity="0.85" />

      {/* Hour hand */}
      <line x1={cx} y1={cy} x2={h.x2} y2={h.y2}
        stroke="#00ff41" strokeWidth="2.2" strokeLinecap="round"
        filter="url(#hs-glow)" />

      {/* Minute hand */}
      <line x1={cx} y1={cy} x2={m.x2} y2={m.y2}
        stroke="#00ff41" strokeWidth="1.6" strokeLinecap="round"
        filter="url(#hs-glow)" />

      {/* Second hand — yellow sweep, ticks every second */}
      <line x1={cx} y1={cy} x2={s.x2} y2={s.y2}
        stroke="#ffd000" strokeWidth="1.2" strokeLinecap="round"
        filter="url(#hs-glow)" />

      {/* Centre dot */}
      <circle cx={cx} cy={cy} r="1.6" fill="#00ff41" filter="url(#hs-glow)" />
      <circle cx={cx} cy={cy} r="0.7" fill={faceBg} />
    </svg>
  );
}
