import re

with open("frontend/src/App.tsx", "r") as f:
    content = f.read()

# Remove unused types
content = content.replace("type Tab = 'manual' | 'download' | 'translate' | 'voiceover';", "")
content = content.replace("const TABS: { id: Tab; icon: any; label: string; badge?: string }[] = [\n  { id: 'manual', icon: Settings, label: 'Chủ Động', badge: 'MỚI' },\n  { id: 'download', icon: Download, label: 'Tải Video' },\n  { id: 'translate', icon: BrainCircuit, label: 'Dịch Văn Bản' },\n  { id: 'voiceover', icon: Mic, label: 'Lồng Tiếng' },\n];", "")
content = content.replace("const [tab, setTab] = useState<Tab>('manual');", "")

with open("frontend/src/App.tsx", "w") as f:
    f.write(content)
