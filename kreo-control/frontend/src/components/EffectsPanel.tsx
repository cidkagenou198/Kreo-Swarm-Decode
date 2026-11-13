import { Sliders, Sun, Gauge, Zap, ArrowLeftRight, Eye, Sparkles } from "lucide-react";
import { LightingModeOption } from "../types";

interface EffectsPanelProps {
  modes: LightingModeOption[];
  currentModeId: number;
  brightness: number;
  speed: number;
  direction: number;
  livePreview: boolean;
  onChangeMode: (modeId: number) => void;
  onChangeBrightness: (val: number) => void;
  onChangeSpeed: (val: number) => void;
  onChangeDirection: (val: number) => void;
  onToggleLivePreview: () => void;
  onApplyPreset: () => void;
}

export function EffectsPanel({
  modes,
  currentModeId,
  brightness,
  speed,
  direction,
  livePreview,
  onChangeMode,
  onChangeBrightness,
  onChangeSpeed,
  onChangeDirection,
  onToggleLivePreview,
  onApplyPreset,
}: EffectsPanelProps) {
  return (
    <div className="p-5 rounded-2xl bg-[#0f1420] border border-slate-800 shadow-xl space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Hardware Lighting Presets
          </h4>
        </div>

        {/* Live Preview Toggle */}
        <button
          onClick={onToggleLivePreview}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
            livePreview
              ? "bg-purple-950/80 border-purple-500 text-purple-300"
              : "bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200"
          }`}
          title="Toggle animated preview simulation on canvas"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>{livePreview ? "Previewing Animation" : "Preview In Canvas"}</span>
        </button>
      </div>

      {/* Preset Mode Dropdown */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 block">
          Preset Animation
        </label>
        <select
          value={currentModeId}
          onChange={(e) => onChangeMode(Number(e.target.value))}
          className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-sm font-medium text-white focus:outline-none focus:border-purple-500 cursor-pointer"
        >
          {modes.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} {m.id === 277 ? "(Per-Key Custom Mode)" : ""}
            </option>
          ))}
        </select>
      </div>

      {/* GravaStar Fluid 60Hz Silk Presets Quick Picks */}
      <div className="space-y-1.5 pt-1">
        <label className="text-[10px] font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          <span>GravaStar Fluid 60Hz Hardware Presets:</span>
        </label>
        <div className="flex flex-wrap gap-1.5">
          {[
            { id: 11, label: "Neon Stream", tag: "Liquid Flow" },
            { id: 13, label: "Sine Wave", tag: "Harmonic" },
            { id: 6, label: "Rainbow Wheel", tag: "Radial" },
            { id: 18, label: "Rotating Storm", tag: "Vortex" },
            { id: 16, label: "Waterfall", tag: "Cascade" },
            { id: 3, label: "Rainbow Wave", tag: "Spectrum" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => onChangeMode(item.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                currentModeId === item.id
                  ? "bg-cyan-950/80 border-cyan-400 text-cyan-200 shadow-sm"
                  : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Direction & Animation Mode Controls */}
      <div className="flex items-center justify-between pt-1">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 flex items-center space-x-1.5">
          <ArrowLeftRight className="w-3.5 h-3.5 text-slate-400" />
          <span>Wave Direction</span>
        </span>
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
          <button
            onClick={() => onChangeDirection(0)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition ${
              direction === 0
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            L ➔ R / CW
          </button>
          <button
            onClick={() => onChangeDirection(1)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition ${
              direction === 1
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            R ➔ L / CCW
          </button>
        </div>
      </div>

      {/* Global Brightness Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center space-x-1.5 text-slate-400 font-semibold uppercase text-[11px]">
            <Sun className="w-3.5 h-3.5 text-amber-400" />
            <span>Global Brightness</span>
          </span>
          <span className="font-mono text-white font-bold">{Math.round((brightness / 4) * 100)}%</span>
        </div>
        <input
          type="range"
          min={0}
          max={4}
          step={1}
          value={brightness}
          onChange={(e) => onChangeBrightness(Number(e.target.value))}
          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
        />
        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>Off</span>
          <span>25%</span>
          <span>50%</span>
          <span>75%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Animation Speed Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center space-x-1.5 text-slate-400 font-semibold uppercase text-[11px]">
            <Gauge className="w-3.5 h-3.5 text-cyan-400" />
            <span>Animation Speed</span>
          </span>
          <span className="font-mono text-white font-bold">{Math.round((speed / 4) * 100)}%</span>
        </div>
        <input
          type="range"
          min={0}
          max={4}
          step={1}
          value={speed}
          onChange={(e) => onChangeSpeed(Number(e.target.value))}
          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
        />
        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>Slow</span>
          <span>|</span>
          <span>Normal</span>
          <span>|</span>
          <span>Fast</span>
        </div>
      </div>

      {/* Apply Preset Button */}
      <div className="pt-2">
        <button
          onClick={onApplyPreset}
          className="w-full py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider bg-slate-800 hover:bg-slate-700 text-purple-300 hover:text-white border border-purple-900/60 transition shadow-sm flex items-center justify-center space-x-1.5"
        >
          <Zap className="w-3.5 h-3.5" />
          <span>Apply Preset to Keyboard</span>
        </button>
      </div>
    </div>
  );
}
