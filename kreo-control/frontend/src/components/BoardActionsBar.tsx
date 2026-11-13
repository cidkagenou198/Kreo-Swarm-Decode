import {
  Undo2,
  Redo2,
  Save,
  RotateCcw,
  Sparkles,
  Palette,
  Crosshair,
  SlidersHorizontal,
  Flame,
  Check,
  Zap,
} from "lucide-react";

interface BoardActionsBarProps {
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  stagedCount: number;
  onSaveToKeyboard: () => void;
  onDiscardChanges: () => void;
  onSolidFill: () => void;
  onTwoColorSplit: () => void;
  onRainbowWave: () => void;
  onGravaStarFluid: () => void;
  onGamerHighlight: () => void;
  onGlitchEffect: () => void;
  onClearBoard: () => void;
  isSyncing: boolean;
}

export function BoardActionsBar({
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  stagedCount,
  onSaveToKeyboard,
  onDiscardChanges,
  onSolidFill,
  onTwoColorSplit,
  onRainbowWave,
  onGravaStarFluid,
  onGamerHighlight,
  onGlitchEffect,
  onClearBoard,
  isSyncing,
}: BoardActionsBarProps) {
  return (
    <div className="p-3.5 rounded-2xl bg-[#0d131f] border border-slate-800 shadow-md space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Quick Lighting Pattern Generators */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Patterns:</span>
          </span>

          <button
            onClick={onSolidFill}
            className="px-2.5 py-1 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center space-x-1"
            title="Fill all 82 keys with current color"
          >
            <Palette className="w-3 h-3 text-purple-400" />
            <span>Solid Fill</span>
          </button>

          <button
            onClick={onTwoColorSplit}
            className="px-2.5 py-1 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center space-x-1"
            title="Split alpha keys and modifier keys into two distinct colors"
          >
            <SlidersHorizontal className="w-3 h-3 text-indigo-400" />
            <span>Alphas / Modifiers</span>
          </button>

          <button
            onClick={onRainbowWave}
            className="px-2.5 py-1 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center space-x-1"
            title="Apply horizontal rainbow gradient spectrum across columns"
          >
            <Flame className="w-3 h-3 text-amber-400" />
            <span>Rainbow Wave</span>
          </button>

          <button
            onClick={onGravaStarFluid}
            className="px-2.5 py-1 rounded-lg bg-gradient-to-r from-purple-900/60 to-indigo-900/60 hover:from-purple-800 hover:to-indigo-800 text-purple-200 font-semibold border border-purple-500/40 transition flex items-center space-x-1 shadow-sm"
            title="Apply GravaStar Mercury-style multi-harmonic liquid plasma across keyboard"
          >
            <Sparkles className="w-3 h-3 text-cyan-300" />
            <span>GravaStar Fluid</span>
          </button>

          <button
            onClick={onGamerHighlight}
            className="px-2.5 py-1 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-emerald-300 font-semibold border border-emerald-800/50 transition flex items-center space-x-1"
            title="Highlight WASD, Arrows, and Space in vibrant neon"
          >
            <Crosshair className="w-3 h-3 text-emerald-400" />
            <span>FPS Gamer</span>
          </button>

          <button
            onClick={onGlitchEffect}
            className="px-2.5 py-1 rounded-lg bg-red-950/70 hover:bg-red-900/80 text-rose-300 font-semibold border border-rose-600/40 transition flex items-center space-x-1 shadow-sm"
            title="Generate Cyberpunk Glitch clusters in your selected color"
          >
            <Zap className="w-3 h-3 text-rose-400" />
            <span>Cyber Glitch</span>
          </button>

          <button
            onClick={onClearBoard}
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
            title="Turn off all key LEDs"
          >
            <span>Blackout</span>
          </button>
        </div>

        {/* Right: History & Hardware Save Controls */}
        <div className="flex items-center gap-2">
          {/* Undo / Redo */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
            <button
              onClick={onUndo}
              disabled={!canUndo}
              className="p-1.5 rounded-md hover:bg-slate-800 text-slate-300 disabled:opacity-30 disabled:hover:bg-transparent transition"
              title="Undo (Ctrl+Z)"
            >
              <Undo2 className="w-4 h-4" />
            </button>
            <div className="w-[1px] h-4 bg-slate-800" />
            <button
              onClick={onRedo}
              disabled={!canRedo}
              className="p-1.5 rounded-md hover:bg-slate-800 text-slate-300 disabled:opacity-30 disabled:hover:bg-transparent transition"
              title="Redo (Ctrl+Y)"
            >
              <Redo2 className="w-4 h-4" />
            </button>
          </div>

          {/* Staged State Notice & Save Buttons */}
          {stagedCount > 0 ? (
            <div className="flex items-center gap-2 animate-fade-in">
              <span className="text-xs text-amber-400 font-mono font-semibold px-2 py-1 rounded bg-amber-950/40 border border-amber-800/50">
                {stagedCount} unsaved {stagedCount === 1 ? "key" : "keys"}
              </span>

              <button
                onClick={onDiscardChanges}
                disabled={isSyncing}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition flex items-center space-x-1"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Discard</span>
              </button>

              <button
                onClick={onSaveToKeyboard}
                disabled={isSyncing}
                className="px-4 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-900/40 transition flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{isSyncing ? "Saving..." : "Save to Keyboard"}</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center text-xs text-slate-500 font-mono space-x-1 px-2 py-1">
              <Check className="w-3.5 h-3.5 text-emerald-500" />
              <span>Keyboard In Sync</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

