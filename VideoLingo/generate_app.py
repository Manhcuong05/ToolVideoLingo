import re

content_v1 = """import { useState, useRef } from 'react';
import {
  Video, Languages, Activity, Download, BrainCircuit, Mic,
  CheckCircle2, AlertCircle, Zap, Music, FileText, Globe, Settings
} from 'lucide-react';

type Tab = 'manual' | 'download' | 'translate' | 'voiceover';

const API = 'http://localhost:8000';

function downloadTextFile(text: string, defaultFilename: string) {
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = defaultFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── Shared helpers ─────────────────────────────────────────────────────────
async function readSSEStream(
  url: string, body: object,
  onEvent: (data: any) => void
) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error('Server error: ' + response.status);
  const reader = response.body!.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\\n\\n');
    buffer = events.pop() || '';
    for (const event of events) {
      if (event.startsWith('data: ')) {
        const dataStr = event.substring(6).trim();
        if (dataStr) onEvent(JSON.parse(dataStr));
      }
    }
  }
}

// ─── Progress Stepper ───────────────────────────────────────────────────────
const DL_STEPS = [
  { id: 'downloading', icon: Download, label: 'Đang tải' },
  { id: 'done', icon: CheckCircle2, label: 'Xong' },
];

function Stepper({ steps, currentStep, message }: { steps: typeof DL_STEPS; currentStep: string; message: string }) {
  const currentIdx = Math.max(0, steps.findIndex(s => s.id === currentStep));
  return (
    <div className="w-full flex flex-col gap-5 bg-[#0B0F19]/80 rounded-2xl p-7 border border-white/5 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cta/5 to-transparent -translate-x-full animate-[shimmer_2s_infinite]"></div>
      <div className="flex flex-col items-center gap-1 z-10">
        <p className="text-white font-medium flex items-center gap-2"><Activity className="w-4 h-4 text-cta animate-pulse" /> Đang xử lý</p>
        <p className="text-gray-400 text-sm animate-pulse">{message}</p>
      </div>
      <div className="flex items-center justify-between w-full relative px-4 z-10">
        <div className="absolute top-5 left-[10%] right-[10%] h-[2px] bg-white/10 rounded-full"></div>
        <div
          className="absolute top-5 left-[10%] h-[2px] bg-gradient-to-r from-cta to-pink-500 rounded-full transition-all duration-700 shadow-[0_0_10px_#E11D484D]"
          style={{ width: `${(currentIdx / (steps.length - 1)) * 80}%` }}
        ></div>
        {steps.map((s, i) => {
          const Icon = s.icon;
          const active = i === currentIdx, past = i < currentIdx;
          return (
            <div key={s.id} className="flex flex-col items-center gap-2 w-1/4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 relative ${active ? 'bg-[#1a0b12] border-cta text-cta shadow-[0_0_20px_#E11D484D] scale-110' : past ? 'bg-cta border-cta text-white' : 'bg-[#0f172a] border-white/10 text-gray-600 scale-95'}`}>
                <Icon className={`w-5 h-5 ${active && i < steps.length - 1 ? 'animate-bounce' : ''}`} />
                {active && <div className="absolute inset-0 rounded-full border border-cta animate-ping opacity-20"></div>}
              </div>
              <span className={`text-xs font-medium text-center ${active ? 'text-white' : past ? 'text-gray-300' : 'text-gray-600'}`}>{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const FPT_VOICES = [
  { code: 'banmai', label: '🎙️ Ban Mai — Nữ Bắc ⭐', region: 'Bắc' },
  { code: 'leminh', label: '🎙️ Lê Minh — Nam Bắc', region: 'Bắc' },
  { code: 'myan', label: '🎙️ Mỹ An — Nữ Trung', region: 'Trung' },
  { code: 'giahuy', label: '🎙️ Gia Huy — Nam Trung', region: 'Trung' },
  { code: 'ngoclam', label: '🎙️ Ngọc Lam — Nữ Trung', region: 'Trung' },
  { code: 'minhquang', label: '🎙️ Minh Quang — Nam Nam', region: 'Nam' },
  { code: 'linhsan', label: '🎙️ Linh San — Nữ Nam', region: 'Nam' },
  { code: 'lannhi', label: '🎙️ Lan Nhi — Nữ Nam', region: 'Nam' },
];

// ─── Rename Control ─────────────────────────────────────────────────────────
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

  if (saved) return <span className="text-xs text-green-400 mt-2 flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> Đã lưu báo tên mới thành công!</span>;

  return (
    <div className="flex items-center gap-2 mt-2 w-full">
      <input type="text" value={name} onChange={e => setName(e.target.value)} disabled={busy} placeholder="Nhập tên dễ nhớ (vd: video_bai1)..." className="glass-input px-3 py-1.5 text-xs flex-grow" />
      <button onClick={handleSave} disabled={busy || !name.trim()} className="glass-button px-3 py-1.5 text-xs whitespace-nowrap bg-cta/10 hover:bg-cta/20 text-cta border-cta/30">
         {busy ? 'Đang lưu...' : 'Lưu tên file'}
      </button>
    </div>
  );
}

// ─── Tab: Manual Pipeline ──────────────────────────────────────────────────────
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
              <option value="ko">🇰�� 한국어</option>
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
                <RenameControl url={dlData.audio_url} defaultName="audio_goc" onRename={(url, fname) => setDlData({...dlData, audio_url: url, audio_filename: fname})} />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <audio controls className="w-full md:w-auto h-10" src={`${API}${dlData.audio_url}`} />
              <a href={`${API}${dlData.audio_url}`} download 
                 className="flex items-center justify-center gap-2 text-xs py-1.5 px-3 rounded text-white bg-cta/80 hover:bg-cta transition-colors">
                <Download className="w-3 h-3"/> Tải Audio
              </a>
            </div>
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
              <div className="px-4 py-2.5 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                 <span className="text-xs text-blue-400 font-semibold uppercase tracking-wide flex items-center gap-2">
                    <FileText className="w-3 h-3" /> Văn bản gốc
                 </span>
                 <button onClick={() => downloadTextFile(originalText, "van_ban_goc.txt")} className="text-xs text-white bg-blue-500/20 hover:bg-blue-500/40 px-2 py-1 rounded flex items-center gap-1 transition-colors">
                    <Download className="w-3 h-3"/> Tải .txt
                 </button>
              </div>
              <textarea value={originalText} onChange={e => setOriginalText(e.target.value)} disabled={phase === 'ttsing' || phase === 'done'}
                className="w-full h-48 bg-transparent text-gray-300 text-sm p-4 outline-none resize-none leading-relaxed" />
            </div>
            <div className="glass-card p-0 flex flex-col border-cta/30 hover:shadow-[0_0_15px_#E11D482D] transition-shadow">
              <div className="px-4 py-2.5 border-b border-cta/20 bg-cta/10 flex justify-between items-center">
                 <span className="text-xs text-white font-bold uppercase tracking-wide flex items-center gap-2">
                    <Globe className="w-3 h-3 text-cta" /> Bản dịch
                 </span>
                 <div className="flex items-center gap-2">
                   <span className="text-[10px] bg-cta/20 text-cta px-2 py-0.5 rounded-full font-medium">Hỗ trợ chỉnh sửa</span>
                   <button onClick={() => downloadTextFile(translatedText, "ban_dich.txt")} className="text-xs text-white bg-pink-500/20 hover:bg-pink-500/40 px-2 py-1 rounded flex items-center gap-1 transition-colors">
                      <Download className="w-3 h-3"/> Tải .txt
                   </button>
                 </div>
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
              <RenameControl url={ttsData.audio_url} defaultName="longtieng_final" onRename={(url, fname) => setTtsData({...ttsData, audio_url: url, audio_filename: fname})} />
            </div>
            <a href={`${API}${ttsData.audio_url}`} download
              className="flex-shrink-0 px-6 py-3 rounded-xl bg-gradient-to-r from-cta to-pink-600 hover:from-pink-600 hover:to-cta text-white font-bold text-sm flex items-center gap-2 whitespace-nowrap transition-all hover:scale-105 shadow-[0_0_15px_#E11D484D]">
              <Download className="w-4 h-4" /> Tải về máy
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

// ─── Main App ────────────────────────────────────────────────────────────────
const TABS: { id: Tab; icon: any; label: string; badge?: string }[] = [
  { id: 'manual', icon: Settings, label: 'Chủ Động', badge: 'MỚI' },
  { id: 'download', icon: Download, label: 'Tải Video' },
  { id: 'translate', icon: BrainCircuit, label: 'Dịch Văn Bản' },
  { id: 'voiceover', icon: Mic, label: 'Lồng Tiếng' },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('manual');

  return (
    <div className="min-h-screen bg-background relative overflow-x-hidden flex flex-col items-center justify-start pt-6 px-4 pb-24">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cta/15 rounded-full blur-[140px] pointer-events-none"></div>
      <div className="absolute bottom-[-5%] right-[-10%] w-[35%] h-[35%] bg-secondary/20 rounded-full blur-[140px] pointer-events-none"></div>

      <header className="w-full max-w-4xl mb-8 flex justify-between items-center glass-card px-7 py-4 z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cta to-purple-600 flex items-center justify-center shadow-lg shadow-cta/20">
            <Video className="text-white w-4 h-4" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">Video<span className="text-cta">Lingo</span></span>
        </div>
        <span className="text-xs text-gray-500 hidden sm:block">AI Video Processing · v2.0</span>
      </header>

      <div className="w-full max-w-4xl mb-6 z-10 text-center">
        <h1 className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-400 mb-2">
          Extract, Translate & Speak
        </h1>
        <p className="text-gray-500 text-sm">Công cụ AI xử lý video toàn diện — phiên dịch, dịch thuật & lồng tiếng</p>
      </div>

      <nav className="w-full max-w-4xl mb-6 z-10">
        <div className="glass-card p-1.5 flex gap-1.5 rounded-2xl">
          {TABS.map(({ id, icon: Icon, label, badge }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`relative flex-1 flex flex-col sm:flex-row items-center justify-center gap-1.5 py-3 px-2 rounded-xl transition-all duration-300 text-xs sm:text-sm font-medium cursor-pointer ${tab === id
                ? 'bg-gradient-to-r from-cta/90 to-pink-600/90 text-white shadow-[0_0_20px_#E11D484D] scale-[1.02]'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
              <span className="sm:hidden text-center leading-tight">{label.split(' ').map((w, i) => <span key={i} className="block">{w}</span>)}</span>
              {badge && (
                <span className="absolute -top-1.5 -right-1.5 bg-yellow-400 text-black text-[9px] font-black px-1.5 py-0.5 rounded-full leading-none">
                  {badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </nav>

      <main className="w-full max-w-4xl z-10">
        <div className="glass-card p-7">
          {tab === 'manual' && <TabManual />}
          {tab === 'download' && <p className="text-gray-400 text-center text-sm py-10">Tab "Tải Video" đang thiết kế.</p>}
          {tab === 'translate' && <p className="text-gray-400 text-center text-sm py-10">Tab "Dịch Văn Bản" đang thiết kế.</p>}
          {tab === 'voiceover' && <p className="text-gray-400 text-center text-sm py-10">Tab "Lồng Tiếng" đang thiết kế.</p>}
        </div>
      </main>
    </div>
  );
}
"""

with open("frontend/src/App.tsx", "w") as f:
    f.write(content_v1)
