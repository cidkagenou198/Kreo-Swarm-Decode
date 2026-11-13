import { KeyLedInfo } from "../types";

export function hsvToRgb(h: number, s: number, v: number): [number, number, number] {
  h = ((h % 360) + 360) % 360;
  s = Math.max(0, Math.min(1, s));
  v = Math.max(0, Math.min(1, v));

  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;

  let r = 0,
    g = 0,
    b = 0;
  if (h >= 0 && h < 60) {
    r = c;
    g = x;
    b = 0;
  } else if (h >= 60 && h < 120) {
    r = x;
    g = c;
    b = 0;
  } else if (h >= 120 && h < 180) {
    r = 0;
    g = c;
    b = x;
  } else if (h >= 180 && h < 240) {
    r = 0;
    g = x;
    b = c;
  } else if (h >= 240 && h < 300) {
    r = x;
    g = 0;
    b = c;
  } else {
    r = c;
    g = 0;
    b = x;
  }

  return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
}

export function rgbToHex(r: number, g: number, b: number): string {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

export function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  if (clean.length !== 6) return [255, 255, 255];
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  return [isNaN(r) ? 255 : r, isNaN(g) ? 255 : g, isNaN(b) ? 255 : b];
}

/**
 * Generate horizontal rainbow wave gradient across keyboard columns (0..15).
 */
export function generateRainbowWave(keys: KeyLedInfo[], offsetHue: number = 0): Record<string, string> {
  const edits: Record<string, string> = {};
  for (const k of keys) {
    const col = k.col || 0;
    const hue = (offsetHue + (col / 15) * 360) % 360;
    const [r, g, b] = hsvToRgb(hue, 1, 1);
    edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
  }
  return edits;
}

/**
 * Split alphas (letters & numbers) and modifiers into two distinct colors.
 */
export function generateTwoColorSplit(
  keys: KeyLedInfo[],
  alphaColor: string,
  modifierColor: string
): Record<string, string> {
  const edits: Record<string, string> = {};
  const modifierKeys = new Set([
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
    "del",
    "page_up",
    "page_down",
    "end",
    "up",
    "down",
    "left",
    "right",
    "print_screen",
    "knob",
  ]);

  for (const k of keys) {
    const u = k.ui_key.toLowerCase();
    if (modifierKeys.has(u)) {
      edits[u] = modifierColor;
    } else {
      edits[u] = alphaColor;
    }
  }
  return edits;
}

/**
 * High-intensity Gamer preset: WASD + Arrows in accent color, others dimmed/secondary.
 */
export function generateGamerHighlight(
  keys: KeyLedInfo[],
  highlightColor: string = "#00FF66",
  baseColor: string = "#111827"
): Record<string, string> {
  const edits: Record<string, string> = {};
  const gamerKeys = new Set(["w", "a", "s", "d", "up", "down", "left", "right", "space"]);

  for (const k of keys) {
    const u = k.ui_key.toLowerCase();
    if (gamerKeys.has(u)) {
      edits[u] = highlightColor;
    } else {
      edits[u] = baseColor;
    }
  }
  return edits;
}

/**
 * GravaStar Fluid Wave preset: Multi-harmonic liquid plasma across 2D key matrix.
 */
export function generateGravaStarFluidWave(
  keys: KeyLedInfo[],
  offsetHue: number = 0
): Record<string, string> {
  const edits: Record<string, string> = {};
  for (const k of keys) {
    const col = k.col || 0;
    const row = k.row || 0;
    // Harmonic liquid plasma equation
    const plasma =
      Math.sin(col * 0.45) +
      Math.sin(row * 0.9) +
      Math.sin((col + row) * 0.35) +
      Math.sin(Math.sqrt(col * col + row * row) * 0.5);
    const hue = (offsetHue + ((plasma + 4) / 8) * 360) % 360;
    const [r, g, b] = hsvToRgb(hue, 0.95, 1.0);
    edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
  }
  return edits;
}

/**
 * Simulates a frame of a hardware animation for real-time preview in the UI canvas.
 */
export function computeSimulationFrame(
  modeId: number,
  keys: KeyLedInfo[],
  timeMs: number,
  baseColorHex: string = "#FF0000",
  speedLevel: number = 2,
  brightnessLevel: number = 3
): Record<string, string> {
  const speedFactor = 0.5 + speedLevel * 0.75;
  const brightness = Math.max(0.1, brightnessLevel / 4);
  const edits: Record<string, string> = {};
  const [baseR, baseG, baseB] = hexToRgb(baseColorHex);

  switch (modeId) {
    case 1: // Static
      for (const k of keys) {
        const r = Math.round(baseR * brightness);
        const g = Math.round(baseG * brightness);
        const b = Math.round(baseB * brightness);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;

    case 2: { // Breathing
      const period = 3000 / speedFactor;
      const progress = ((timeMs % period) / period) * Math.PI * 2;
      const intensity = (Math.sin(progress) * 0.5 + 0.5) * brightness;
      for (const k of keys) {
        const r = Math.round(baseR * intensity);
        const g = Math.round(baseG * intensity);
        const b = Math.round(baseB * intensity);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 3: // Rainbow (Neon Rainbow)
    case 4: { // Wave
      const period = 4000 / speedFactor;
      const offsetHue = ((timeMs % period) / period) * 360;
      for (const k of keys) {
        const col = k.col || 0;
        const row = k.row || 0;
        const hue = (offsetHue + (col / 15) * 360 + (row / 5) * 45) % 360;
        const [r, g, b] = hsvToRgb(hue, 1, brightness);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 6: { // Rainbow Wheel (GravaStar Rotating Angular Wheel)
      const period = 3200 / speedFactor;
      const t = (timeMs % period) / period;
      const centerCol = 7.5;
      const centerRow = 2.5;
      for (const k of keys) {
        const dx = (k.col || 0) - centerCol;
        const dy = ((k.row || 0) - centerRow) * 1.5;
        const angle = Math.atan2(dy, dx);
        const normAngle = (angle + Math.PI) / (Math.PI * 2);
        const dist = Math.sqrt(dx * dx + dy * dy);
        const hue = ((normAngle + t) * 360 + dist * 10) % 360;
        const [r, g, b] = hsvToRgb(hue, 1.0, brightness);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 11: { // Neon Stream (GravaStar Liquid Chromatic Flow)
      const period = 3500 / speedFactor;
      const t = (timeMs % period) / period;
      for (const k of keys) {
        const col = k.col || 0;
        const row = k.row || 0;
        const wave = Math.sin((col / 4) + t * Math.PI * 2) * 25;
        const hue = (t * 360 + (col / 15) * 240 + (row / 5) * 50 + wave + 360) % 360;
        const [r, g, b] = hsvToRgb(hue, 0.95, brightness);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 13: { // Sine Wave (GravaStar Harmonic Fluid Wave)
      const period = 2600 / speedFactor;
      const t = (timeMs % period) / period;
      for (const k of keys) {
        const col = k.col || 0;
        const row = k.row || 0;
        const phase = (col / 15) * Math.PI * 2 - t * Math.PI * 2;
        const wave = Math.sin(phase) * 0.5 + 0.5;
        const hue = (t * 360 + (col / 15) * 180 + (row / 5) * 40) % 360;
        const val = (0.35 + wave * 0.65) * brightness;
        const [r, g, b] = hsvToRgb(hue, 0.9, val);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 15: { // Rotating Windmill (GravaStar Pinwheel Sweeper)
      const period = 2400 / speedFactor;
      const t = (timeMs % period) / period;
      const centerCol = 7.5;
      const centerRow = 2.5;
      const blades = 4;
      for (const k of keys) {
        const dx = (k.col || 0) - centerCol;
        const dy = ((k.row || 0) - centerRow) * 1.5;
        const angle = Math.atan2(dy, dx);
        const bladePhase = Math.cos(blades * angle - t * Math.PI * 2);
        const intensity = (bladePhase * 0.5 + 0.5) * brightness;
        const hue = (((angle + Math.PI) / (Math.PI * 2)) * 360 + t * 360) % 360;
        const [r, g, b] = hsvToRgb(hue, 1.0, Math.max(0.2 * brightness, intensity));
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 16: { // Colorful Waterfall (GravaStar Cascading Liquid Cascade)
      const period = 2000 / speedFactor;
      const t = (timeMs % period) / period;
      for (const k of keys) {
        const col = k.col || 0;
        const row = k.row || 0;
        const yWave = ((row / 5) - t + 1) % 1;
        const hue = (yWave * 360 + (col / 15) * 60) % 360;
        const shimmer = Math.sin(col * 3 + row * 2 + t * 10) * 0.15 + 0.85;
        const [r, g, b] = hsvToRgb(hue, 0.9, brightness * shimmer);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 18: { // Rotating Storm (GravaStar Orbital Vortex)
      const period = 2200 / speedFactor;
      const t = (timeMs % period) / period;
      const centerCol = 7.5;
      const centerRow = 2.5;
      for (const k of keys) {
        const dx = (k.col || 0) - centerCol;
        const dy = ((k.row || 0) - centerRow) * 1.5;
        const r = Math.sqrt(dx * dx + dy * dy);
        const theta = Math.atan2(dy, dx);
        const spiral = theta - r * 0.6 - t * Math.PI * 4;
        const hue = (((spiral % (Math.PI * 2)) / (Math.PI * 2)) * 360 + 360) % 360;
        const pulse = (Math.sin(r * 1.2 - t * Math.PI * 2) * 0.3 + 0.7) * brightness;
        const [red, grn, blu] = hsvToRgb(hue, 1.0, pulse);
        edits[k.ui_key.toLowerCase()] = rgbToHex(red, grn, blu);
      }
      break;
    }

    case 10: { // Retro Snake
      const colStep = Math.floor((timeMs / (150 / speedFactor)) % 16);
      for (const k of keys) {
        const dist = Math.abs((k.col || 0) - colStep);
        const val = Math.max(0, 1 - dist / 3) * brightness;
        const [r, g, b] = hsvToRgb(120, 1, val);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    case 17: { // Blossoming / Center Ripple
      const centerCol = 7.5;
      const centerRow = 2.5;
      const period = 2000 / speedFactor;
      const radius = ((timeMs % period) / period) * 10;
      for (const k of keys) {
        const dx = (k.col || 0) - centerCol;
        const dy = (k.row || 0) - centerRow;
        const d = Math.sqrt(dx * dx + dy * dy);
        const diff = Math.abs(d - radius);
        const val = Math.max(0, 1 - diff / 2) * brightness;
        const [r, g, b] = hsvToRgb(280, 0.9, val);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
    }

    default: // Default spectrum drift
      for (const k of keys) {
        const period = 5000 / speedFactor;
        const hue = (((timeMs % period) / period) * 360 + (k.led_index / 82) * 360) % 360;
        const [r, g, b] = hsvToRgb(hue, 0.85, brightness);
        edits[k.ui_key.toLowerCase()] = rgbToHex(r, g, b);
      }
      break;
  }

  return edits;
}

