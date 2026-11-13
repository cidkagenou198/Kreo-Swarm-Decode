import { KeyLedInfo } from "../types";
import { Check } from "lucide-react";

interface KeyboardLayoutProps {
  keys: KeyLedInfo[];
  selectedKeys: Set<string>;
  displayColors: Record<string, string>;
  onSelectKey: (uiKey: string, multiSelect: boolean) => void;
  onQuickSelect: (group: string) => void;
  onClearSelection: () => void;
  onInvertSelection: () => void;
}

// 75% Layout Row Structure with key sizes in standard units (u)
interface KeyLayoutDef {
  logicalId: string;
  uiKey: string;
  label: string;
  widthUnits: number;
}

const ROW_DEFS: KeyLayoutDef[][] = [
  // Row 0: Function row (16u total)
  [
    { logicalId: "ESC", uiKey: "esc", label: "Esc", widthUnits: 1 },
    { logicalId: "F1", uiKey: "f1", label: "F1", widthUnits: 1 },
    { logicalId: "F2", uiKey: "f2", label: "F2", widthUnits: 1 },
    { logicalId: "F3", uiKey: "f3", label: "F3", widthUnits: 1 },
    { logicalId: "F4", uiKey: "f4", label: "F4", widthUnits: 1 },
    { logicalId: "F5", uiKey: "f5", label: "F5", widthUnits: 1 },
    { logicalId: "F6", uiKey: "f6", label: "F6", widthUnits: 1 },
    { logicalId: "F7", uiKey: "f7", label: "F7", widthUnits: 1 },
    { logicalId: "F8", uiKey: "f8", label: "F8", widthUnits: 1 },
    { logicalId: "F9", uiKey: "f9", label: "F9", widthUnits: 1 },
    { logicalId: "F10", uiKey: "f10", label: "F10", widthUnits: 1 },
    { logicalId: "F11", uiKey: "f11", label: "F11", widthUnits: 1 },
    { logicalId: "F12", uiKey: "f12", label: "F12", widthUnits: 1 },
    { logicalId: "PRINTSCREEN", uiKey: "print_screen", label: "PrtSc", widthUnits: 1 },
    { logicalId: "KNOB", uiKey: "knob", label: "● Knob", widthUnits: 2 },
  ],
  // Row 1: Number row (16u total)
  [
    { logicalId: "GRAVE", uiKey: "`", label: "~", widthUnits: 1 },
    { logicalId: "1", uiKey: "1", label: "1", widthUnits: 1 },
    { logicalId: "2", uiKey: "2", label: "2", widthUnits: 1 },
    { logicalId: "3", uiKey: "3", label: "3", widthUnits: 1 },
    { logicalId: "4", uiKey: "4", label: "4", widthUnits: 1 },
    { logicalId: "5", uiKey: "5", label: "5", widthUnits: 1 },
    { logicalId: "6", uiKey: "6", label: "6", widthUnits: 1 },
    { logicalId: "7", uiKey: "7", label: "7", widthUnits: 1 },
    { logicalId: "8", uiKey: "8", label: "8", widthUnits: 1 },
    { logicalId: "9", uiKey: "9", label: "9", widthUnits: 1 },
    { logicalId: "0", uiKey: "0", label: "0", widthUnits: 1 },
    { logicalId: "MINUS", uiKey: "-", label: "-", widthUnits: 1 },
    { logicalId: "EQUAL", uiKey: "=", label: "=", widthUnits: 1 },
    { logicalId: "BACKSPACE", uiKey: "backspace", label: "Backspace", widthUnits: 2 },
    { logicalId: "DELETE", uiKey: "del", label: "Del", widthUnits: 1 },
  ],
  // Row 2: QWERTY row (16u total)
  [
    { logicalId: "TAB", uiKey: "tab", label: "Tab", widthUnits: 1.5 },
    { logicalId: "Q", uiKey: "q", label: "Q", widthUnits: 1 },
    { logicalId: "W", uiKey: "w", label: "W", widthUnits: 1 },
    { logicalId: "E", uiKey: "e", label: "E", widthUnits: 1 },
    { logicalId: "R", uiKey: "r", label: "R", widthUnits: 1 },
    { logicalId: "T", uiKey: "t", label: "T", widthUnits: 1 },
    { logicalId: "Y", uiKey: "y", label: "Y", widthUnits: 1 },
    { logicalId: "U", uiKey: "u", label: "U", widthUnits: 1 },
    { logicalId: "I", uiKey: "i", label: "I", widthUnits: 1 },
    { logicalId: "O", uiKey: "o", label: "O", widthUnits: 1 },
    { logicalId: "P", uiKey: "p", label: "P", widthUnits: 1 },
    { logicalId: "LBRACKET", uiKey: "[", label: "[", widthUnits: 1 },
    { logicalId: "RBRACKET", uiKey: "]", label: "]", widthUnits: 1 },
    { logicalId: "BACKSLASH", uiKey: "\\", label: "\\", widthUnits: 1.5 },
    { logicalId: "PAGEUP", uiKey: "page_up", label: "PgUp", widthUnits: 1 },
  ],
  // Row 3: ASDF row (16u total)
  [
    { logicalId: "CAPSLOCK", uiKey: "caps", label: "Caps Lock", widthUnits: 1.75 },
    { logicalId: "A", uiKey: "a", label: "A", widthUnits: 1 },
    { logicalId: "S", uiKey: "s", label: "S", widthUnits: 1 },
    { logicalId: "D", uiKey: "d", label: "D", widthUnits: 1 },
    { logicalId: "F", uiKey: "f", label: "F", widthUnits: 1 },
    { logicalId: "G", uiKey: "g", label: "G", widthUnits: 1 },
    { logicalId: "H", uiKey: "h", label: "H", widthUnits: 1 },
    { logicalId: "J", uiKey: "j", label: "J", widthUnits: 1 },
    { logicalId: "K", uiKey: "k", label: "K", widthUnits: 1 },
    { logicalId: "L", uiKey: "l", label: "L", widthUnits: 1 },
    { logicalId: "SEMICOLON", uiKey: ";", label: ";", widthUnits: 1 },
    { logicalId: "QUOTE", uiKey: "'", label: "'", widthUnits: 1 },
    { logicalId: "ENTER", uiKey: "enter", label: "Enter", widthUnits: 2.25 },
    { logicalId: "PAGEDOWN", uiKey: "page_down", label: "PgDn", widthUnits: 1 },
  ],
  // Row 4: ZXCV row (16u total)
  [
    { logicalId: "LSHIFT", uiKey: "left_shift", label: "Shift", widthUnits: 2.25 },
    { logicalId: "Z", uiKey: "z", label: "Z", widthUnits: 1 },
    { logicalId: "X", uiKey: "x", label: "X", widthUnits: 1 },
    { logicalId: "C", uiKey: "c", label: "C", widthUnits: 1 },
    { logicalId: "V", uiKey: "v", label: "V", widthUnits: 1 },
    { logicalId: "B", uiKey: "b", label: "B", widthUnits: 1 },
    { logicalId: "N", uiKey: "n", label: "N", widthUnits: 1 },
    { logicalId: "M", uiKey: "m", label: "M", widthUnits: 1 },
    { logicalId: "COMMA", uiKey: ",", label: ",", widthUnits: 1 },
    { logicalId: "DOT", uiKey: ".", label: ".", widthUnits: 1 },
    { logicalId: "SLASH", uiKey: "/", label: "/", widthUnits: 1 },
    { logicalId: "RSHIFT", uiKey: "right_shift", label: "Shift", widthUnits: 1.75 },
    { logicalId: "UP", uiKey: "up", label: "▲", widthUnits: 1 },
    { logicalId: "END", uiKey: "end", label: "End", widthUnits: 1 },
  ],
  // Row 5: Modifier row (16u total)
  [
    { logicalId: "LCTRL", uiKey: "left_ctrl", label: "Ctrl", widthUnits: 1.25 },
    { logicalId: "LGUI", uiKey: "left_win", label: "Win", widthUnits: 1.25 },
    { logicalId: "LALT", uiKey: "left_alt", label: "Alt", widthUnits: 1.25 },
    { logicalId: "SPACE", uiKey: "space", label: "Spacebar", widthUnits: 6.25 },
    { logicalId: "RALT", uiKey: "right_alt", label: "Alt", widthUnits: 1 },
    { logicalId: "FN", uiKey: "fn", label: "Fn", widthUnits: 1 },
    { logicalId: "RCTRL", uiKey: "right_ctrl", label: "Ctrl", widthUnits: 1 },
    { logicalId: "LEFT", uiKey: "left", label: "◄", widthUnits: 1 },
    { logicalId: "DOWN", uiKey: "down", label: "▼", widthUnits: 1 },
    { logicalId: "RIGHT", uiKey: "right", label: "►", widthUnits: 1 },
  ],
];

export function KeyboardLayout({
  keys,
  selectedKeys,
  displayColors,
  onSelectKey,
  onQuickSelect,
  onClearSelection,
  onInvertSelection,
}: KeyboardLayoutProps) {
  // Map of uiKey -> color
  const colorMap = new Map<string, string>();
  for (const k of keys) {
    colorMap.set(k.ui_key.toLowerCase(), k.color);
    colorMap.set(k.logical_id.toLowerCase(), k.color);
  }

  return (
    <div className="space-y-4">
      {/* Quick Selection Toolbar (NGENUITY & Wootility Style) */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1">
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-slate-400 font-medium mr-1 uppercase tracking-wider text-[11px]">Select:</span>
          <button
            onClick={() => onQuickSelect("all")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
          >
            All Keys
          </button>
          <button
            onClick={() => onQuickSelect("wasd")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-purple-300 font-semibold border border-purple-800/60 transition"
          >
            WASD
          </button>
          <button
            onClick={() => onQuickSelect("qwer")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
          >
            QWER
          </button>
          <button
            onClick={() => onQuickSelect("numbers")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
          >
            Numbers (1-0)
          </button>
          <button
            onClick={() => onQuickSelect("arrows")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-purple-300 font-semibold border border-purple-800/60 transition"
          >
            Arrows (▲▼◄►)
          </button>
          <button
            onClick={() => onQuickSelect("functions")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
          >
            Functions (F1-F12)
          </button>
          <button
            onClick={() => onQuickSelect("modifiers")}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
          >
            Modifiers
          </button>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <button
            onClick={onInvertSelection}
            className="px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
          >
            Invert
          </button>
          <button
            onClick={onClearSelection}
            className="px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
          >
            Clear Selection ({selectedKeys.size})
          </button>
        </div>
      </div>

      {/* Main Keyboard Chasis (ANSI 75%) */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-b from-[#111624] via-[#0d121c] to-[#090d15] border border-slate-800 shadow-2xl space-y-1.5 select-none">
        {ROW_DEFS.map((row, rowIdx) => (
          <div key={rowIdx} className="flex gap-1.5 justify-between">
            {row.map((kDef) => {
              const u = kDef.uiKey.toLowerCase();
              const isSelected = selectedKeys.has(u);
              const keyColor = displayColors[u] || colorMap.get(u) || "#273240";
              const isKnob = kDef.logicalId === "KNOB";

              return (
                <button
                  key={kDef.logicalId}
                  onClick={(e) => onSelectKey(kDef.uiKey.toLowerCase(), e.shiftKey || e.ctrlKey || e.metaKey)}
                  style={{
                    flex: kDef.widthUnits,
                    boxShadow: isSelected
                      ? `0 0 16px 2px ${keyColor}CC, inset 0 0 10px ${keyColor}66`
                      : `0 0 8px 0px ${keyColor}40, inset 0 0 4px ${keyColor}20`,
                  }}
                  className={`
                    relative h-11 sm:h-12 rounded-lg font-mono text-[11px] sm:text-xs font-semibold
                    flex flex-col items-center justify-between p-1.5 transition-all duration-150
                    border ${isSelected ? "border-purple-400 ring-2 ring-purple-500/60 scale-[1.02] z-10" : "border-slate-800 hover:border-slate-700"}
                    ${isKnob ? "bg-gradient-to-b from-slate-700 to-slate-900 rounded-full text-purple-300" : "bg-[#181f2f] hover:bg-[#1d263a]"}
                  `}
                >
                  {/* Glowing Underglow Dot / Strip */}
                  <div
                    className="w-full h-1 rounded-full transition-all duration-200"
                    style={{
                      backgroundColor: keyColor,
                      boxShadow: `0 0 8px ${keyColor}`,
                    }}
                  />

                  {/* Key Legend */}
                  <span className={`tracking-tight ${isSelected ? "text-white font-bold" : "text-slate-300"}`}>
                    {kDef.label}
                  </span>

                  {/* Selection Mark */}
                  {isSelected && (
                    <div className="absolute top-1 right-1 w-3 h-3 bg-purple-500 rounded-full flex items-center justify-center text-[8px] text-white shadow-sm">
                      <Check className="w-2.5 h-2.5" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
