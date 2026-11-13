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
  Paintbrush,
  MousePointer,
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
  autoApply: boolean;
  onToggleAutoApply: () => void;
  paintMode: boolean;
  onTogglePaintMode: () => void;
  activePattern: string | null;
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
  autoApply,
  onToggleAutoApply,
  paintMode,
  onTogglePaintMode,
  activePattern,
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
            className={`px-2.5 py-1 rounded-lg border transition flex items-center space-x-1 ${
              activePattern === "solid"
                ? "bg-purple-900/70 border-purple-400 text-purple-200 shadow-sm"
                : "bg-slate-800/90 hover:bg-slate-700 text-slate-200 border-slate-700"
            }`}
            title="Fill all 82 keys with current color"
          >
            <Palette className="w-3 h-3 text-purple-400" />
            <span>Solid Fill</span>
          </button>

          <button
            onClick={onTwoColorSplit}
            className={`px-2.5 py-1 rounded-lg border transition flex items-center space-x-1 ${
              activePattern === "split"
                ? "bg-indigo-900/70 border-indigo-400 text-indigo-200 shadow-sm"
                : "bg-slate-800/90 hover:bg-slate-700 text-slate-200 border-slate-700"
            }`}
            title="Split alpha keys and modifier keys into two distinct colors"
          >
            <SlidersHorizontal className="w-3 h-3 text-indigo-400" />
            <span>Alphas / Modifiers</span>
          </button>

          <button
            onClick={onRainbowWave}
            className={`px-2.5 py-1 rounded-lg border transition flex items-center space-x-1 ${
              activePattern === "rainbow"
                ? "bg-amber-900/70 border-amber-400 text-amber-200 shadow-sm"
                : "bg-slate-800/90 hover:bg-slate-700 text-slate-200 border-slate-700"
            }`}
            title="Apply horizontal rainbow gradient spectrum across columns"
          >
            <Flame className="w-3 h-3 text-amber-400" />
            <span>Rainbow Wave</span>
          </button>

          <button
            onClick={onGravaStarFluid}
            className={`px-2.5 py-1 rounded-lg font-semibold border transition flex items-center space-x-1 shadow-sm ${
              activePattern === "fluid"
                ? "bg-cyan-900/80 border-cyan-400 text-cyan-100 ring-1 ring-cyan-400"
                : "bg-gradient-to-r from-purple-900/60 to-indigo-900/60 hover:from-purple-800 hover:to-indigo-800 text-purple-200 border-purple-500/40"
            }`}
            title="Apply GravaStar Mercury-style multi-harmonic liquid plasma across keyboard"
          >
            <Sparkles className="w-3 h-3 text-cyan-300" />
            <span>GravaStar Fluid</span>
          </button>

          <button
            onClick={onGamerHighlight}
            className={`px-2.5 py-1 rounded-lg font-semibold border transition flex items-center space-x-1 ${
              activePattern === "gamer"
                ? "bg-emerald-900/80 border-emerald-400 text-emerald-100 ring-1 ring-emerald-400"
                : "bg-slate-800/90 hover:bg-slate-700 text-emerald-300 border-emerald-800/50"
            }`}
            title="Highlight WASD, Arrows, and Space in your selected color"
          >
            <Crosshair className="w-3 h-3 text-emerald-400" />
            <span>FPS Gamer</span>
          </button>

          <button
            onClick={onGlitchEffect}
            className={`px-2.5 py-1 rounded-lg font-semibold border transition flex items-center space-x-1 shadow-sm ${
              activePattern === "glitch"
                ? "bg-rose-900/80 border-rose-400 text-rose-100 ring-1 ring-rose-400 animate-pulse"
                : "bg-red-950/70 hover:bg-red-900/80 text-rose-300 border-rose-600/40"
            }`}
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

        {/* Right: Mode Toggles, History & Hardware Save Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Tool Mode: Paint on Click vs Select Keys */}
          <button
            onClick={onTogglePaintMode}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition ${
              paintMode
                ? "bg-purple-950/80 border-purple-500 text-purple-300 shadow-sm"
                : "bg-slate-900/80 border-slate-700 text-slate-400 hover:text-slate-200"
            }`}
            title={paintMode ? "Paint Mode ON: Click any key to paint it immediately" : "Select Mode: Click keys to multi-select"}
          >
            {paintMode ? (
              <>
                <Paintbrush className="w-3.5 h-3.5 text-purple-400" />
                <span>Paint Mode</span>
              </>
            ) : (
              <>
                <MousePointer className="w-3.5 h-3.5 text-slate-400" />
                <span>Select Mode</span>
              </>
            )}
          </button>

          {/* Live Hardware Sync Toggle */}
          <button
            onClick={onToggleAutoApply}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition ${
              autoApply
                ? "bg-emerald-950/70 border-emerald-500/60 text-emerald-300 shadow-sm shadow-emerald-950/50"
                : "bg-slate-900/80 border-slate-700 text-slate-400 hover:text-slate-200"
            }`}
            title={
              autoApply
                ? "Live Hardware Sync ON: Changes reflect on physical keyboard immediately"
                : "Live Hardware Sync OFF: Changes are staged locally until you click Save"
            }
          >
            <Zap className={`w-3.5 h-3.5 ${autoApply ? "text-emerald-400" : "text-slate-500"}`} />
            <span>{autoApply ? "Live Sync ON" : "Live Sync OFF"}</span>
          </button>

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
          {stagedCount > 0 && (
            <button
              onClick={onDiscardChanges}
              disabled={isSyncing}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition flex items-center space-x-1"
              title="Discard staged edits"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Discard ({stagedCount})</span>
            </button>
          )}

          <button
            onClick={onSaveToKeyboard}
            disabled={isSyncing}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition flex items-center space-x-1.5 shadow-md ${
              stagedCount > 0
                ? "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-900/40 animate-pulse"
                : "bg-slate-800/90 hover:bg-slate-700 text-emerald-400 border border-emerald-700/50"
            }`}
            title="Commit per-key lighting to physical keyboard memory"
          >
            {isSyncing ? (
              <span>Saving...</span>
            ) : stagedCount > 0 ? (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>Save ({stagedCount}) to Keyboard</span>
              </>
            ) : (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span>Keyboard In Sync</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
