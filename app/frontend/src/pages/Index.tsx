import { useEffect, useMemo, useState } from 'react';
import { createClient } from '@metagptx/web-sdk';
import { toast } from 'sonner';
import { Code2, Eye, Loader2, LogIn, Sparkles, User } from 'lucide-react';

const client = createClient();
const MODEL = 'claude-opus-4.6';

interface PageVersion {
  id: number;
  version_no: number;
  prompt: string;
  html: string;
  created_at?: string;
}

type AuthState = 'loading' | 'authenticated' | 'anonymous';

const SYSTEM_PROMPT =
  '你是资深前端工程师。根据用户需求输出一个完整、独立可运行的 HTML5 页面：包含 <!DOCTYPE html>、内联 <style> 与 <script>，响应式、现代、代码整洁。只输出 HTML 代码本身，不要任何解释，不要 markdown 代码块。';

const extractHtml = (raw: string) => {
  let text = raw.trim();
  const fence = text.match(/```(?:html)?\s*([\s\S]*?)(```|$)/i);
  if (fence) text = fence[1].trim();
  const start = text.search(/<!DOCTYPE|<html/i);
  return start > 0 ? text.slice(start) : text;
};

const errMsg = (e: any) => e?.data?.detail || e?.response?.data?.detail || e?.message || '请求失败';

export default function Index() {
  const [auth, setAuth] = useState<AuthState>('loading');
  const [prompt, setPrompt] = useState('');
  const [inputError, setInputError] = useState('');
  const [versions, setVersions] = useState<PageVersion[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [streamHtml, setStreamHtml] = useState('');
  const [generating, setGenerating] = useState(false);
  const [tab, setTab] = useState<'preview' | 'code'>('preview');

  useEffect(() => {
    client.auth
      .me()
      .then((res) => {
        if (res?.data) {
          setAuth('authenticated');
          loadVersions();
        } else setAuth('anonymous');
      })
      .catch(() => setAuth('anonymous'));
  }, []);

  const loadVersions = async (selectLatest = true) => {
    try {
      const res = await client.entities.page_versions.query({ sort: '-version_no', limit: 100 });
      const items: PageVersion[] = res.data?.items ?? [];
      setVersions(items);
      if (selectLatest && items.length) setSelectedId(items[0].id);
    } catch (e) {
      toast.error('加载历史版本失败：' + errMsg(e));
    }
  };

  const current = useMemo(() => versions.find((v) => v.id === selectedId), [versions, selectedId]);
  const displayHtml = generating ? streamHtml : current?.html ?? '';

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setInputError('请输入网页需求');
      return;
    }
    if (auth !== 'authenticated') {
      client.auth.toLogin();
      return;
    }
    setInputError('');
    setGenerating(true);
    setStreamHtml('');
    setTab('preview');
    let acc = '';
    try {
      await client.ai.gentxt({
        model: MODEL,
        stream: true,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: prompt.trim() },
        ],
        onChunk: (chunk: any) => {
          acc += chunk?.content ?? '';
          setStreamHtml(extractHtml(acc));
        },
        onComplete: () => {},
        onError: (e: any) => {
          throw e;
        },
      });
      const html = extractHtml(acc);
      if (!html) throw new Error('生成结果为空，请重试');
      const nextNo = (versions[0]?.version_no ?? 0) + 1;
      const res = await client.entities.page_versions.create({
        data: { version_no: nextNo, prompt: prompt.trim(), html },
      });
      const saved: PageVersion = res.data;
      setVersions((prev) => [saved, ...prev]);
      setSelectedId(saved.id);
      setPrompt('');
      toast.success(`已保存为 V${nextNo}`);
    } catch (e) {
      toast.error('生成失败：' + errMsg(e));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAF9] text-[#0C0A09]" style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}>
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono&display=swap" />
      <header className="h-14 border-b border-[#E7E5E4] bg-white flex items-center justify-between px-5">
        <div className="flex items-center gap-2 font-semibold">
          <span className="w-7 h-7 rounded-lg bg-[#0C0A09] text-white grid place-items-center"><Sparkles size={15} /></span>
          AI 网页生成助手
        </div>
        {auth === 'authenticated' ? (
          <span aria-label="已登录" className="w-8 h-8 rounded-full border border-[#E7E5E4] grid place-items-center"><User size={16} /></span>
        ) : auth === 'anonymous' ? (
          <button onClick={() => client.auth.toLogin()} className="flex items-center gap-1.5 text-sm px-3 h-8 rounded-[10px] bg-[#0C0A09] text-white hover:bg-[#292524]">
            <LogIn size={14} /> 登录
          </button>
        ) : null}
      </header>

      <main className="flex flex-col lg:flex-row gap-4 p-4 lg:h-[calc(100vh-56px)]">
        <aside className="lg:w-[380px] flex flex-col gap-4 shrink-0 min-h-0">
          <section className="bg-white border border-[#E7E5E4] rounded-[14px] p-4">
            <h2 className="text-[15px] font-semibold mb-1">描述你想要的网页</h2>
            <p className="text-xs text-[#78716C] mb-3">例如：一个咖啡店落地页，包含菜单、营业时间和联系方式</p>
            <textarea
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                if (inputError) setInputError('');
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate();
              }}
              rows={5}
              disabled={generating}
              placeholder="输入网页需求…"
              className={`w-full resize-none text-sm rounded-[10px] border p-3 outline-none focus:ring-2 focus:ring-[#0C0A09] ${inputError ? 'border-[#DC2626]' : 'border-[#E7E5E4]'}`}
            />
            {inputError && <p role="alert" className="text-xs text-[#DC2626] mt-1.5">{inputError}</p>}
            <button
              onClick={handleGenerate}
              disabled={generating || auth === 'loading'}
              className="mt-3 w-full h-10 rounded-[10px] bg-[#0C0A09] text-white text-sm font-medium flex items-center justify-center gap-2 hover:bg-[#292524] disabled:opacity-60"
            >
              {generating ? <><Loader2 size={15} className="animate-spin" /> 生成中…</> : auth === 'anonymous' ? '登录后生成' : '生成网页'}
            </button>
          </section>

          <section className="bg-white border border-[#E7E5E4] rounded-[14px] p-4 flex-1 min-h-[200px] flex flex-col min-h-0">
            <h2 className="text-[15px] font-semibold mb-3">历史版本 <span className="text-[#78716C] font-normal text-xs">({versions.length})</span></h2>
            <div className="flex-1 overflow-auto space-y-2">
              {versions.length === 0 && (
                <p className="text-xs text-[#78716C] py-6 text-center">{auth === 'anonymous' ? '登录后可保存并查看历史版本' : '暂无版本，提交需求后自动保存'}</p>
              )}
              {versions.map((v) => {
                const active = v.id === selectedId && !generating;
                return (
                  <button
                    key={v.id}
                    onClick={() => setSelectedId(v.id)}
                    disabled={generating}
                    className={`w-full text-left p-3 rounded-[10px] border transition-colors duration-150 ${active ? 'bg-[#0C0A09] text-white border-[#0C0A09]' : 'bg-white border-[#E7E5E4] hover:bg-[#F5F5F4]'}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${active ? 'bg-[#F97316] text-white' : 'bg-[#F5F5F4] text-[#0C0A09]'}`}>V{v.version_no}</span>
                      {v.created_at && <span className={`text-[11px] ${active ? 'text-[#D6D3D1]' : 'text-[#78716C]'}`}>{new Date(v.created_at).toLocaleString('zh-CN')}</span>}
                    </div>
                    <p className="text-[13px] line-clamp-2">{v.prompt}</p>
                  </button>
                );
              })}
            </div>
          </section>
        </aside>

        <section className="flex-1 bg-white border border-[#E7E5E4] rounded-[14px] flex flex-col min-h-[70vh] lg:min-h-0 overflow-hidden">
          <div className="h-12 border-b border-[#E7E5E4] flex items-center justify-between px-3">
            <div className="flex gap-1 bg-[#F5F5F4] p-1 rounded-[10px]">
              {([['preview', '预览', Eye], ['code', '代码', Code2]] as const).map(([key, label, Icon]) => (
                <button key={key} onClick={() => setTab(key)} className={`flex items-center gap-1.5 text-sm px-3 h-7 rounded-lg ${tab === key ? 'bg-white shadow-sm text-[#0C0A09]' : 'text-[#78716C]'}`}>
                  <Icon size={14} /> {label}
                </button>
              ))}
            </div>
            <span className="text-xs text-[#78716C]">{generating ? '实时生成中…' : current ? `当前查看 V${current.version_no}` : ''}</span>
          </div>
          <div className="flex-1 min-h-0">
            {!displayHtml ? (
              <div className="h-full grid place-items-center text-sm text-[#78716C] p-8 text-center">输入需求并提交，生成的网页将在这里实时预览</div>
            ) : tab === 'preview' ? (
              <iframe title="网页预览" srcDoc={displayHtml} sandbox="allow-scripts allow-forms allow-modals" className="w-full h-full border-0 bg-white" />
            ) : (
              <pre className="h-full overflow-auto p-4 text-[12.5px] leading-relaxed bg-[#0C0A09] text-[#E7E5E4]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{displayHtml}</pre>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
