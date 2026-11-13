import { useState } from "react";
import { Pipette, Sparkles, Paintbrush, Palette } from "lucide-react";

interface ColorPickerPanelProps {
  currentColor: string;
  onChangeColor: (color: string) => void;
  onApplyToSelection: () => void;
  onApplyToAll: () => void;
  selectedCount: number;
}

const DEFAULT_SWATCHES = [
  "#FF0033", // Neon Red
  "#FF5500", // Vibrant Orange
  "#FFCC00", // Amber Yellow
  "#00FF66", // Cyber Green
  "#00E5FF", // Aqua Cyan
  "#0066FF", // Electric Blue
  "#7B2CBF", // Deep Violet
  "#FF00AA", // Hot Pink
  "#FFFFFF", // Pure White
  "#000000", // LED Off
];

const THEME_PALETTES: { name: string; colors: string[] }[] = [
  { name: "Cyberpunk", colors: ["#00E5FF", "#FF007F", "#FFE600", "#7B2CBF"] },
  { name: "Synthwave", colors: ["#FF00AA", "#9D4EDD", "#3A0CA3", "#4CC9F0"] },
  { name: "Oceanic", colors: ["#0077B6", "#00B4D8", "#90E0EF", "#03045E"] },
  { name: "Toxic Matrix", colors: ["#00FF66", "#39FF14", "#0D5C22", "#003B14"] },
];

export function ColorPickerPanel({
  currentColor,
  onChangeColor,
  onApplyToSelection,
  onApplyToAll,
  selectedCount,
}: ColorPickerPanelProps) {
  const [recentColors, setRecentColors] = useState<string[]>([
    "#00E5FF",
    "#FF00AA",
    "#00FF66",
    "#FFCC00",
  ]);

  const handleSelectColor = (color: string) => {
    onChangeColor(color);
    if (!recentColors.includes(color) && color !== "#000000") {
      setRecentColors((prev) => [color, ...prev.slice(0, 7)]);
    }
  };

  return (
    <div className="p-5 rounded-2xl bg-[#0f1420] border border-slate-800 shadow-xl space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Paintbrush className="w-4 h-4 text-purple-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            RGB Color Palette
          </h4>
        </div>
        <span className="text-xs text-slate-400 font-mono uppercase font-semibold">
          {currentColor}
        </span>
      </div>

      {/* Main Color Preview & Direct Hex Input */}
      <div className="flex items-center gap-3">
        {/* Interactive Color Box */}
        <div className="relative group">
          <div
            className="w-14 h-14 rounded-xl border border-slate-700 shadow-md cursor-pointer flex items-center justify-center transition transform group-hover:scale-105"
            style={{
              backgroundColor: currentColor,
              boxShadow: `0 0 16px ${currentColor}66`,
            }}
          >
            <input
              type="color"
              value={currentColor.startsWith("#") ? currentColor : "#FF0000"}
              onChange={(e) => handleSelectColor(e.target.value)}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              title="Click to open color gradient picker"
            />
            <Pipette className="w-5 h-5 text-white/80 drop-shadow pointer-events-none group-hover:text-white" />
          </div>
        </div>

        {/* Hex Input and Sliders */}
        <div className="flex-1 space-y-1.5">
          <label className="text-[11px] font-semibold tracking-wider uppercase text-slate-400">
            Hex Code
          </label>
          <div className="flex items-center rounded-lg bg-slate-900 border border-slate-700/80 px-2.5 py-1.5 focus-within:border-purple-500">
            <span className="text-slate-500 font-mono text-sm mr-1">#</span>
            <input
              type="text"
              value={currentColor.replace("#", "")}
              onChange={(e) => {
                const val = e.target.value.trim();
                if (/^[0-9A-Fa-f]{0,6}$/.test(val)) {
                  handleSelectColor(`#${val}`);
                }
              }}
              className="bg-transparent text-sm font-mono text-white focus:outline-none uppercase w-full"
              maxLength={6}
            />
          </div>
        </div>
      </div>

      {/* Preset Swatches (NGENUITY & Wootility Style) */}
      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 block">
          Preset Swatches
        </label>
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
          {DEFAULT_SWATCHES.map((color) => {
            const isCurrent = currentColor.toLowerCase() === color.toLowerCase();
            return (
              <button
                key={color}
                onClick={() => handleSelectColor(color)}
                style={{ backgroundColor: color }}
                className={`
                  h-7 rounded-lg transition-transform hover:scale-110 relative border
                  ${isCurrent ? "border-white ring-2 ring-purple-400 scale-105" : "border-slate-700/80"}
                `}
                title={color}
              />
            );
          })}
        </div>
      </div>

      {/* Designer Palettes */}
      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 flex items-center space-x-1.5">
          <Palette className="w-3 h-3 text-purple-400" />
          <span>Designer Palettes</span>
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {THEME_PALETTES.map((theme) => (
            <div
              key={theme.name}
              className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5"
            >
              <div className="text-[10px] font-medium text-slate-400 truncate">{theme.name}</div>
              <div className="flex gap-1">
                {theme.colors.map((c) => (
                  <button
                    key={c}
                    onClick={() => handleSelectColor(c)}
                    style={{ backgroundColor: c }}
                    className="flex-1 h-5 rounded hover:scale-110 transition border border-black/40"
                    title={`${theme.name}: ${c}`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recently Used Swatches */}
      {recentColors.length > 0 && (
        <div className="space-y-2">
          <label className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 block">
            Recently Used
          </label>
          <div className="flex flex-wrap gap-2">
            {recentColors.map((color, idx) => (
              <button
                key={`${color}-${idx}`}
                onClick={() => handleSelectColor(color)}
                style={{ backgroundColor: color }}
                className="w-6 h-6 rounded-md border border-slate-700/80 hover:scale-110 transition shadow-sm"
                title={color}
              />
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="pt-2 flex flex-col sm:flex-row gap-2">
        <button
          onClick={onApplyToSelection}
          disabled={selectedCount === 0}
          className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-900/30 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center space-x-1.5"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Stage on Selected ({selectedCount})</span>
        </button>

        <button
          onClick={onApplyToAll}
          className="py-2.5 px-4 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition flex items-center justify-center space-x-1"
        >
          <span>Fill All Keys</span>
        </button>
      </div>
    </div>
  );
}
