import { useEffect, useRef, useState } from "react";
import {
  Monitor,
  Video,
  VideoOff,
  Radio,
  Sliders,
  Crosshair,
  Maximize2,
  Layers,
  Info,
} from "lucide-react";
import { KeyLedInfo } from "../types";

interface DisplayMapperPanelProps {
  keys: KeyLedInfo[];
  onColorsSampled: (colors: Record<string, string>) => void;
  isHardwareConnected: boolean;
  isActiveTab?: boolean;
}

interface HoverKeyStats {
  ui_key: string;
  label: string;
  xPercent: number;
  yPercent: number;
  pixelX: number;
  pixelY: number;
  sampleRadius: number;
  sampledColor: string;
  rgb: { r: number; g: number; b: number };
}

// Convert RGB to HSV, boost saturation, convert back to RGB
function boostSaturation(r: number, g: number, b: number, boost: number): { r: number; g: number; b: number } {
  let rf = r / 255;
  let gf = g / 255;
  let bf = b / 255;

  const max = Math.max(rf, gf, bf);
  const min = Math.min(rf, gf, bf);
  const delta = max - min;

  let h = 0;
  let s = max === 0 ? 0 : delta / max;
  let v = max;

  if (delta !== 0) {
    if (max === rf) h = ((gf - bf) / delta) % 6;
    else if (max === gf) h = (bf - rf) / delta + 2;
    else h = (rf - gf) / delta + 4;
    h = h * 60;
    if (h < 0) h += 360;
  }

  // Boost saturation
  s = Math.min(1.0, s * boost);

  // Convert back to RGB
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;

  let ro = 0, go = 0, bo = 0;
  if (h >= 0 && h < 60) { ro = c; go = x; bo = 0; }
  else if (h >= 60 && h < 120) { ro = x; go = c; bo = 0; }
  else if (h >= 120 && h < 180) { ro = 0; go = c; bo = x; }
  else if (h >= 180 && h < 240) { ro = 0; go = x; bo = c; }
  else if (h >= 240 && h < 300) { ro = x; go = 0; bo = c; }
  else { ro = c; go = 0; bo = x; }

  return {
    r: Math.round((ro + m) * 255),
    g: Math.round((go + m) * 255),
    b: Math.round((bo + m) * 255),
  };
}

function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) => Math.max(0, Math.min(255, n)).toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

export function DisplayMapperPanel({
  keys,
  onColorsSampled,
  isHardwareConnected,
  isActiveTab = true,
}: DisplayMapperPanelProps) {
  // Capture Stream State
  const [isCapturing, setIsCapturing] = useState<boolean>(false);
  const [captureError, setCaptureError] = useState<string | null>(null);
  const [activeScene, setActiveScene] = useState<"screen" | "gravastar" | "cyberpunk" | "aurora" | "synthwave" | "fire">("gravastar");

  // Mapping Configuration
  const [mappingPreset, setMappingPreset] = useState<"full" | "center" | "bottom" | "custom">("full");
  const [insetX, setInsetX] = useState<number>(0.05); // Horizontal Margin (0 to 0.35)
  const [insetY, setInsetY] = useState<number>(0.08); // Vertical Margin (0 to 0.35)
  const [sampleRadius, setSampleRadius] = useState<number>(14); // Sample radius in px on canvas
  const [saturationBoost, setSaturationBoost] = useState<number>(1.35); // 1.0 to 2.0
  const [smoothness, setSmoothness] = useState<number>(0.4); // 0 (instant) to 0.85 (smooth)

  // Hardware Sync
  const [syncToHardware, setSyncToHardware] = useState<boolean>(false);
  const [hardwareFps, setHardwareFps] = useState<number>(0);
  const [hardwareLatency, setHardwareLatency] = useState<number>(0);

  // Keyboard Layer Overlay Options
  const [showKeyLabels, setShowKeyLabels] = useState<boolean>(true);
  const [showSampleZones, setShowSampleZones] = useState<boolean>(true);
  const [keyOpacity, setKeyOpacity] = useState<number>(0.85);

  // Hover Inspection State
  const [hoveredKey, setHoveredKey] = useState<KeyLedInfo | null>(null);
  const [hoverKeyStats, setHoverKeyStats] = useState<HoverKeyStats | null>(null);

  // References
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Color EMA history cache
  const smoothedColorsRef = useRef<Record<string, { r: number; g: number; b: number }>>({});
  const lastSyncTimeRef = useRef<number>(0);
  const isSyncInProgressRef = useRef<boolean>(false);

  // Maximum row and col for normalization
  const maxRow = 5;
  const maxCol = 15.5;

  // Change preset margins
  const handleSelectPreset = (preset: "full" | "center" | "bottom" | "custom") => {
    setMappingPreset(preset);
    if (preset === "full") {
      setInsetX(0.04);
      setInsetY(0.06);
    } else if (preset === "center") {
      setInsetX(0.18);
      setInsetY(0.20);
    } else if (preset === "bottom") {
      setInsetX(0.06);
      setInsetY(0.50);
    }
  };

  // Start Screen Capture via Browser getDisplayMedia
  const handleStartCapture = async () => {
    try {
      setCaptureError(null);
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: "monitor",
          frameRate: { ideal: 60, max: 60 },
        },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      setIsCapturing(true);
      setActiveScene("screen");

      // Handle user stopping share from browser UI
      stream.getVideoTracks()[0].onended = () => {
        handleStopCapture();
      };
    } catch (err: any) {
      if (err.name !== "NotAllowedError") {
        setCaptureError(err.message || "Failed to initialize screen capture");
      }
    }
  };

  const handleStopCapture = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCapturing(false);
    setActiveScene("cyberpunk");
  };

  // Clean up media streams on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, []);

  // Main Canvas Render & Color Sampling Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    let frameCount = 0;
    let fpsTimer = performance.now();

    const renderLoop = (time: number) => {
      const width = canvas.width;
      const height = canvas.height;

      // 1. Draw Display Content (Live Screen Video OR Procedural Test Pattern)
      if (activeScene === "screen" && videoRef.current && videoRef.current.readyState >= 2) {
        ctx.drawImage(videoRef.current, 0, 0, width, height);
      } else {
        // Procedural animated scenes for instant preview without screen share
        const t = time * 0.001;
        if (activeScene === "gravastar") {
          // GravaStar Mercury Iridescent Chroma Fluid Plasma
          const grad = ctx.createLinearGradient(0, 0, width, height);
          grad.addColorStop(0, "#05051a");
          grad.addColorStop(0.5, "#2b0938");
          grad.addColorStop(1, "#021b38");
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, width, height);

          // Moving multi-orbital harmonic iridescent fluid blooms
          for (let i = 0; i < 4; i++) {
            const cx = (Math.sin(t * 0.85 + (i * Math.PI) / 2) * 0.38 + 0.5) * width;
            const cy = (Math.cos(t * 0.65 + (i * Math.PI) / 2) * 0.32 + 0.5) * height;
            const rad = ctx.createRadialGradient(cx, cy, 20, cx, cy, width * 0.45);
            const hue = (t * 55 + i * 90) % 360;
            rad.addColorStop(0, `hsla(${hue}, 100%, 65%, 0.9)`);
            rad.addColorStop(0.5, `hsla(${(hue + 45) % 360}, 100%, 50%, 0.45)`);
            rad.addColorStop(1, "rgba(0, 0, 0, 0)");
            ctx.fillStyle = rad;
            ctx.beginPath();
            ctx.arc(cx, cy, width * 0.45, 0, Math.PI * 2);
            ctx.fill();
          }
        } else if (activeScene === "cyberpunk") {
          // Cyberpunk Neon Synthwave Grid & Sunset
          const grad = ctx.createLinearGradient(0, 0, 0, height);
          grad.addColorStop(0, "#0d0221");
          grad.addColorStop(0.5, "#541388");
          grad.addColorStop(0.8, "#d90368");
          grad.addColorStop(1, "#f1e9da");
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, width, height);

          // Moving cyan neon streaks
          for (let i = 0; i < 5; i++) {
            const x = (Math.sin(t + i) * 0.4 + 0.5) * width;
            const y = (Math.cos(t * 0.8 + i) * 0.35 + 0.5) * height;
            const rad = ctx.createRadialGradient(x, y, 10, x, y, 140);
            rad.addColorStop(0, "rgba(0, 245, 212, 0.8)");
            rad.addColorStop(1, "rgba(0, 245, 212, 0)");
            ctx.fillStyle = rad;
            ctx.beginPath();
            ctx.arc(x, y, 140, 0, Math.PI * 2);
            ctx.fill();
          }
        } else if (activeScene === "aurora") {
          // Nordic Emerald & Violet Aurora
          const grad = ctx.createLinearGradient(0, 0, width, height);
          grad.addColorStop(0, "#051923");
          grad.addColorStop(0.5, "#006466");
          grad.addColorStop(1, "#0b525b");
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, width, height);

          for (let i = 0; i < 4; i++) {
            const y = (Math.sin(t * 0.6 + i) * 0.3 + 0.5) * height;
            const rad = ctx.createRadialGradient(width * 0.5, y, 30, width * 0.5, y, 220);
            rad.addColorStop(0, i % 2 === 0 ? "rgba(0, 255, 136, 0.7)" : "rgba(179, 136, 255, 0.7)");
            rad.addColorStop(1, "rgba(0, 0, 0, 0)");
            ctx.fillStyle = rad;
            ctx.fillRect(0, 0, width, height);
          }
        } else if (activeScene === "synthwave") {
          // Rainbow Spectrum Wave
          const grad = ctx.createLinearGradient(0, 0, width, 0);
          const hueShift = (t * 50) % 360;
          grad.addColorStop(0, `hsl(${hueShift}, 100%, 50%)`);
          grad.addColorStop(0.25, `hsl(${(hueShift + 90) % 360}, 100%, 50%)`);
          grad.addColorStop(0.5, `hsl(${(hueShift + 180) % 360}, 100%, 50%)`);
          grad.addColorStop(0.75, `hsl(${(hueShift + 270) % 360}, 100%, 50%)`);
          grad.addColorStop(1, `hsl(${hueShift}, 100%, 50%)`);
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, width, height);
        } else {
          // Fire / Inferno
          const grad = ctx.createLinearGradient(0, height, 0, 0);
          grad.addColorStop(0, "#ff4800");
          grad.addColorStop(0.4, "#ff8500");
          grad.addColorStop(0.8, "#ffc300");
          grad.addColorStop(1, "#100007");
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, width, height);
        }
      }

      // 2. Sample Screen Pixels for each Key
      const keyColorsHex: Record<string, string> = {};
      const alpha = Math.max(0.05, 1.0 - smoothness);

      // Read pixel data in bulk from canvas
      const imgData = ctx.getImageData(0, 0, width, height);
      const data = imgData.data;

      for (const k of keys) {
        // Calculate normalized position according to mapping insets
        const normCol = Math.min(1.0, Math.max(0.0, k.col / maxCol));
        const normRow = Math.min(1.0, Math.max(0.0, k.row / maxRow));

        const mappedX = insetX + (1.0 - 2.0 * insetX) * normCol;
        const mappedY = insetY + (1.0 - 2.0 * insetY) * normRow;

        const px = Math.round(mappedX * (width - 1));
        const py = Math.round(mappedY * (height - 1));

        // Sample a neighborhood box of radius R around (px, py)
        const rad = sampleRadius;
        let sumR = 0, sumG = 0, sumB = 0, sampleCount = 0;

        const xMin = Math.max(0, px - rad);
        const xMax = Math.min(width - 1, px + rad);
        const yMin = Math.max(0, py - rad);
        const yMax = Math.min(height - 1, py + rad);

        // Step through samples (stride 2 for performance)
        for (let sy = yMin; sy <= yMax; sy += 3) {
          const rowOffset = sy * width * 4;
          for (let sx = xMin; sx <= xMax; sx += 3) {
            const idx = rowOffset + sx * 4;
            sumR += data[idx];
            sumG += data[idx + 1];
            sumB += data[idx + 2];
            sampleCount++;
          }
        }

        const avgR = sampleCount > 0 ? sumR / sampleCount : 0;
        const avgG = sampleCount > 0 ? sumG / sampleCount : 0;
        const avgB = sampleCount > 0 ? sumB / sampleCount : 0;

        // Apply saturation enhancement
        const boosted = boostSaturation(avgR, avgG, avgB, saturationBoost);

        // Apply Exponential Moving Average (EMA) smoothing
        const uKey = k.ui_key.toLowerCase();
        const prev = smoothedColorsRef.current[uKey] || { r: boosted.r, g: boosted.g, b: boosted.b };
        const smR = prev.r * (1.0 - alpha) + boosted.r * alpha;
        const smG = prev.g * (1.0 - alpha) + boosted.g * alpha;
        const smB = prev.b * (1.0 - alpha) + boosted.b * alpha;

        smoothedColorsRef.current[uKey] = { r: smR, g: smG, b: smB };

        const hex = rgbToHex(Math.round(smR), Math.round(smG), Math.round(smB));
        keyColorsHex[uKey] = hex;

        // If this key is currently hovered, update HUD stats
        if (hoveredKey && hoveredKey.ui_key.toLowerCase() === uKey) {
          setHoverKeyStats({
            ui_key: k.ui_key,
            label: k.label,
            xPercent: Math.round(mappedX * 100),
            yPercent: Math.round(mappedY * 100),
            pixelX: px,
            pixelY: py,
            sampleRadius: rad,
            sampledColor: hex,
            rgb: { r: Math.round(smR), g: Math.round(smG), b: Math.round(smB) },
          });
        }
      }

      // Notify parent for studio keyboard preview
      onColorsSampled(keyColorsHex);

      // 3. Hardware Physical Sync (throttled to ~12-14 FPS to preserve wireless bandwidth)
      const now = performance.now();
      if (isActiveTab && syncToHardware && isHardwareConnected && !isSyncInProgressRef.current) {
        if (now - lastSyncTimeRef.current >= 75) {
          // ~13.3 FPS
          lastSyncTimeRef.current = now;
          isSyncInProgressRef.current = true;
          const t0 = performance.now();

          fetch("/api/ambience/stream-frame", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ colors: keyColorsHex }),
          })
            .then(() => {
              const latency = Math.round(performance.now() - t0);
              setHardwareLatency(latency);
            })
            .catch(() => {})
            .finally(() => {
              isSyncInProgressRef.current = false;
            });
        }
      }

      // Track FPS
      frameCount++;
      if (now - fpsTimer >= 1000) {
        setHardwareFps(frameCount);
        frameCount = 0;
        fpsTimer = now;
      }

      animFrameRef.current = requestAnimationFrame(renderLoop);
    };

    animFrameRef.current = requestAnimationFrame(renderLoop);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [
    activeScene,
    insetX,
    insetY,
    sampleRadius,
    saturationBoost,
    smoothness,
    syncToHardware,
    isHardwareConnected,
    isActiveTab,
    keys,
    hoveredKey,
    onColorsSampled,
  ]);

  return (
    <div className="space-y-6">
      {/* Top Banner & Mode Selector */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-purple-950/40 via-indigo-950/20 to-slate-900 border border-purple-900/50 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-xl bg-purple-600 text-white shadow-lg shadow-purple-600/30">
            <Monitor className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white tracking-wide">
                Virtual Display Mapping & Ambient Screen Sync
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-purple-900/70 text-purple-300 text-[10px] font-mono font-bold border border-purple-700/50 uppercase">
                Phase 5 Real-Time
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
              Maps your monitor's display pixels to individual mechanical keys. Captures pixel clusters
              under each key, averages the color in real-time, and mirrors ambient lighting to your Kreo Swarm 75.
            </p>
          </div>
        </div>

        {/* Live Controls */}
        <div className="flex items-center space-x-3 flex-wrap">
          {!isCapturing ? (
            <button
              onClick={handleStartCapture}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-900/40 transition"
            >
              <Video className="w-4 h-4" />
              <span>Capture Display Stream</span>
            </button>
          ) : (
            <button
              onClick={handleStopCapture}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider bg-red-600/90 hover:bg-red-500 text-white shadow-lg shadow-red-900/40 transition"
            >
              <VideoOff className="w-4 h-4" />
              <span>Stop Capture</span>
            </button>
          )}

          {/* Sync to Hardware Toggle */}
          <button
            onClick={() => setSyncToHardware(!syncToHardware)}
            disabled={!isHardwareConnected}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition border ${
              syncToHardware
                ? "bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500 shadow-lg shadow-emerald-900/40 animate-pulse"
                : "bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700"
            } disabled:opacity-50`}
          >
            <Radio className="w-4 h-4" />
            <span>{syncToHardware ? "Keyboard Synced (LIVE)" : "Sync to Physical Keyboard"}</span>
          </button>
        </div>
      </div>

      {captureError && (
        <div className="p-3 rounded-xl bg-red-950/60 border border-red-700 text-red-200 text-xs flex items-center space-x-2">
          <Info className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span>Screen Capture Error: {captureError}</span>
        </div>
      )}

      {/* Hidden Video element for WebRTC display capture */}
      <video ref={videoRef} className="hidden" playsInline muted autoPlay />

      {/* The Virtual Display Layout Container */}
      <div className="relative rounded-2xl bg-[#070a10] border border-slate-800 p-5 shadow-2xl flex flex-col items-center">
        {/* Monitor Frame & Bezel */}
        <div className="w-full max-w-5xl rounded-2xl border-4 border-slate-800 bg-[#000000] p-3 shadow-2xl relative overflow-hidden group">
          {/* Top Bar of Monitor */}
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-900 text-[11px] text-slate-500 font-mono">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-300 font-semibold">
                {activeScene === "screen" ? "Desktop Display 1 (2560 x 1440)" : `Simulated Scene: ${activeScene.toUpperCase()}`}
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <span>Sampling: {keys.length} Keys ANSI</span>
              <span>•</span>
              <span>Engine: {hardwareFps} FPS</span>
              {syncToHardware && (
                <>
                  <span>•</span>
                  <span className="text-emerald-400 font-bold">Latency: {hardwareLatency}ms</span>
                </>
              )}
            </div>
          </div>

          {/* Display Screen Surface with Keyboard Layer Overlaid */}
          <div className="relative aspect-[16/9] w-full overflow-hidden rounded-lg bg-black flex items-center justify-center">
            {/* The Screen Canvas (Renders screen video or test pattern) */}
            <canvas
              ref={canvasRef}
              width={640}
              height={360}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            />

            {/* The Keyboard Layer Overlay on the Display Layout */}
            <div className="absolute inset-0 w-full h-full pointer-events-auto">
              {keys.map((k) => {
                const normCol = Math.min(1.0, Math.max(0.0, k.col / maxCol));
                const normRow = Math.min(1.0, Math.max(0.0, k.row / maxRow));

                // Position on screen based on insets
                const mappedX = (insetX + (1.0 - 2.0 * insetX) * normCol) * 100;
                const mappedY = (insetY + (1.0 - 2.0 * insetY) * normRow) * 100;

                const curColor = smoothedColorsRef.current[k.ui_key.toLowerCase()];
                const colorHex = curColor
                  ? rgbToHex(Math.round(curColor.r), Math.round(curColor.g), Math.round(curColor.b))
                  : "#00E5FF";

                const isHovered = hoveredKey?.ui_key === k.ui_key;

                return (
                  <div
                    key={k.ui_key}
                    onMouseEnter={() => setHoveredKey(k)}
                    onMouseLeave={() => setHoveredKey(null)}
                    style={{
                      left: `${mappedX}%`,
                      top: `${mappedY}%`,
                      transform: "translate(-50%, -50%)",
                    }}
                    className={`absolute cursor-pointer transition-transform duration-75 select-none ${
                      isHovered ? "z-30 scale-125" : "z-10"
                    }`}
                  >
                    {/* Key Sample Bounding Reticle Box */}
                    {showSampleZones && (
                      <div
                        style={{
                          width: `${sampleRadius * 2.2}px`,
                          height: `${sampleRadius * 2.2}px`,
                          borderColor: isHovered ? "#ffffff" : colorHex,
                        }}
                        className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-md border pointer-events-none transition-all duration-100 ${
                          isHovered
                            ? "border-2 shadow-lg shadow-white/50 bg-white/20"
                            : "border-dashed opacity-50 bg-black/10"
                        }`}
                      />
                    )}

                    {/* Keycap Body with Averaged Pixel Color */}
                    <div
                      style={{
                        backgroundColor: colorHex,
                        opacity: keyOpacity,
                        boxShadow: isHovered
                          ? `0 0 16px ${colorHex}, 0 0 4px #ffffff`
                          : `0 0 8px ${colorHex}88`,
                      }}
                      className={`min-w-[28px] h-6 px-1.5 rounded-md border flex items-center justify-center transition-all ${
                        isHovered
                          ? "border-white text-white font-extrabold"
                          : "border-white/40 text-black/80 font-bold"
                      }`}
                    >
                      {showKeyLabels && (
                        <span
                          className="text-[9px] uppercase tracking-tighter truncate drop-shadow-sm font-mono"
                          style={{
                            color: isHovered ? "#ffffff" : "#000000",
                            textShadow: isHovered ? "0 1px 2px rgba(0,0,0,0.8)" : "none",
                          }}
                        >
                          {k.label}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Crosshair Guidelines when a Key is Hovered */}
              {hoverKeyStats && (
                <div className="absolute inset-0 pointer-events-none z-20">
                  {/* Vertical guide line */}
                  <div
                    style={{ left: `${hoverKeyStats.xPercent}%` }}
                    className="absolute top-0 bottom-0 w-[1px] bg-purple-400/60 border-l border-dashed border-purple-400"
                  />
                  {/* Horizontal guide line */}
                  <div
                    style={{ top: `${hoverKeyStats.yPercent}%` }}
                    className="absolute left-0 right-0 h-[1px] bg-purple-400/60 border-t border-dashed border-purple-400"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Monitor Chin & Stand Indicator */}
          <div className="h-4 bg-slate-900 border-t border-slate-800 flex items-center justify-center">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-ping" />
          </div>
        </div>

        {/* Monitor Base Stand Graphic */}
        <div className="w-32 h-6 bg-gradient-to-b from-slate-800 to-slate-900 border-x border-b border-slate-700/80 rounded-b-lg shadow-md -mt-1 flex items-center justify-center">
          <div className="w-16 h-1 bg-slate-700/60 rounded-full" />
        </div>
        <div className="w-64 h-2 bg-slate-800/80 rounded-full shadow-lg -mt-0.5 border border-slate-700/50" />
      </div>

      {/* Real-time HUD Key Inspection Bar */}
      <div className="p-4 rounded-xl bg-[#0d121c] border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-purple-950/60 text-purple-400 border border-purple-800/40">
            <Crosshair className="w-5 h-5" />
          </div>
          {hoverKeyStats ? (
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-white uppercase">
                  Key: {hoverKeyStats.label} ({hoverKeyStats.ui_key})
                </span>
                <span
                  style={{ backgroundColor: hoverKeyStats.sampledColor }}
                  className="w-4 h-4 rounded-md border border-white/60 shadow-sm"
                />
                <span className="text-xs font-mono font-bold text-purple-300">
                  {hoverKeyStats.sampledColor}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Display Pixel: ({hoverKeyStats.pixelX}px, {hoverKeyStats.pixelY}px) • Screen Offset: {hoverKeyStats.xPercent}%, {hoverKeyStats.yPercent}% • Sample Box: {hoverKeyStats.sampleRadius * 2}x{hoverKeyStats.sampleRadius * 2} px
              </p>
            </div>
          ) : (
            <div>
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Key Inspection HUD
              </span>
              <p className="text-xs text-slate-500">
                Hover over any key on the display layout to inspect its exact screen pixel coordinates and averaged RGB color.
              </p>
            </div>
          )}
        </div>

        {/* Test Scenes Selector (when not capturing) */}
        {!isCapturing && (
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400 font-medium">Test Scene:</span>
            {(["gravastar", "cyberpunk", "aurora", "synthwave", "fire"] as const).map((sc) => (
              <button
                key={sc}
                onClick={() => setActiveScene(sc)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider transition ${
                  activeScene === sc
                    ? "bg-purple-600 text-white shadow-sm"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {sc === "gravastar" ? "GravaStar Fluid" : sc}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Calibration & Mapping Tuning Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Display Region Mapping */}
        <div className="p-4 rounded-xl bg-[#0b101a] border border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-purple-300">
            <Maximize2 className="w-4 h-4" />
            <span>Display Mapping Region</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <button
              onClick={() => handleSelectPreset("full")}
              className={`px-2 py-1.5 rounded-lg border font-medium transition ${
                mappingPreset === "full"
                  ? "bg-purple-600 text-white border-purple-500 shadow-sm"
                  : "bg-slate-900 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              Full Screen
            </button>
            <button
              onClick={() => handleSelectPreset("center")}
              className={`px-2 py-1.5 rounded-lg border font-medium transition ${
                mappingPreset === "center"
                  ? "bg-purple-600 text-white border-purple-500 shadow-sm"
                  : "bg-slate-900 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              Action Center
            </button>
            <button
              onClick={() => handleSelectPreset("bottom")}
              className={`px-2 py-1.5 rounded-lg border font-medium transition ${
                mappingPreset === "bottom"
                  ? "bg-purple-600 text-white border-purple-500 shadow-sm"
                  : "bg-slate-900 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              Bottom Bar
            </button>
          </div>

          <div className="space-y-2 pt-1 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Horizontal Inset Margin</span>
              <span className="font-mono text-purple-300">{Math.round(insetX * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.30"
              step="0.01"
              value={insetX}
              onChange={(e) => {
                setInsetX(parseFloat(e.target.value));
                setMappingPreset("custom");
              }}
              className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />

            <div className="flex justify-between text-slate-400 pt-1">
              <span>Vertical Inset Margin</span>
              <span className="font-mono text-purple-300">{Math.round(insetY * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.45"
              step="0.01"
              value={insetY}
              onChange={(e) => {
                setInsetY(parseFloat(e.target.value));
                setMappingPreset("custom");
              }}
              className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        {/* Card 2: Pixel Sampling & Color Enhancement */}
        <div className="p-4 rounded-xl bg-[#0b101a] border border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-purple-300">
            <Sliders className="w-4 h-4" />
            <span>Sampling & Color Filter</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Sampling Area Radius</span>
              <span className="font-mono text-purple-300">{sampleRadius * 2} px box</span>
            </div>
            <input
              type="range"
              min="6"
              max="32"
              step="2"
              value={sampleRadius}
              onChange={(e) => setSampleRadius(parseInt(e.target.value))}
              className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />

            <div className="flex justify-between text-slate-400 pt-1">
              <span>Vivid Saturation Boost</span>
              <span className="font-mono text-purple-300">{saturationBoost.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="2.0"
              step="0.05"
              value={saturationBoost}
              onChange={(e) => setSaturationBoost(parseFloat(e.target.value))}
              className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />

            <div className="flex justify-between text-slate-400 pt-1">
              <span>Transition Smoothing (EMA)</span>
              <span className="font-mono text-purple-300">{Math.round(smoothness * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.80"
              step="0.05"
              value={smoothness}
              onChange={(e) => setSmoothness(parseFloat(e.target.value))}
              className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        {/* Card 3: Display Overlay View Options */}
        <div className="p-4 rounded-xl bg-[#0b101a] border border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-purple-300">
            <Layers className="w-4 h-4" />
            <span>Keyboard Layer Visibility</span>
          </div>

          <div className="space-y-2.5 text-xs">
            <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800 cursor-pointer hover:border-slate-700">
              <span className="text-slate-300 font-medium">Show Sampling Bounding Reticles</span>
              <input
                type="checkbox"
                checked={showSampleZones}
                onChange={(e) => setShowSampleZones(e.target.checked)}
                className="accent-purple-500 rounded cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800 cursor-pointer hover:border-slate-700">
              <span className="text-slate-300 font-medium">Show Keycap Labels</span>
              <input
                type="checkbox"
                checked={showKeyLabels}
                onChange={(e) => setShowKeyLabels(e.target.checked)}
                className="accent-purple-500 rounded cursor-pointer"
              />
            </label>

            <div className="pt-1">
              <div className="flex justify-between text-slate-400 text-xs">
                <span>Keycap Glow Opacity</span>
                <span className="font-mono text-purple-300">{Math.round(keyOpacity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.3"
                max="1.0"
                step="0.05"
                value={keyOpacity}
                onChange={(e) => setKeyOpacity(parseFloat(e.target.value))}
                className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer mt-1"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
