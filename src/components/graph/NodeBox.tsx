import React from 'react';

interface Props {
  pos: { x: number; y: number; w: number; h: number };
  label: string;
  subLabel: string;
  isActive: boolean;
  isSelected: boolean;
  isVisited: boolean;
  count?: number;
  activeColor: string;
  scale: number;
  onClick: () => void;
}

export default function NodeBox({
  pos,
  label,
  subLabel,
  isActive,
  isSelected,
  isVisited,
  count,
  activeColor,
  scale,
  onClick,
}: Props) {
  return (
    <g className="cursor-pointer" onClick={onClick}>
      {isActive && (
        <rect
          x={pos.x - 3}
          y={pos.y - 3}
          width={pos.w + 6}
          height={pos.h + 6}
          rx={8 * scale}
          fill="none"
          stroke={activeColor}
          strokeWidth="2"
          className="animate-pulse opacity-60"
        />
      )}
      <rect
        x={pos.x}
        y={pos.y}
        width={pos.w}
        height={pos.h}
        rx={6 * scale}
        fill="#0f172a"
        stroke={isActive ? activeColor : isSelected ? '#cbd5e1' : isVisited ? '#475569' : '#1e293b'}
        strokeWidth={isActive || isSelected ? '2' : '1.2'}
      />
      <text
        x={pos.x + 10 * scale}
        y={pos.y + 18 * scale}
        fill={isActive ? '#ffffff' : '#f1f5f9'}
        fontSize={11 * scale}
        fontWeight="600"
      >
        {label}
      </text>
      <text
        x={pos.x + 10 * scale}
        y={pos.y + 32 * scale}
        fill={isActive ? activeColor : '#64748b'}
        fontSize={9 * scale}
      >
        {subLabel}
      </text>
      {isVisited && (
        <g>
          <circle cx={pos.x + pos.w - 12 * scale} cy={pos.y + 12 * scale} r={6 * scale} fill="#10b981" />
          <text
            x={pos.x + pos.w - 12 * scale}
            y={pos.y + 15 * scale}
            textAnchor="middle"
            fill="#ffffff"
            fontSize={8 * scale}
            fontWeight="bold"
          >
            {count && count > 1 ? count : '✓'}
          </text>
        </g>
      )}
      {isActive && (
        <circle
          cx={pos.x + pos.w - 12 * scale}
          cy={pos.y + pos.h - 12 * scale}
          r={4 * scale}
          fill={activeColor}
          className="animate-ping"
        />
      )}
    </g>
  );
}
