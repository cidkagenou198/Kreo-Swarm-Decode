import { useState, useRef } from "react";
import {
  X,
  Plus,
  Copy,
  Trash2,
  Download,
  Upload,
  CheckCircle2,
  FolderOpen,
  Edit2,
  Sparkles,
  Zap,
} from "lucide-react";
import { KeyboardProfile } from "../types";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profiles: KeyboardProfile[];
  activeProfileId: string | null;
  onActivateProfile: (profileId: string) => Promise<void>;
  onCreateProfile: (name: string, description: string) => Promise<void>;
  onDuplicateProfile: (profileId: string) => Promise<void>;
  onDeleteProfile: (profileId: string) => Promise<void>;
  onUpdateProfile: (profileId: string, name: string, description: string) => Promise<void>;
  onImportProfile: (data: any) => Promise<void>;
  isSyncing: boolean;
}

export function ProfileModal({
  isOpen,
  onClose,
  profiles,
  activeProfileId,
  onActivateProfile,
  onCreateProfile,
  onDuplicateProfile,
  onDeleteProfile,
  onUpdateProfile,
  onImportProfile,
  isSyncing,
}: ProfileModalProps) {
  const [editingProfileId, setEditingProfileId] = useState<string | null>(null);
  const [editName, setEditName] = useState<string>("");
  const [editDesc, setEditDesc] = useState<string>("");

  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [newName, setNewName] = useState<string>("");
  const [newDesc, setNewDesc] = useState<string>("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleStartEdit = (p: KeyboardProfile) => {
    setEditingProfileId(p.id);
    setEditName(p.name);
    setEditDesc(p.description);
  };

  const handleSaveEdit = async () => {
    if (!editingProfileId) return;
    await onUpdateProfile(editingProfileId, editName, editDesc);
    setEditingProfileId(null);
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await onCreateProfile(newName.trim(), newDesc.trim());
    setNewName("");
    setNewDesc("");
    setIsCreating(false);
  };

  const handleExport = (p: KeyboardProfile) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(p, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `${p.name.toLowerCase().replace(/\s+/g, "_")}.kreo.json`);
    dlAnchor.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (evt) => {
      try {
        const json = JSON.parse(evt.target?.result as string);
        await onImportProfile(json);
      } catch (err) {
        alert("Invalid JSON profile file format.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-3xl rounded-2xl bg-[#0f1420] border border-slate-800 shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-[#111726]/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/40 text-purple-400">
              <FolderOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Profiles Manager</h3>
              <p className="text-xs text-slate-400">
                Save, load, and switch hardware lighting profiles instantly.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white shadow-sm transition"
            >
              <Plus className="w-4 h-4" />
              <span>New Profile</span>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              title="Import .kreo.json"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Import</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".json,.kreo.json"
              className="hidden"
            />

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Create Profile Inline Form */}
        {isCreating && (
          <div className="p-4 bg-purple-950/20 border-b border-purple-900/40 space-y-3 animate-fade-in">
            <div className="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Create New Profile (Snapshots Active Keyboard State)</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Profile Name (e.g. Valorant Pro)"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
              />
              <input
                type="text"
                placeholder="Description (Optional)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setIsCreating(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newName.trim()}
                className="px-4 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </div>
        )}

        {/* Profiles List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3 divide-y divide-slate-800/40">
          {profiles.map((p) => {
            const isActive = p.id === activeProfileId;
            const isEditing = editingProfileId === p.id;
            const keyCount = Object.keys(p.lighting.keys || {}).length;

            return (
              <div
                key={p.id}
                className={`pt-3 first:pt-0 p-4 rounded-xl border transition ${
                  isActive
                    ? "bg-purple-950/20 border-purple-500/60 ring-1 ring-purple-500/30"
                    : "bg-[#0b101a]/70 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                {isEditing ? (
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full bg-slate-900 border border-purple-500 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
                    />
                    <input
                      type="text"
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
                    />
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => setEditingProfileId(null)}
                        className="px-3 py-1 rounded text-xs text-slate-400 hover:text-slate-200"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveEdit}
                        className="px-3 py-1 rounded text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    {/* Left: Metadata */}
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2.5">
                        <span className="text-sm font-bold text-white tracking-wide">
                          {p.name}
                        </span>
                        {isActive && (
                          <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 text-[10px] font-mono font-semibold">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>ACTIVE ON KEYBOARD</span>
                          </span>
                        )}
                        <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-mono">
                          {p.lighting.mode_name}
                        </span>
                      </div>
                      {p.description && (
                        <p className="text-xs text-slate-400 line-clamp-1">{p.description}</p>
                      )}
                      <div className="flex items-center space-x-3 text-[11px] text-slate-500 font-mono pt-0.5">
                        <span>Brightness: {Math.round((p.lighting.brightness / 4) * 100)}%</span>
                        <span>•</span>
                        <span>
                          {p.lighting.is_custom_per_key
                            ? `${keyCount} custom keys`
                            : `Speed: ${p.lighting.speed}/4`}
                        </span>
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center space-x-2">
                      {!isActive && (
                        <button
                          onClick={() => onActivateProfile(p.id)}
                          disabled={isSyncing}
                          className="px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-purple-600 hover:bg-purple-500 text-white shadow-sm transition flex items-center space-x-1"
                        >
                          <Zap className="w-3.5 h-3.5" />
                          <span>Activate</span>
                        </button>
                      )}

                      <button
                        onClick={() => handleStartEdit(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                        title="Rename"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => onDuplicateProfile(p.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                        title="Duplicate"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => handleExport(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                        title="Export JSON"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>

                      {profiles.length > 1 && (
                        <button
                          onClick={() => onDeleteProfile(p.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/40 transition"
                          title="Delete Profile"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

