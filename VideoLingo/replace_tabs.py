import re

with open("frontend/src/App.tsx", "r") as f:
    content = f.read()

# 1. Remove the TABS declaration
content = re.sub(r'const TABS:.*?;\n', '', content, flags=re.DOTALL)

# 2. Update App component to remove state and nav
target_nav = """  const [tab, setTab] = useState<Tab>('manual');

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
}"""

replacement_nav = """  return (
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

      <main className="w-full max-w-4xl z-10">
        <div className="glass-card p-7">
          <TabManual />
        </div>
      </main>
    </div>
  );
}"""

content = content.replace(target_nav, replacement_nav)

# Fix API error string format inside TabManual API call error catching
api_transcribe = """} catch (err: any) { setError(err.message); setPhase('downloaded'); }"""
api_transcribe_replace = """} catch (err: any) { 
      let errorMsg = err.message;
      if (errorMsg.includes("503") || errorMsg.includes("unavailable") || errorMsg.includes("spikes")) {
        errorMsg = "Server AI hiện đang quá tải (hoặc Gemini API bị lỗi 503 HTTP), vui lòng thử bấm Phiên Dịch lại sau vài giây.";
      }
      setError(errorMsg); 
      setPhase('downloaded'); 
    }"""
content = content.replace(api_transcribe, api_transcribe_replace)

with open("frontend/src/App.tsx", "w") as f:
    f.write(content)

