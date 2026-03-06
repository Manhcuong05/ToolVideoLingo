import re

with open("frontend/src/App.tsx", "r") as f:
    content = f.read()

rename_component = """// ─── Rename Control ─────────────────────────────────────────────────────────
function RenameControl({ url, defaultName, onRename }: { url: string, defaultName: string, onRename: (newUrl: string, newFilename: string) => void }) {
  const [name, setName] = useState(defaultName);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  const old_filename = url.split('/').pop();

  async function handleSave() {
    if(!name.trim() || !old_filename) return;
    setBusy(true); setSaved(false);
    try {
      const res = await fetch(`${API}/api/rename-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_filename, new_filename: name.trim() })
      });
      const data = await res.json();
      if(!res.ok) throw new Error(data.detail || 'Lỗi lưu file');
      setSaved(true);
      onRename(data.new_url, data.new_filename);
    } catch(err:any) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (saved) return <span className="text-xs text-green-400 mt-2 flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> Đã lưu tên mới thành công!</span>;

  return (
    <div className="flex items-center gap-2 mt-2 w-full">
      <input type="text" value={name} onChange={e => setName(e.target.value)} disabled={busy} placeholder="Nhập tên dễ nhớ (vd: video_bai1)..." className="glass-input px-3 py-1.5 text-xs flex-grow" />
      <button onClick={handleSave} disabled={busy || !name.trim()} className="glass-button px-3 py-1.5 text-xs whitespace-nowrap bg-cta/10 hover:bg-cta/20 text-cta border-cta/30">
         {busy ? 'Đang lưu...' : 'Lưu tên file'}
      </button>
    </div>
  );
}

"""

if "function RenameControl" not in content:
    # Insert before "// ─── Tab: Manual Pipeline"
    idx = content.find("// ─── Tab: Manual Pipeline")
    if idx != -1:
        content = content[:idx] + rename_component + content[idx:]


# Enhance TabManual Downloaded section
dl_target = """<p className="text-gray-400 text-xs mt-1">{dlData.title}</p>
              </div>"""
dl_replace = """<p className="text-gray-400 text-xs mt-1">{dlData.title}</p>
                <RenameControl url={dlData.audio_url} defaultName="audio_goc" onRename={(url, fname) => setDlData({...dlData, audio_url: url, audio_filename: fname})} />
              </div>"""

if dl_target in content:
    content = content.replace(dl_target, dl_replace)


# Enhance TabManual TTS section
tts_target = """<h4 className="font-bold text-white text-base">✅ Giọng đọc đã sẵn sàng!</h4>
              <audio controls className="w-full h-10" src={`${API}${ttsData.audio_url}`} />
            </div>
            <a href={`${API}${ttsData.audio_url}`} download"""
tts_replace = """<h4 className="font-bold text-white text-base">✅ Giọng đọc đã sẵn sàng!</h4>
              <audio controls className="w-full h-10" src={`${API}${ttsData.audio_url}`} />
              <RenameControl url={ttsData.audio_url} defaultName="longtieng_final" onRename={(url, fname) => setTtsData({...ttsData, audio_url: url, audio_filename: fname})} />
            </div>
            <a href={`${API}${ttsData.audio_url}`} download"""

if tts_target in content:
    content = content.replace(tts_target, tts_replace)

with open("frontend/src/App.tsx", "w") as f:
    f.write(content)

print("App updated successfully.")

