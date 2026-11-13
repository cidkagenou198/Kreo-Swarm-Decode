import { useState } from "react";
import { KeyLedInfo } from "../types";
import { SWARM75_SVG_PATHS } from "../lib/svgPaths";

interface SvgKeyboardSurfaceProps {
  keys: KeyLedInfo[];
  selectedKeys: Set<string>;
  displayColors: Record<string, string>;
  onSelectKey: (uiKey: string, multiSelect: boolean) => void;
}

export function SvgKeyboardSurface({
  keys,
  selectedKeys,
  displayColors,
  onSelectKey,
}: SvgKeyboardSurfaceProps) {
  const [hoveredKey, setHoveredKey] = useState<KeyLedInfo | null>(null);

  // Map svgId -> KeyLedInfo for fast lookup
  const keyBySvgId = new Map<string, KeyLedInfo>();
  for (const k of keys) {
    keyBySvgId.set(k.svg_id, k);
  }

  return (
    <div className="relative w-full max-w-4xl mx-auto select-none">
      {/* Keyboard Container with 1:1 Aspect Ratio Matching Assets */}
      <div className="relative w-full aspect-[2999.67/2000] rounded-2xl overflow-hidden border border-slate-800/80 bg-[#070b12] shadow-2xl flex items-center justify-center">
        {/* Layer 1: Base Chassis Image */}
        <img
          src="/keyboard/swarm75/base/default.webp"
          alt="Kreo Swarm 75 Mechanical Chassis"
          className="absolute inset-0 w-full h-full object-contain pointer-events-none filter drop-shadow-[0_0_35px_rgba(124,58,237,0.18)]"
        />

        {/* Layer 2: Interactive SVG Vector LED Layer */}
        <svg
          viewBox="0 0 2999.67 2999.67"
          className="absolute inset-0 w-full h-full object-contain z-10"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Soft LED Key Glow */}
            <filter id="glow-key" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="10" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>

            {/* High-Intensity Selection Glow */}
            <filter id="glow-selected" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="16" result="blur1" />
              <feGaussianBlur stdDeviation="6" result="blur2" />
              <feMerge>
                <feMergeNode in="blur1" />
                <feMergeNode in="blur2" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Render All 82 Key Paths */}
          {Object.entries(SWARM75_SVG_PATHS).map(([svgId, pathD]) => {
            const keyInfo = keyBySvgId.get(svgId);
            const uiKey = keyInfo?.ui_key?.toLowerCase() || svgId.replace("key_", "").toLowerCase();
            const isSelected = selectedKeys.has(uiKey);
            const isHovered = hoveredKey?.svg_id === svgId;
            const color = displayColors[uiKey] || keyInfo?.color || "#273240";

            return (
              <path
                key={svgId}
                id={svgId}
                d={pathD}
                fill={color}
                fillOpacity={isSelected ? 0.85 : isHovered ? 0.75 : 0.55}
                stroke={isSelected ? "#FFFFFF" : isHovered ? "#C084FC" : color}
                strokeWidth={isSelected ? 10 : isHovered ? 6 : 2}
                filter={isSelected ? "url(#glow-selected)" : "url(#glow-key)"}
                className="cursor-pointer transition-all duration-150"
                onClick={(e) => onSelectKey(uiKey, e.shiftKey || e.ctrlKey || e.metaKey)}
                onMouseEnter={() => keyInfo && setHoveredKey(keyInfo)}
                onMouseLeave={() => setHoveredKey(null)}
              />
            );
          })}
        </svg>

        {/* Layer 3: Laser-Etched Legends Image (Overlay with Screen Blend) */}
        <img
          src="/keyboard/swarm75/letters/default.webp"
          alt="Kreo Swarm 75 Keycap Legends"
          className="absolute inset-0 w-full h-full object-contain pointer-events-none z-20 opacity-90 mix-blend-screen"
        />

        {/* Layer 4: Live Hover Tooltip Badge */}
        {hoveredKey && (
          <div className="absolute bottom-3 left-4 z-30 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-mono backdrop-blur-md shadow-lg flex items-center space-x-2 text-slate-200">
            <div
              className="w-3 h-3 rounded-full border border-slate-500 shadow-sm"
              style={{
                backgroundColor: displayColors[hoveredKey.ui_key.toLowerCase()] || hoveredKey.color,
              }}
            />
            <span className="font-bold text-white">{hoveredKey.label}</span>
            <span className="text-slate-400">({hoveredKey.logical_id})</span>
            <span className="text-purple-400 font-semibold uppercase">
              {displayColors[hoveredKey.ui_key.toLowerCase()] || hoveredKey.color}
            </span>
            <span className="text-slate-500 text-[10px]">
              Pos: {hoveredKey.row},{hoveredKey.col}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

