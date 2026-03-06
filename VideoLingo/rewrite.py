import re

with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

# 1. Imports
content = content.replace(
    "CheckCircle2, AlertCircle, Zap, Music, FileText, Globe\n} from 'lucide-react';",
    "CheckCircle2, AlertCircle, Zap, Music, FileText, Globe, Settings\n} from 'lucide-react';"
)

# 2. Type Tab
content = content.replace(
    "type Tab = 'auto' | 'download' | 'translate' | 'voiceover';",
    "type Tab = 'manual' | 'download' | 'translate' | 'voiceover';"
)

# 3. TABS array
content = content.replace(
    "{ id: 'auto', icon: Zap, label: 'Tự Động', badge: 'HOT' },",
    "{ id: 'manual', icon: Settings, label: 'Chủ Động', badge: 'MỚI' },"
)

# 4. Tab condition
content = content.replace(
    "{tab === 'auto' && <TabAuto />}",
    "{tab === 'manual' && <TabManual />}"
)
content = content.replace(
    "const [tab, setTab] = useState<Tab>('auto');",
    "const [tab, setTab] = useState<Tab>('manual');"
)

# 5. Replace TabAuto with TabManual
# First, extract FPT_VOICES so we can put it above TabManual
fpt_voices = """const FPT_VOICES = [
  { code: 'banmai', label: '🎙️ Ban Mai — Nữ Bắc ⭐', region: 'Bắc' },
  { code: 'leminh', label: '🎙️ Lê Minh — Nam Bắc', region: 'Bắc' },
  { code: 'myan', label: '🎙️ Mỹ An — Nữ Trung', region: 'Trung' },
  { code: 'giahuy', label: '🎙️ Gia Huy — Nam Trung', region: 'Trung' },
  { code: 'ngoclam', label: '🎙️ Ngọc Lam — Nữ Trung', region: 'Trung' },
  { code: 'minhquang', label: '🎙️ Minh Quang — Nam Nam', region: 'Nam' },
  { code: 'linhsan', label: '🎙️ Linh San — Nữ Nam', region: 'Nam' },
  { code: 'lannhi', label: '🎙️ Lan Nhi — Nữ Nam', region: 'Nam' },
];"""

tab_manual = fpt_voices + "\n\n" + """// ─── Tab: Manual Pipeline ──────────────────────────────────────────────────────
function TabManual() {
  const [url, setUrl] = useState('');
  const [targetLang, setTargetLang] = useState('vi');
  
  const [phase, setPhase] = useState<'idle'|'downloading'|'downloaded'|'processing'|'ready'|'ttsing'|'done'>('idle');
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');
  
  const [dlData, setDlData] = useState<any>(null);
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [voice, setVoice] = useState('banmai');
  const [ttsData, setTtsData] = useState<any>(null);

  async function handleDownload(e: React.FormEvent) {
    e.preventDefault();
    if (!url) return;
    setPhase('downloading'); setDlData(null); setOriginalText(''); setTranslatedText(''); setTtsData(null); setError(''); setMsg('Đang tải video/âm thanh...');
    try {
      await readSSEStream(`${API}/api/download-only`, { url }, data => {
        if (data.status === 'processing') setMsg(data.message);
        else if (data.status === 'success') {
          setDlData(data);
          setPhase('downloaded');
        }
        else if (data.status === 'error') throw new Error(data.message);
      });
    } catch (err: any) { setError(err.message); setPhase('idle'); }
  }

  async function handleTranscribe() {
    setPhase('processing'); setError(''); setMsg('AI đang phiên dịch và dịch thuật...');
    try {
      const res = await fetch(`${API}/api/transcribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_filename: dlData.audio_filename, target_language: targetLang }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Lỗi phiên dịch');
      setOriginalText(data.transcription);
      setTranslatedText(data.translation);
      setPhase('ready');
    } catch (err: any) { setError(err.message); setPhase('downloaded'); }
  }

  async function handleTTS() {
    if (!translatedText.trim()) return;
    setPhase('ttsing'); setError(''); setMsg('Đang tạo giọng đọc...');
    try {
      const res = await fetch(`${API}/api/tts-only`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: translatedText.trim(), lang: 'vi', voice }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Lỗi lồng tiếng');
      setTtsData(data);
      setPhase('done');
    } catch (err: any) { setError(err.message); setPhase('ready'); }
  }

  const selectedVoice = FPT_VOICES.find(v => v.code === voice);

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <p className="text-gray-400 text-sm">Trình tự xử lý chủ động: Tải video ➔ Phiên dịch ➔ Chỉnh sửa ➔ Lồng tiếng.</p>
      </div>

      {/* STEP 1: DOWNLOAD */}
      <div className={`flex flex-col gap-4 transition-all duration-500 ${phase !== 'idle' && phase !== 'downloading' ? 'opacity-50' : ''}`}>
        <form onSubmit={handleDownload} className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-grow">
              <Video className="w-4 h-4 text-gray-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input type="url" required value={url} onChange={e => setUrl(e.target.value)} disabled={phase !== 'idle'}
                placeholder="https://www.youtube.com/watch?v=..." className="w-full glass-input px-4 py-3 pl-10 text-sm" />
            </div>
            <select value={targetLang} onChange={e => setTargetLang(e.target.value)} disabled={phase !== 'idle'}
              className="glass-input px-4 py-3 text-sm cursor-pointer border-r-8 border-transparent">
              <option value="vi">🇻🇳 Tiếng Việt</option>
              <option value="en">🇬🇧 English</option>
              <option value="zh">🇨🇳 中文</option>
              <option value="ja">🇯🇵 日本語</option>
              <option value="ko">🇰🇷 한국어</option>
            </select>
            <button type="submit" disabled={phase !== 'idle' || !url}
              className="glass-button flex items-center justify-center gap-2 px-6 py-3 whitespace-nowrap disabled:opacity-50 hover:scale-[1.02] transition-transform text-sm">
              {phase === 'downloading' ? <><Activity className="animate-spin w-4 h-4" /> Đang tải...</> : <><Download className="w-4 h-4" /> Bắt đầu tải</>}
            </button>
          </div>
        </form>
      </div>

      {phase === 'downloading' && (
        <div className="flex items-center gap-3 bg-[#0B0F19]/80 rounded-xl p-5 border border-white/5 animate-fade-in-up">
           <Download className="w-5 h-5 text-cta animate-bounce" />
           <p className="text-gray-300 text-sm animate-pulse">{msg}</p>
        </div>
      )}

      {/* STEP 2: DOWNLOADED RESULT & TRANSLATE TRIGGER */}
      {(phase === 'downloaded' || phase === 'processing' || phase === 'ready' || phase === 'ttsing' || phase === 'done') && dlData && (
        <div className="flex flex-col gap-4 animate-fade-in-up">
          <div className="glass-card p-5 flex flex-col md:flex-row items-center gap-5 border-green-400/20 bg-green-400/5">
            <div className="flex items-center gap-4 flex-grow">
              <CheckCircle2 className="w-8 h-8 text-green-400 shrink-0" />
              <div>
                <p className="text-white font-semibold text-sm">Video đã tải xong!</p>
                <p className="text-gray-400 text-xs mt-1">{dlData.title}</p>
              </div>
            </div>
            <audio controls className="w-full md:w-auto h-10" src={`${API}${dlData.audio_url}`} />
          </div>

          {(phase === 'downloaded' || phase === 'processing') && (
            <button onClick={handleTranscribe} disabled={phase === 'processing'}
              className="glass-button w-full flex items-center justify-center gap-2 py-3 disabled:opacity-50 hover:scale-[1.01] transition-transform text-sm font-semibold bg-gradient-to-r hover:from-cta/80 hover:to-pink-600/80 shadow-[0_0_15px_#E11D484D] border-cta/50 text-white">
              {phase === 'processing' ? <><Activity className="animate-spin w-4 h-4" /> {msg}</> : <><BrainCircuit className="w-4 h-4" /> Bắt đầu Phiên dịch</>}
            </button>
          )}
        </div>
      )}

      {/* STEP 3: TEXT EDITOR */}
      {(phase === 'ready' || phase === 'ttsing' || phase === 'done') && (
        <div className="flex flex-col gap-4 animate-fade-in-up border-t border-white/10 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="glass-card p-0 flex flex-col hover:border-blue-400/30 transition-colors">
              <div className="px-4 py-2.5 border-b border-white/5 bg-white/[0.02]">
                 <span className="text-xs text-blue-400 font-semibold uppercase tracking-wide flex items-center gap-2">
                    <FileText className="w-3 h-3" /> Văn bản gốc
                 </span>
              </div>
              <textarea value={originalText} onChange={e => setOriginalText(e.target.value)} disabled={phase === 'ttsing' || phase === 'done'}
                className="w-full h-48 bg-transparent text-gray-300 text-sm p-4 outline-none resize-none leading-relaxed" />
            </div>
            <div className="glass-card p-0 flex flex-col border-cta/30 hover:shadow-[0_0_15px_#E11D482D] transition-shadow">
              <div className="px-4 py-2.5 border-b border-cta/20 bg-cta/10 flex justify-between items-center">
                 <span className="text-xs text-white font-bold uppercase tracking-wide flex items-center gap-2">
                    <Globe className="w-3 h-3 text-cta" /> Bản dịch
                 </span>
                 <span className="text-[10px] bg-cta/20 text-cta px-2 py-0.5 rounded-full font-medium">Hỗ trợ chỉnh sửa</span>
              </div>
              <textarea value={translatedText} onChange={e => setTranslatedText(e.target.value)} disabled={phase === 'ttsing' || phase === 'done'}
                className="w-full h-48 bg-transparent text-white text-sm p-4 outline-none resize-none leading-relaxed" />
            </div>
          </div>
          
          <div className="flex flex-col gap-3 mt-2">
             <p className="text-xs text-gray-400 text-center">Bạn có thể sửa trực tiếp bản dịch ở ô bên phải cho đến khi ưng ý, sau đó chọn giọng và lồng tiếng.</p>
             <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {FPT_VOICES.map(v => (
                  <button key={v.code} type="button" onClick={() => setVoice(v.code)} disabled={phase === 'ttsing' || phase === 'done'}
                    className={`flex flex-col items-center gap-1 py-3 px-2 rounded-xl border text-xs font-medium transition-all ${voice === v.code
                        ? 'bg-cta/20 border-cta text-white shadow-[0_0_12px_#E11D483D]'
                        : 'border-white/10 bg-white/[0.03] text-gray-400 hover:border-white/20 hover:text-white'
                      }`}>
                    <span className="text-lg">🎙️</span>
                    <span className="text-center leading-tight">{v.label.replace('🎙️ ', '').split(' — ')[0]}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${v.region === 'Bắc' ? 'bg-blue-500/20 text-blue-300' :
                        v.region === 'Trung' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-green-500/20 text-green-300'
                      }`}>{v.region}</span>
                  </button>
                ))}
            </div>
            {phase !== 'done' && (
              <button onClick={handleTTS} disabled={phase === 'ttsing' || !translatedText.trim()}
                className="glass-button w-full flex items-center justify-center gap-2 py-3 disabled:opacity-50 hover:scale-[1.01] transition-transform text-sm font-bold mt-2 shadow-[0_0_15px_#E11D484D] border-cta/50">
                {phase === 'ttsing' ? <><Activity className="animate-spin w-4 h-4" /> {msg}</> : <><Mic className="w-4 h-4" /> Tạo lồng tiếng — {selectedVoice?.label.replace('🎙️ ', '').split(' — ')[0]}</>}
              </button>
            )}
          </div>
        </div>
      )}

      {/* STEP 4: DONE */}
      {phase === 'done' && ttsData && (
        <div className="flex flex-col gap-4 animate-fade-in-up border-t border-white/10 pt-6 mt-2">
          <div className="glass-card p-6 flex flex-col sm:flex-row items-center gap-5 border-cta/30 bg-gradient-to-r from-transparent to-cta/5 shadow-[0_0_30px_#E11D483D] scale-[1.02]">
            <div className="w-14 h-14 rounded-full bg-cta/20 flex items-center justify-center shrink-0 border border-cta/30 shadow-[0_0_15px_#E11D484D]">
              <Music className="w-7 h-7 text-cta" />
            </div>
            <div className="w-full flex flex-col gap-2">
              <h4 className="font-bold text-white text-base">✅ Giọng đọc đã sẵn sàng!</h4>
              <audio controls className="w-full h-10" src={`${API}${ttsData.audio_url}`} />
            </div>
            <a href={`${API}${ttsData.audio_url}`} download
              className="flex-shrink-0 px-6 py-3 rounded-xl bg-gradient-to-r from-cta to-pink-600 hover:from-pink-600 hover:to-cta text-white font-bold text-sm flex items-center gap-2 whitespace-nowrap transition-all hover:scale-105 shadow-[0_0_15px_#E11D484D]">
              <Download className="w-4 h-4" /> Tải về
            </a>
          </div>
          <button onClick={() => { setPhase('idle'); setUrl(''); setDlData(null); setOriginalText(''); setTranslatedText(''); setTtsData(null); }}
             className="text-gray-400 text-sm hover:text-white transition-colors py-2 flex items-center justify-center gap-2">
             <span className="text-xl">+</span> Bắt đầu tải video mới
          </button>
        </div>
      )}

      {error && <div className="flex items-center gap-2 text-red-500 bg-red-400/10 border border-red-400/30 px-4 py-3 rounded-xl text-sm font-medium mt-2"><AlertCircle className="w-5 h-5 shrink-0" />{error}</div>}
    </div>
  );
}
"""

start_idx = content.find('// ─── Tab: Auto Pipeline')
end_idx = content.find('// ─── Tab: Download Only')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + tab_manual + "\n" + content[end_idx:]

with open('frontend/src/App.tsx', 'w') as f:
    f.write(content)

print("Rewrite successful")
