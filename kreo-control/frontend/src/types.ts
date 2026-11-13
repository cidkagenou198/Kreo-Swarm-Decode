export type ConnectionType = "wired" | "wireless";

export interface DeviceDescriptor {
  vendor_id: number;
  product_id: number;
  usage_page: number;
  usage: number;
  interface_number: number;
  path: string;
  product_name: string;
  product_string: string | null;
  serial_number: string | null;
  connection_type: ConnectionType;
}

export interface DeviceStatusResponse {
  connected: boolean;
  device: DeviceDescriptor | null;
}

export interface RGBColor {
  r: number;
  g: number;
  b: number;
}

export interface LightingState {
  mode_id: number;
  mode_name: string;
  brightness: number;
  speed: number;
  direction: number;
  color_mode: number;
  color: string;
  is_custom_per_key: boolean;
}

export interface KeyLedInfo {
  logical_id: string;
  ui_key: string;
  label: string;
  svg_id: string;
  led_index: number;
  row: number;
  col: number;
  color: string;
}

export interface LightingModeOption {
  id: number;
  name: string;
  key: string;
}

export interface ProfileLightingData {
  mode_id: number;
  mode_name: string;
  brightness: number;
  speed: number;
  direction: number;
  color: string;
  is_custom_per_key: boolean;
  keys: Record<string, string>;
}

export interface KeyboardProfile {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  lighting: ProfileLightingData;
}

export interface ProfilesListResponse {
  active_profile_id: string | null;
  profiles: KeyboardProfile[];
}
