import { useEffect, useState, useRef, useCallback } from "react";
import {
  Keyboard,
  Sparkles,
  Sliders,
  RefreshCw,
  Wifi,
  Usb,
  ShieldCheck,
  Zap,
  CheckCircle2,
  AlertCircle,
  Eye,
  Grid,
  FolderOpen,
  ChevronDown,
  Layers,
  Plus,
  Check,
  Monitor,
} from "lucide-react";
import {
  DeviceStatusResponse,
  KeyLedInfo,
  LightingModeOption,
  LightingState,
  KeyboardProfile,
  ProfilesListResponse,
} from "./types";
import { SvgKeyboardSurface } from "./components/SvgKeyboardSurface";
import { KeyboardLayout } from "./components/KeyboardLayout";
import { BoardActionsBar } from "./components/BoardActionsBar";
import { ColorPickerPanel } from "./components/ColorPickerPanel";
import { EffectsPanel } from "./components/EffectsPanel";
import { ProfileModal } from "./components/ProfileModal";
import { DisplayMapperPanel } from "./components/DisplayMapperPanel";
import {
  generateGamerHighlight,
  generateRainbowWave,
  generateTwoColorSplit,
  generateGravaStarFluidWave,
  generateCyberpunkGlitch,
  computeSimulationFrame,
} from "./lib/lightingEffects";

// Resilient response parser preventing Unexpected End of JSON Input on gateway / proxy errors
async function parseResponse<T>(res: Response, fallbackError: string): Promise<T> {
  const text = await res.text();
  let parsed: any = null;
  try {
    parsed = text && text.trim() ? JSON.parse(text) : null;
  } catch {
    parsed = null;
  }

  if (!res.ok) {
    const detail =
      parsed?.detail ||
      (res.status === 502 || res.status === 504
        ? "Backend server offline (port 8000). Please start backend service."
        : `${fallbackError} (${res.status})`);
    throw new Error(detail);
  }

  if (parsed === null) {
    throw new Error("Empty response from backend service");
  }

  return parsed as T;
}

// Safe fetch helper that gracefully returns null without throwing on bad/empty responses
async function safeFetchJson<T>(url: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(url, init);
    if (!res.ok) return null;
    const text = await res.text();
    if (!text || !text.trim()) return null;
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

export default function App() {
  const [backendOnline, setBackendOnline] = useState<boolean>(true);
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatusResponse | null>(null);
  const [lightingState, setLightingState] = useState<LightingState | null>(null);
  const [keys, setKeys] = useState<KeyLedInfo[]>([]);
  const [modes, setModes] = useState<LightingModeOption[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set(["w", "a", "s", "d"]));

  // Profile Management State
  const [profiles, setProfiles] = useState<KeyboardProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // View Mode: Photorealistic Studio vs Tactical 75% Mechanical Grid
  const [viewMode, setViewMode] = useState<"studio" | "tactical">("studio");

  // Staged Editing & History Stack
  const [hardwareColors, setHardwareColors] = useState<Record<string, string>>({});
  const [stagedEdits, setStagedEdits] = useState<Record<string, string>>({});
  const [history, setHistory] = useState<Record<string, string>[]>([{}]);
  const [historyIndex, setHistoryIndex] = useState<number>(0);

  // Tab & Customization State (Default to per-key for direct access)
  const [activeTab, setActiveTab] = useState<"perKey" | "presets" | "ambience">("perKey");
  const [currentColor, setCurrentColor] = useState<string>("#00FF66");
  const [targetModeId, setTargetModeId] = useState<number>(3);
  const [targetBrightness, setTargetBrightness] = useState<number>(4);
  const [targetSpeed, setTargetSpeed] = useState<number>(2);
  const [targetDirection, setTargetDirection] = useState<number>(0);

  // Live Simulation Frame State (when previewing animations)
  const [livePreview, setLivePreview] = useState<boolean>(false);
  const [simulationColors, setSimulationColors] = useState<Record<string, string> | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Screen Ambience Live Sampled Colors
  const [ambientLiveColors, setAmbientLiveColors] = useState<Record<string, string> | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  const handleAmbientColorsSampled = useCallback((colors: Record<string, string>) => {
    setAmbientLiveColors(colors);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsProfileDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Push new staged edits to history stack
  const pushToHistory = (newEdits: Record<string, string>) => {
    setStagedEdits(newEdits);
    const updatedHistory = history.slice(0, historyIndex + 1);
    updatedHistory.push(newEdits);
    setHistory(updatedHistory);
    setHistoryIndex(updatedHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const prevIdx = historyIndex - 1;
      setHistoryIndex(prevIdx);
      setStagedEdits(history[prevIdx]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const nextIdx = historyIndex + 1;
      setHistoryIndex(nextIdx);
      setStagedEdits(history[nextIdx]);
    }
  };

  // Fetch initial device state, keys, modes, and profiles
  const fetchAll = async () => {
    try {
      setLoading(true);
      const [devData, state, keyList, modeList, pData] = await Promise.all([
        safeFetchJson<DeviceStatusResponse>("/api/device/status"),
        safeFetchJson<LightingState>("/api/lighting/state"),
        safeFetchJson<KeyLedInfo[]>("/api/lighting/per-key"),
        safeFetchJson<LightingModeOption[]>("/api/lighting/modes"),
        safeFetchJson<ProfilesListResponse>("/api/profiles"),
      ]);

      if (!devData) {
        setBackendOnline(false);
        setFeedback({
          message: "Backend server offline (port 8000). Please run start-app.bat to connect.",
          type: "error",
        });
        return;
      }

      setBackendOnline(true);
      setDeviceStatus(devData);

      if (state) {
        setLightingState(state);
        setTargetModeId(state.mode_id);
        setTargetBrightness(state.brightness);
        setTargetSpeed(state.speed);
        setTargetDirection(state.direction);
        if (state.color) {
          setCurrentColor(state.color);
        }
      }

      if (keyList && keyList.length > 0) {
        setKeys(keyList);
        const hwMap: Record<string, string> = {};
        for (const k of keyList) {
          hwMap[k.ui_key.toLowerCase()] = k.color;
        }
        setHardwareColors(hwMap);
      }

      if (modeList && modeList.length > 0) {
        setModes(modeList);
      }

      if (pData) {
        setProfiles(pData.profiles);
        setActiveProfileId(pData.active_profile_id);
      }
    } catch (err: any) {
      setBackendOnline(false);
      showToast(err.message || "Failed to sync with keyboard", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  // Auto-reconnect poll when backend is offline
  useEffect(() => {
    if (!backendOnline) {
      const interval = setInterval(() => {
        fetch("/api/health")
          .then((r) => {
            if (r.ok) {
              setBackendOnline(true);
              fetchAll();
            }
          })
          .catch(() => {});
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [backendOnline]);

  // Keyboard Shortcuts (Ctrl+Z, Ctrl+Y, Ctrl+S)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        if (e.shiftKey) {
          handleRedo();
        } else {
          handleUndo();
        }
        e.preventDefault();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        handleRedo();
        e.preventDefault();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        handleSaveToKeyboard();
        e.preventDefault();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  // Animation frame loop for live preview simulation
  useEffect(() => {
    if (!livePreview || activeTab !== "presets") {
      setSimulationColors(null);
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
      return;
    }

    let start = performance.now();
    const frame = (time: number) => {
      const elapsed = time - start;
      const sim = computeSimulationFrame(
        targetModeId,
        keys,
        elapsed,
        currentColor,
        targetSpeed,
        targetBrightness
      );
      setSimulationColors(sim);
      animFrameRef.current = requestAnimationFrame(frame);
    };

    animFrameRef.current = requestAnimationFrame(frame);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [livePreview, activeTab, targetModeId, keys, currentColor, targetSpeed, targetBrightness]);

  // Key Selection
  const handleSelectKey = (uiKey: string, multiSelect: boolean) => {
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (multiSelect) {
        if (next.has(uiKey)) {
          next.delete(uiKey);
        } else {
          next.add(uiKey);
        }
      } else {
        if (next.size === 1 && next.has(uiKey)) {
          next.clear();
        } else {
          next.clear();
          next.add(uiKey);
        }
      }
      return next;
    });
  };

  const handleQuickSelect = (group: string) => {
    if (group === "all") {
      setSelectedKeys(new Set(keys.map((k) => k.ui_key.toLowerCase())));
      return;
    }
    const groups: Record<string, string[]> = {
      wasd: ["w", "a", "s", "d"],
      qwer: ["q", "w", "e", "r"],
      arrows: ["up", "down", "left", "right"],
      numbers: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
      functions: Array.from({ length: 12 }, (_, i) => `f${i + 1}`),
      modifiers: [
        "esc",
        "tab",
        "caps",
        "left_shift",
        "right_shift",
        "left_ctrl",
        "left_win",
        "left_alt",
        "space",
        "right_alt",
        "fn",
        "right_ctrl",
        "enter",
        "backspace",
      ],
    };
    if (groups[group]) {
      setSelectedKeys(new Set(groups[group]));
    }
  };

  const handleClearSelection = () => setSelectedKeys(new Set());

  const handleInvertSelection = () => {
    setSelectedKeys((prev) => {
      const next = new Set<string>();
      for (const k of keys) {
        const u = k.ui_key.toLowerCase();
        if (!prev.has(u)) next.add(u);
      }
      return next;
    });
  };

  // Color Change with Live Staging on Selected Keys
  const handleChangeColor = (newColor: string) => {
    setCurrentColor(newColor);
    if (selectedKeys.size > 0 && activeTab === "perKey") {
      const updated = { ...stagedEdits };
      selectedKeys.forEach((key) => {
        updated[key] = newColor;
      });
      pushToHistory(updated);
    } else if (activeTab === "presets") {
      handleUpdatePresetParam(undefined, undefined, undefined, newColor);
    }
  };

  // Staged Edits Actions
  const handleStageSelectionColor = () => {
    if (selectedKeys.size === 0) return;
    const updated = { ...stagedEdits };
    selectedKeys.forEach((key) => {
      updated[key] = currentColor;
    });
    pushToHistory(updated);
    showToast(`Staged ${currentColor} on ${selectedKeys.size} key(s)`);
  };

  const handleSolidFill = () => {
    const updated: Record<string, string> = {};
    for (const k of keys) {
      updated[k.ui_key.toLowerCase()] = currentColor;
    }
    pushToHistory(updated);
    showToast(`Staged solid fill (${currentColor}) across all keys`);
  };

  const handleTwoColorSplit = () => {
    const split = generateTwoColorSplit(keys, currentColor, "#7B2CBF");
    pushToHistory({ ...stagedEdits, ...split });
    showToast("Staged Alphas & Modifiers two-color split");
  };

  const handleRainbowWave = () => {
    const wave = generateRainbowWave(keys, 0);
    pushToHistory({ ...stagedEdits, ...wave });
    showToast("Staged Rainbow Wave gradient across keyboard");
  };

  const handleGravaStarFluid = () => {
    const fluid = generateGravaStarFluidWave(keys, 0);
    pushToHistory({ ...stagedEdits, ...fluid });
    showToast("Staged GravaStar Mercury fluid plasma wave across keyboard");
  };

  const handleGamerHighlight = () => {
    const gamer = generateGamerHighlight(keys, currentColor, "#111827");
    pushToHistory({ ...stagedEdits, ...gamer });
    showToast("Staged FPS Gamer highlight (WASD & Arrows)");
  };

  const handleCyberGlitch = () => {
    const glitch = generateCyberpunkGlitch(keys, currentColor);
    pushToHistory({ ...stagedEdits, ...glitch });
    showToast(`Staged Cyber Glitch in ${currentColor} across keyboard`);
  };

  const handleClearBoard = () => {
    const blackout: Record<string, string> = {};
    for (const k of keys) {
      blackout[k.ui_key.toLowerCase()] = "#000000";
    }
    pushToHistory(blackout);
    showToast("Staged blackout (all LEDs off)");
  };

  const handleDiscardChanges = () => {
    setStagedEdits({});
    setHistory([{}]);
    setHistoryIndex(0);
    showToast("Discarded unsaved changes");
  };

  // Hardware Commit: Save Staged Edits to Keyboard
  const handleSaveToKeyboard = async () => {
    if (Object.keys(stagedEdits).length === 0) return;
    try {
      setSyncing(true);
      const res = await fetch("/api/lighting/per-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ edits: stagedEdits }),
      });

      const updatedKeys = await parseResponse<KeyLedInfo[]>(res, "Hardware per-key write failed");

      setKeys(updatedKeys);
      const hwMap: Record<string, string> = {};
      for (const k of updatedKeys) {
        hwMap[k.ui_key.toLowerCase()] = k.color;
      }
      setHardwareColors(hwMap);
      setStagedEdits({});
      setHistory([{}]);
      setHistoryIndex(0);

      showToast("Saved custom lighting to keyboard hardware!");

      const newState = await safeFetchJson<LightingState>("/api/lighting/state");
      if (newState) {
        setLightingState(newState);
      }
    } catch (err: any) {
      showToast(err.message || "Failed to commit changes", "error");
    } finally {
      setSyncing(false);
    }
  };

  // Instant Mode Select & Hardware Apply
  const handleSelectAndApplyMode = async (modeId: number) => {
    setTargetModeId(modeId);
    try {
      setSyncing(true);
      const res = await fetch("/api/lighting/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: modeId,
          brightness: targetBrightness,
          speed: targetSpeed,
          direction: targetDirection,
          color: currentColor,
        }),
      });

      const updatedState = await parseResponse<LightingState>(res, "Failed to set preset");
      setLightingState(updatedState);
      showToast(`Hardware preset '${updatedState.mode_name}' applied!`);
    } catch (err: any) {
      showToast(err.message || "Failed to apply preset", "error");
    } finally {
      setSyncing(false);
    }
  };

  // Live parameter updater for speed, brightness, direction, and color
  const handleUpdatePresetParam = async (
    newBrightness?: number,
    newSpeed?: number,
    newDirection?: number,
    newColor?: string
  ) => {
    const b = newBrightness !== undefined ? newBrightness : targetBrightness;
    const s = newSpeed !== undefined ? newSpeed : targetSpeed;
    const d = newDirection !== undefined ? newDirection : targetDirection;
    const c = newColor !== undefined ? newColor : currentColor;

    if (newBrightness !== undefined) setTargetBrightness(newBrightness);
    if (newSpeed !== undefined) setTargetSpeed(newSpeed);
    if (newDirection !== undefined) setTargetDirection(newDirection);
    if (newColor !== undefined) setCurrentColor(newColor);

    try {
      const res = await fetch("/api/lighting/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: targetModeId,
          brightness: b,
          speed: s,
          direction: d,
          color: c,
        }),
      });
      const updatedState = await parseResponse<LightingState>(res, "Failed to update preset");
      setLightingState(updatedState);
    } catch {
      // Background silent update
    }
  };

  // Hardware Commit: Apply Preset Animation
  const handleApplyPreset = async () => {
    try {
      setSyncing(true);
      const res = await fetch("/api/lighting/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: targetModeId,
          brightness: targetBrightness,
          speed: targetSpeed,
          direction: targetDirection,
          color: currentColor,
        }),
      });

      const updatedState = await parseResponse<LightingState>(res, "Failed to set preset");
      setLightingState(updatedState);
      showToast(`Hardware preset '${updatedState.mode_name}' applied!`);
    } catch (err: any) {
      showToast(err.message || "Failed to apply preset", "error");
    } finally {
      setSyncing(false);
    }
  };

  // Profile Management Handlers
  const handleActivateProfile = async (id: string) => {
    try {
      setSyncing(true);
      const res = await fetch(`/api/profiles/${id}/activate`, { method: "POST" });
      const activated = await parseResponse<KeyboardProfile>(res, "Failed to activate profile");

      setActiveProfileId(activated.id);
      setProfiles((prev) => prev.map((p) => ({ ...p, is_active: p.id === activated.id })));

      // Refresh hardware lighting state & per-key colors
      const [s, keyList] = await Promise.all([
        safeFetchJson<LightingState>("/api/lighting/state"),
        safeFetchJson<KeyLedInfo[]>("/api/lighting/per-key"),
      ]);
      if (s) {
        setLightingState(s);
        setTargetModeId(s.mode_id);
        setTargetBrightness(s.brightness);
        setTargetSpeed(s.speed);
        setTargetDirection(s.direction);
        if (s.color) setCurrentColor(s.color);
      }
      if (keyList && keyList.length > 0) {
        setKeys(keyList);
        const hwMap: Record<string, string> = {};
        for (const k of keyList) hwMap[k.ui_key.toLowerCase()] = k.color;
        setHardwareColors(hwMap);
        setStagedEdits({});
        setHistory([{}]);
        setHistoryIndex(0);
      }

      showToast(`Activated profile '${activated.name}' on keyboard!`);
      setIsProfileDropdownOpen(false);
    } catch (err: any) {
      showToast(err.message || "Failed to activate profile", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleCreateProfile = async (name: string, description: string) => {
    try {
      setSyncing(true);
      const mergedKeys = { ...hardwareColors, ...stagedEdits };
      const isCustom = lightingState?.is_custom_per_key || activeTab === "perKey";
      const payload = {
        name,
        description,
        lighting: {
          mode_id: isCustom ? 277 : targetModeId,
          mode_name: isCustom
            ? "Custom (Per-Key)"
            : modes.find((m) => m.id === targetModeId)?.name || "Preset",
          brightness: targetBrightness,
          speed: targetSpeed,
          direction: targetDirection,
          color: currentColor,
          is_custom_per_key: isCustom,
          keys: isCustom ? mergedKeys : {},
        },
      };

      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const created = await parseResponse<KeyboardProfile>(res, "Failed to create profile");
      setProfiles((prev) => [...prev, created]);
      showToast(`Profile '${created.name}' created!`);
    } catch (err: any) {
      showToast(err.message || "Failed to create profile", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleDuplicateProfile = async (id: string) => {
    try {
      setSyncing(true);
      const res = await fetch(`/api/profiles/${id}/duplicate`, { method: "POST" });
      const cloned = await parseResponse<KeyboardProfile>(res, "Failed to duplicate profile");
      setProfiles((prev) => [...prev, cloned]);
      showToast(`Duplicated as '${cloned.name}'!`);
    } catch (err: any) {
      showToast(err.message || "Failed to duplicate profile", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleDeleteProfile = async (id: string) => {
    try {
      setSyncing(true);
      const res = await fetch(`/api/profiles/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete profile");
      setProfiles((prev) => prev.filter((p) => p.id !== id));
      showToast("Profile removed");
    } catch (err: any) {
      showToast(err.message || "Failed to delete profile", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleUpdateProfile = async (id: string, name: string, description: string) => {
    try {
      setSyncing(true);
      const res = await fetch(`/api/profiles/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description }),
      });
      const updated = await parseResponse<KeyboardProfile>(res, "Failed to update profile");
      setProfiles((prev) => prev.map((p) => (p.id === id ? updated : p)));
      showToast("Profile updated");
    } catch (err: any) {
      showToast(err.message || "Failed to update profile", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleImportProfile = async (data: any) => {
    try {
      setSyncing(true);
      const res = await fetch("/api/profiles/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const imported = await parseResponse<KeyboardProfile>(res, "Failed to import profile");
      setProfiles((prev) => [...prev, imported]);
      showToast(`Imported profile '${imported.name}'!`);
    } catch (err: any) {
      showToast(err.message || "Failed to import profile", "error");
    } finally {
      setSyncing(false);
    }
  };

  // Find active profile object
  const activeProfile = profiles.find((p) => p.id === activeProfileId) || profiles[0];

  // Effective display colors (hardware + staged diffs, or animation simulation, or ambient sync)
  const displayColors: Record<string, string> =
    activeTab === "ambience" && ambientLiveColors
      ? ambientLiveColors
      : simulationColors || {
          ...hardwareColors,
          ...stagedEdits,
        };

  const stagedCount = Object.keys(stagedEdits).length;

  return (
    <div className="flex h-screen w-screen bg-[#090d14] text-slate-100 font-sans select-none overflow-hidden flex-col">
      {/* Backend Offline Warning Banner */}
      {!backendOnline && (
        <div className="bg-red-950/90 border-b border-red-800 text-red-200 px-6 py-2 flex items-center justify-between text-xs font-medium z-50">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>
              <strong>Backend Disconnected:</strong> Cannot reach API server at http://127.0.0.1:8000.
              Please start the backend (run <code>start-app.bat</code> or <code>uv run uvicorn kreo_control.api.app:app --port 8000</code>).
            </span>
          </div>
          <button
            onClick={fetchAll}
            className="px-3 py-1 rounded bg-red-800 hover:bg-red-700 text-white font-bold text-xs"
          >
            Retry Connection
          </button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <aside className="w-64 border-r border-slate-800/80 bg-[#0d121c] flex flex-col justify-between p-4 flex-shrink-0">
          <div className="space-y-6">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-3 px-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-900/30">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold tracking-wider text-white uppercase">Kreo Control</h1>
                <span className="text-xs text-purple-400 font-mono">Swarm 75 Labs</span>
              </div>
            </div>

            {/* Device Status Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-2">
              <div className="text-[11px] font-semibold tracking-wider uppercase text-slate-400">Target Device</div>
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-purple-950/60 text-purple-400 border border-purple-800/40">
                  <Keyboard className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-slate-100 truncate">Kreo Swarm 75</div>
                  <div className="text-xs text-slate-400 flex items-center space-x-1">
                    {backendOnline && deviceStatus?.device?.connection_type === "wireless" ? (
                      <>
                        <Wifi className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400 font-medium">2.4 GHz Wireless</span>
                      </>
                    ) : backendOnline && deviceStatus?.connected ? (
                      <>
                        <Usb className="w-3 h-3 text-indigo-400" />
                        <span className="text-indigo-400 font-medium">Wired USB</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3 h-3 text-red-400" />
                        <span className="text-red-400 font-medium">Disconnected</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Active Profile Summary Card */}
            <div className="p-3.5 rounded-xl bg-[#111726]/80 border border-purple-900/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold tracking-wider uppercase text-purple-300">
                  Active Profile
                </span>
                <button
                  onClick={() => setIsProfileModalOpen(true)}
                  className="text-[11px] font-semibold text-purple-400 hover:text-purple-300 underline"
                >
                  Manage
                </button>
              </div>
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-purple-600/20 text-purple-400 border border-purple-500/30">
                  <Layers className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-bold text-white truncate">
                    {activeProfile?.name || "Default Profile"}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate">
                    {activeProfile?.lighting.mode_name}
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Menu */}
            <nav className="space-y-1">
              <button
                onClick={() => {
                  setActiveTab("perKey");
                  setLivePreview(false);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  activeTab === "perKey"
                    ? "bg-purple-600/20 text-purple-300 border border-purple-500/40 shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>Interactive Per-Key RGB</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab("ambience");
                  setLivePreview(false);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  activeTab === "ambience"
                    ? "bg-purple-600/20 text-purple-300 border border-purple-500/40 shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <Monitor className="w-4 h-4 text-purple-400" />
                <span>Screen Ambience & Mapper</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab("presets");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  activeTab === "presets"
                    ? "bg-purple-600/20 text-purple-300 border border-purple-500/40 shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <Sliders className="w-4 h-4 text-purple-400" />
                <span>Hardware Preset Effects</span>
              </button>

              <button
                onClick={() => setIsProfileModalOpen(true)}
                className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition"
              >
                <FolderOpen className="w-4 h-4 text-purple-400" />
                <span>Profiles & Presets</span>
              </button>
            </nav>
          </div>

          {/* Status Badge */}
          <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-800/40 text-purple-300 text-xs space-y-1">
            <div className="flex items-center space-x-1.5 font-semibold">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              <span>Kreo Control Active</span>
            </div>
            <p className="text-[11px] text-purple-200/80 leading-relaxed">
              Hardware communication direct over 2.4 GHz RF / Wired USB.
            </p>
          </div>
        </aside>

        {/* Main Studio Area */}
        <main className="flex-1 flex flex-col bg-[#090d14] overflow-y-auto">
          {/* Top Header Bar */}
          <header className="h-16 border-b border-slate-800/80 px-8 flex items-center justify-between bg-[#0b101a]/70 backdrop-blur-md sticky top-0 z-20">
            <div className="flex items-center space-x-5">
              {/* Profile Dropdown Selector */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                  className="flex items-center space-x-2.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-purple-800/50 hover:border-purple-600 text-slate-200 hover:text-white transition shadow-sm text-xs font-medium"
                >
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-slate-400">Profile:</span>
                  <span className="font-bold text-purple-300">{activeProfile?.name || "Default"}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {/* Dropdown Menu */}
                {isProfileDropdownOpen && (
                  <div className="absolute left-0 mt-2 w-64 rounded-xl bg-[#0f1420] border border-slate-800 shadow-2xl py-1 z-30 animate-fade-in divide-y divide-slate-800/60">
                    <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Switch Active Profile
                    </div>
                    <div className="py-1 max-h-56 overflow-y-auto">
                      {profiles.map((p) => {
                        const isActive = p.id === activeProfileId;
                        return (
                          <button
                            key={p.id}
                            onClick={() => handleActivateProfile(p.id)}
                            className={`w-full flex items-center justify-between px-3 py-2 text-xs transition text-left ${
                              isActive
                                ? "bg-purple-950/40 text-purple-300 font-semibold"
                                : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                            }`}
                          >
                            <div className="truncate pr-2">
                              <div>{p.name}</div>
                              <div className="text-[10px] text-slate-500 font-mono">
                                {p.lighting.mode_name}
                              </div>
                            </div>
                            {isActive && <Check className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />}
                          </button>
                        );
                      })}
                    </div>
                    <div className="p-1">
                      <button
                        onClick={() => {
                          setIsProfileDropdownOpen(false);
                          setIsProfileModalOpen(true);
                        }}
                        className="w-full flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold text-purple-400 hover:bg-purple-950/40 transition"
                      >
                        <FolderOpen className="w-3.5 h-3.5" />
                        <span>Manage All Profiles...</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <h2 className="text-xs font-semibold tracking-wide text-slate-300">
                  Hardware Mode:{" "}
                  <span className="text-purple-400 font-mono">
                    {lightingState ? lightingState.mode_name : (backendOnline ? "Querying..." : "Backend Offline")}
                  </span>
                </h2>
                {lightingState?.is_custom_per_key && (
                  <span className="px-2 py-0.5 rounded-full bg-purple-900/60 text-purple-300 text-[10px] font-semibold border border-purple-700/50">
                    Custom Per-Key RGB
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {feedback && (
                <div
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-medium border animate-fade-in ${
                    feedback.type === "success"
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300"
                      : "bg-red-950/80 border-red-700 text-red-300"
                  }`}
                >
                  {feedback.type === "success" ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                  )}
                  <span>{feedback.message}</span>
                </div>
              )}

              {/* View Mode Toggle */}
              <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
                <button
                  onClick={() => setViewMode("studio")}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md transition font-medium ${
                    viewMode === "studio"
                      ? "bg-purple-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Eye className="w-3 h-3" />
                  <span>Studio Render</span>
                </button>
                <button
                  onClick={() => setViewMode("tactical")}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md transition font-medium ${
                    viewMode === "tactical"
                      ? "bg-purple-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Grid className="w-3 h-3" />
                  <span>Tactical Grid</span>
                </button>
              </div>

              <button
                onClick={() => setIsProfileModalOpen(true)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700"
                title="Open Profiles Manager"
              >
                <FolderOpen className="w-3.5 h-3.5 text-purple-400" />
                <span>Profiles</span>
              </button>

              <button
                onClick={fetchAll}
                disabled={loading || syncing}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading || syncing ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
            </div>
          </header>

          {/* Studio Content Container */}
          <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto w-full">
            {/* Studio Tab Navigation */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    setActiveTab("perKey");
                    setLivePreview(false);
                  }}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                    activeTab === "perKey"
                      ? "bg-purple-600 text-white shadow-lg shadow-purple-900/40"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Interactive Per-Key RGB</span>
                </button>

                <button
                  onClick={() => {
                    setActiveTab("ambience");
                    setLivePreview(false);
                  }}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                    activeTab === "ambience"
                      ? "bg-purple-600 text-white shadow-lg shadow-purple-900/40"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  <Monitor className="w-4 h-4" />
                  <span>Screen Ambience & Mapper</span>
                </button>

                <button
                  onClick={() => setActiveTab("presets")}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                    activeTab === "presets"
                      ? "bg-purple-600 text-white shadow-lg shadow-purple-900/40"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  <Sliders className="w-4 h-4" />
                  <span>Hardware Preset Effects</span>
                </button>
              </div>

              {/* Quick Action: Save current lighting as Profile */}
              <button
                onClick={() => setIsProfileModalOpen(true)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-950/60 border border-purple-700/60 text-purple-300 hover:bg-purple-900/60 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Save As Profile</span>
              </button>
            </div>

            {/* Screen Ambience Display Mapper View */}
            {activeTab === "ambience" && (
              <DisplayMapperPanel
                keys={keys}
                onColorsSampled={handleAmbientColorsSampled}
                isHardwareConnected={backendOnline && (deviceStatus?.connected ?? false)}
                isActiveTab={activeTab === "ambience"}
              />
            )}

            {/* Per-Key Toolbar only in perKey tab */}
            {activeTab === "perKey" && (
              <BoardActionsBar
                canUndo={historyIndex > 0}
                canRedo={historyIndex < history.length - 1}
                onUndo={handleUndo}
                onRedo={handleRedo}
                stagedCount={stagedCount}
                onSaveToKeyboard={handleSaveToKeyboard}
                onDiscardChanges={handleDiscardChanges}
                onSolidFill={handleSolidFill}
                onTwoColorSplit={handleTwoColorSplit}
                onRainbowWave={handleRainbowWave}
                onGravaStarFluid={handleGravaStarFluid}
                onGamerHighlight={handleGamerHighlight}
                onGlitchEffect={handleCyberGlitch}
                onClearBoard={handleClearBoard}
                isSyncing={syncing}
              />
            )}

            {/* Interactive Keyboard Layout Canvas */}
            <section className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold tracking-wider text-slate-200 uppercase">
                    Physical Keyboard Surface Preview (Kreo Swarm 75)
                  </h3>
                  <p className="text-xs text-slate-400">
                    {activeTab === "ambience"
                      ? "Live real-time physical illumination mirrored from display pixel sampling."
                      : viewMode === "studio"
                      ? "Interactive Photorealistic Asset Surface — Click keys to select and paint colors."
                      : "Tactical Mechanical Grid Layout — Pro keycap sizing with instant LED glow."}
                  </p>
                </div>
                <div className="flex items-center space-x-3 text-xs">
                  {activeTab === "ambience" ? (
                    <span className="text-emerald-400 font-mono font-semibold flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span>Real-time Screen Mirroring</span>
                    </span>
                  ) : (
                    <span className="text-purple-400 font-mono font-semibold">
                      {selectedKeys.size} keys selected
                    </span>
                  )}
                </div>
              </div>

              {viewMode === "studio" ? (
                <SvgKeyboardSurface
                  keys={keys}
                  selectedKeys={selectedKeys}
                  displayColors={displayColors}
                  onSelectKey={handleSelectKey}
                />
              ) : (
                <KeyboardLayout
                  keys={keys}
                  selectedKeys={selectedKeys}
                  displayColors={displayColors}
                  onSelectKey={handleSelectKey}
                  onQuickSelect={handleQuickSelect}
                  onClearSelection={handleClearSelection}
                  onInvertSelection={handleInvertSelection}
                />
              )}
            </section>

            {/* Customization Panels Grid (Shown in perKey and presets tabs) */}
            {activeTab !== "ambience" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ColorPickerPanel
                  currentColor={currentColor}
                  onChangeColor={handleChangeColor}
                  onApplyToSelection={handleStageSelectionColor}
                  onApplyToAll={handleSolidFill}
                  selectedCount={selectedKeys.size}
                />

                <EffectsPanel
                  modes={modes}
                  currentModeId={targetModeId}
                  brightness={targetBrightness}
                  speed={targetSpeed}
                  direction={targetDirection}
                  livePreview={livePreview}
                  onChangeMode={handleSelectAndApplyMode}
                  onChangeBrightness={(val) => handleUpdatePresetParam(val, undefined, undefined)}
                  onChangeSpeed={(val) => handleUpdatePresetParam(undefined, val, undefined)}
                  onChangeDirection={(val) => handleUpdatePresetParam(undefined, undefined, val)}
                  onToggleLivePreview={() => setLivePreview(!livePreview)}
                  onApplyPreset={handleApplyPreset}
                />
              </div>
            )}
          </div>
        </main>

        {/* Profiles Modal */}
        <ProfileModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          profiles={profiles}
          activeProfileId={activeProfileId}
          onActivateProfile={handleActivateProfile}
          onCreateProfile={handleCreateProfile}
          onDuplicateProfile={handleDuplicateProfile}
          onDeleteProfile={handleDeleteProfile}
          onUpdateProfile={handleUpdateProfile}
          onImportProfile={handleImportProfile}
          isSyncing={syncing}
        />
      </div>
    </div>
  );
}
