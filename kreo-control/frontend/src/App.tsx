import { useEffect, useState, useRef } from "react";
import {
  Keyboard,
  RefreshCw,
  Wifi,
  Usb,
  Zap,
  CheckCircle2,
  AlertCircle,
  FolderOpen,
  ChevronDown,
  Plus,
  Check,
  Sliders,
} from "lucide-react";
import {
  DeviceStatusResponse,
  KeyLedInfo,
  LightingState,
  KeyboardProfile,
  ProfilesListResponse,
} from "./types";
import { SvgKeyboardSurface } from "./components/SvgKeyboardSurface";
import { BoardActionsBar } from "./components/BoardActionsBar";
import { ColorPickerPanel } from "./components/ColorPickerPanel";
import { ProfileModal } from "./components/ProfileModal";
import {
  generateGamerHighlight,
  generateRainbowWave,
  generateTwoColorSplit,
  generateGravaStarFluidWave,
  generateCyberpunkGlitch,
} from "./lib/lightingEffects";

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
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set(["w", "a", "s", "d"]));

  // Profile Management State
  const [profiles, setProfiles] = useState<KeyboardProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Staged Editing & History Stack
  const [hardwareColors, setHardwareColors] = useState<Record<string, string>>({});
  const [stagedEdits, setStagedEdits] = useState<Record<string, string>>({});
  const [history, setHistory] = useState<Record<string, string>[]>([{}]);
  const [historyIndex, setHistoryIndex] = useState<number>(0);

  // Active lighting control state
  const [currentColor, setCurrentColor] = useState<string>("#00FF66");
  const [targetBrightness, setTargetBrightness] = useState<number>(4);
  const [autoApply, setAutoApply] = useState<boolean>(true);
  const [paintMode, setPaintMode] = useState<boolean>(false);
  const [activePattern, setActivePattern] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 3500);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsProfileDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [devData, state, keyList, pData] = await Promise.all([
        safeFetchJson<DeviceStatusResponse>("/api/device/status"),
        safeFetchJson<LightingState>("/api/lighting/state"),
        safeFetchJson<KeyLedInfo[]>("/api/lighting/per-key"),
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
        setTargetBrightness(state.brightness);
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

  const commitPerKeyEdits = async (edits: Record<string, string>, toastMsg?: string) => {
    try {
      setSyncing(true);
      const res = await fetch("/api/lighting/per-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ edits }),
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
      if (toastMsg) showToast(toastMsg);

      const newState = await safeFetchJson<LightingState>("/api/lighting/state");
      if (newState) setLightingState(newState);
    } catch (err: any) {
      showToast(err.message || "Failed to commit per-key edits", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleSelectKey = (uiKey: string, multiSelect: boolean) => {
    if (multiSelect) {
      setSelectedKeys((prev) => {
        const next = new Set(prev);
        if (next.has(uiKey)) {
          next.delete(uiKey);
        } else {
          next.add(uiKey);
        }
        return next;
      });
      return;
    }

    setSelectedKeys(new Set([uiKey]));

    if (paintMode) {
      setActivePattern(null);
      if (autoApply) {
        commitPerKeyEdits({ [uiKey]: currentColor });
      } else {
        const updated = { ...stagedEdits, [uiKey]: currentColor };
        pushToHistory(updated);
      }
    }
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

  const handleChangeColor = (newColor: string) => {
    setCurrentColor(newColor);

    if (activePattern === "glitch") {
      const glitch = generateCyberpunkGlitch(keys, newColor);
      if (autoApply) commitPerKeyEdits(glitch, `Cyber Glitch recolored to ${newColor}`);
      else pushToHistory(glitch);
      return;
    }
    if (activePattern === "gamer") {
      const gamer = generateGamerHighlight(keys, newColor, "#111827");
      if (autoApply) commitPerKeyEdits(gamer, `FPS Gamer recolored to ${newColor}`);
      else pushToHistory(gamer);
      return;
    }
    if (activePattern === "solid") {
      const solid: Record<string, string> = {};
      for (const k of keys) solid[k.ui_key.toLowerCase()] = newColor;
      if (autoApply) commitPerKeyEdits(solid, `Solid fill recolored to ${newColor}`);
      else pushToHistory(solid);
      return;
    }

    if (selectedKeys.size > 0) {
      const edits: Record<string, string> = {};
      selectedKeys.forEach((key) => {
        edits[key] = newColor;
      });
      if (autoApply) {
        commitPerKeyEdits(edits, `Applied ${newColor} to ${selectedKeys.size} key(s) on keyboard`);
      } else {
        const updated = { ...stagedEdits, ...edits };
        pushToHistory(updated);
      }
    }
  };

  const handleStageSelectionColor = () => {
    if (selectedKeys.size === 0) return;
    const edits: Record<string, string> = {};
    selectedKeys.forEach((key) => {
      edits[key] = currentColor;
    });
    setActivePattern(null);

    if (autoApply) {
      commitPerKeyEdits(edits, `Applied ${currentColor} to ${selectedKeys.size} key(s) on keyboard`);
    } else {
      const updated = { ...stagedEdits, ...edits };
      pushToHistory(updated);
      showToast(`Staged ${currentColor} on ${selectedKeys.size} key(s)`);
    }
  };

  const handleSolidFill = () => {
    setActivePattern("solid");
    const updated: Record<string, string> = {};
    for (const k of keys) {
      updated[k.ui_key.toLowerCase()] = currentColor;
    }
    if (autoApply) {
      commitPerKeyEdits(updated, `Applied solid fill (${currentColor}) across keyboard`);
    } else {
      pushToHistory(updated);
      showToast(`Staged solid fill (${currentColor}) across all keys`);
    }
  };

  const handleTwoColorSplit = () => {
    setActivePattern("split");
    const split = generateTwoColorSplit(keys, currentColor, "#7B2CBF");
    if (autoApply) {
      commitPerKeyEdits(split, "Applied Alphas & Modifiers two-color split to keyboard");
    } else {
      pushToHistory({ ...stagedEdits, ...split });
      showToast("Staged Alphas & Modifiers two-color split");
    }
  };

  const handleRainbowWave = () => {
    setActivePattern("rainbow");
    const wave = generateRainbowWave(keys, 0);
    if (autoApply) {
      commitPerKeyEdits(wave, "Applied Rainbow Wave gradient across keyboard");
    } else {
      pushToHistory({ ...stagedEdits, ...wave });
      showToast("Staged Rainbow Wave gradient across keyboard");
    }
  };

  const handleGravaStarFluid = () => {
    setActivePattern("fluid");
    const fluid = generateGravaStarFluidWave(keys, 0);
    if (autoApply) {
      commitPerKeyEdits(fluid, "Applied GravaStar Mercury fluid plasma wave across keyboard");
    } else {
      pushToHistory({ ...stagedEdits, ...fluid });
      showToast("Staged GravaStar Mercury fluid plasma wave across keyboard");
    }
  };

  const handleGamerHighlight = () => {
    setActivePattern("gamer");
    const gamer = generateGamerHighlight(keys, currentColor, "#111827");
    if (autoApply) {
      commitPerKeyEdits(gamer, `Applied FPS Gamer highlight (${currentColor}) to keyboard`);
    } else {
      pushToHistory({ ...stagedEdits, ...gamer });
      showToast("Staged FPS Gamer highlight (WASD & Arrows)");
    }
  };

  const handleCyberGlitch = () => {
    setActivePattern("glitch");
    const glitch = generateCyberpunkGlitch(keys, currentColor);
    if (autoApply) {
      commitPerKeyEdits(glitch, `Applied Cyber Glitch (${currentColor}) across keyboard`);
    } else {
      pushToHistory({ ...stagedEdits, ...glitch });
      showToast(`Staged Cyber Glitch in ${currentColor} across keyboard`);
    }
  };

  const handleClearBoard = () => {
    setActivePattern(null);
    const blackout: Record<string, string> = {};
    for (const k of keys) {
      blackout[k.ui_key.toLowerCase()] = "#000000";
    }
    if (autoApply) {
      commitPerKeyEdits(blackout, "Blackout: all keyboard LEDs turned off");
    } else {
      pushToHistory(blackout);
      showToast("Staged blackout (all LEDs off)");
    }
  };

  const handleDiscardChanges = () => {
    setStagedEdits({});
    setHistory([{}]);
    setHistoryIndex(0);
    showToast("Discarded unsaved changes");
  };

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

  const handleUpdateBrightness = async (newBrightness: number) => {
    setTargetBrightness(newBrightness);
    try {
      const res = await fetch("/api/lighting/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: 277,
          brightness: newBrightness,
          speed: 0,
        }),
      });
      const updatedState = await parseResponse<LightingState>(res, "Failed to update brightness");
      setLightingState(updatedState);
      showToast(`Brightness set to level ${newBrightness}`);
    } catch {
      // background silent fail
    }
  };

  const handleActivateProfile = async (id: string) => {
    try {
      setSyncing(true);
      const res = await fetch(`/api/profiles/${id}/activate`, { method: "POST" });
      const activated = await parseResponse<KeyboardProfile>(res, "Failed to activate profile");

      setActiveProfileId(activated.id);
      setProfiles((prev) => prev.map((p) => ({ ...p, is_active: p.id === activated.id })));

      const [s, keyList] = await Promise.all([
        safeFetchJson<LightingState>("/api/lighting/state"),
        safeFetchJson<KeyLedInfo[]>("/api/lighting/per-key"),
      ]);
      if (s) {
        setLightingState(s);
        setTargetBrightness(s.brightness);
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
      const payload = {
        name,
        description,
        lighting: {
          mode_id: 277,
          mode_name: "Custom (Per-Key)",
          brightness: targetBrightness,
          speed: 0,
          direction: 0,
          color: currentColor,
          is_custom_per_key: true,
          keys: mergedKeys,
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

  const activeProfile = profiles.find((p) => p.id === activeProfileId) || profiles[0];

  const displayColors: Record<string, string> = {
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
              Please start the backend (run <code>start-app.ps1</code>).
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

      {/* Main Studio Area */}
      <main className="flex-1 flex flex-col bg-[#090d14] overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-slate-800/80 px-8 flex items-center justify-between bg-[#0b101a]/70 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center space-x-5">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-900/30">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold tracking-wider text-white uppercase">Kreo Control</h1>
                <span className="text-[10px] text-purple-400 font-mono tracking-wider">Swarm 75 Studio</span>
              </div>
            </div>

            {/* Connection Status Pill */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
              <Keyboard className="w-3.5 h-3.5 text-purple-400" />
              <span className="font-semibold text-slate-200">Swarm 75:</span>
              {backendOnline && deviceStatus?.device?.connection_type === "wireless" ? (
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <Wifi className="w-3 h-3" /> 2.4 GHz Wireless
                </span>
              ) : backendOnline && deviceStatus?.connected ? (
                <span className="text-indigo-400 font-medium flex items-center gap-1">
                  <Usb className="w-3 h-3" /> Wired USB
                </span>
              ) : (
                <span className="text-red-400 font-medium flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> Disconnected
                </span>
              )}
              {lightingState && (
                <span className="text-[10px] text-purple-300 font-mono border-l border-slate-700 pl-2 ml-1">
                  {lightingState.mode_name}
                </span>
              )}
            </div>

            {/* Profile Dropdown Selector */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-purple-800/50 hover:border-purple-600 text-slate-200 hover:text-white transition shadow-sm text-xs font-medium"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-slate-400">Profile:</span>
                <span className="font-bold text-purple-300">{activeProfile?.name || "Default"}</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

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
          {/* Action & Pattern Toolbar */}
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
            autoApply={autoApply}
            onToggleAutoApply={() => setAutoApply((prev) => !prev)}
            paintMode={paintMode}
            onTogglePaintMode={() => setPaintMode((prev) => !prev)}
            activePattern={activePattern}
          />

          {/* Quick Key Selection Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">
                Select:
              </span>
              <button
                onClick={() => handleQuickSelect("all")}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
              >
                All Keys
              </button>
              <button
                onClick={() => handleQuickSelect("wasd")}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-purple-300 font-semibold border border-purple-800/60 transition"
              >
                WASD
              </button>
              <button
                onClick={() => handleQuickSelect("arrows")}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-purple-300 font-semibold border border-purple-800/60 transition"
              >
                Arrows
              </button>
              <button
                onClick={() => handleQuickSelect("numbers")}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
              >
                Numbers (1-0)
              </button>
              <button
                onClick={() => handleQuickSelect("functions")}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
              >
                Functions (F1-F12)
              </button>
              <button
                onClick={() => handleQuickSelect("modifiers")}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
              >
                Modifiers
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleInvertSelection}
                className="px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
              >
                Invert
              </button>
              <button
                onClick={handleClearSelection}
                className="px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
              >
                Clear ({selectedKeys.size})
              </button>
            </div>
          </div>

          {/* Interactive Photorealistic Vector Keyboard Surface */}
          <section className="space-y-2">
            <SvgKeyboardSurface
              keys={keys}
              selectedKeys={selectedKeys}
              displayColors={displayColors}
              onSelectKey={handleSelectKey}
            />
          </section>

          {/* Color Picker & Brightness Controls */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <ColorPickerPanel
                currentColor={currentColor}
                onChangeColor={handleChangeColor}
                onApplyToSelection={handleStageSelectionColor}
                onApplyToAll={handleSolidFill}
                selectedCount={selectedKeys.size}
                autoApply={autoApply}
              />
            </div>

            {/* Brightness & Quick Save Card */}
            <div className="p-5 rounded-2xl bg-[#0f1420] border border-slate-800 shadow-xl space-y-6 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Sliders className="w-4 h-4 text-purple-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Hardware Controls
                  </h4>
                </div>

                {/* Brightness Level Slider (0-4) */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">LED Brightness</span>
                    <span className="font-mono font-bold text-purple-300">
                      {targetBrightness} / 4
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="4"
                    step="1"
                    value={targetBrightness}
                    onChange={(e) => handleUpdateBrightness(parseInt(e.target.value, 10))}
                    className="w-full accent-purple-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>OFF</span>
                    <span>25%</span>
                    <span>50%</span>
                    <span>75%</span>
                    <span>100%</span>
                  </div>
                </div>
              </div>

              {/* Save As Profile Button */}
              <div className="space-y-2 pt-4 border-t border-slate-800">
                <button
                  onClick={() => setIsProfileModalOpen(true)}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider bg-purple-600 hover:bg-purple-500 text-white transition shadow-lg shadow-purple-900/30"
                >
                  <Plus className="w-4 h-4" />
                  <span>Save Current as Profile</span>
                </button>
                <p className="text-[10px] text-slate-500 text-center">
                  Save current per-key illumination and colors to hardware profiles
                </p>
              </div>
            </div>
          </div>
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
  );
}
