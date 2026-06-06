import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';

const API_BASE = import.meta.env.PUBLIC_RAG_API_URL ?? 'https://atharvadevasthali.com';

type Source = { title: string; source: string };

type Message = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  sources?: Source[];
};

function generateId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export const ChatWidget = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const sessionId = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      inputRef.current?.focus();
    }
  }, [open, messages]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: generateId(), role: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const body: Record<string, string> = {
        message: text,
        link: window.location.href,
      };
      if (sessionId.current) body.session_id = sessionId.current;

      const res = await fetch(`${API_BASE}/api/blog/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      sessionId.current = data.session_id;

      setMessages(prev => [
        ...prev,
        {
          id: generateId(),
          role: 'assistant',
          text: data.answer,
          sources: data.sources?.length ? data.sources : undefined,
        },
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        { id: generateId(), role: 'assistant', text: 'Something went wrong. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-[100000] flex flex-col items-end gap-3">
      {/* Chat panel */}
      {open && (
        <div
          className="flex flex-col rounded-2xl overflow-hidden shadow-2xl border border-white/10"
          style={{
            width: 'min(380px, calc(100vw - 48px))',
            height: 'min(520px, calc(100vh - 120px))',
            background: '#0F0F10',
          }}
        >
          {/* Header */}
          <div
            className="flex items-center gap-3 px-4 py-3 border-b border-white/10 shrink-0"
            style={{ background: '#18181a' }}
          >
            <div className="w-2 h-2 rounded-full bg-[#fdb55e] shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white font-rubik truncate">Ask Atharva</p>
              <p className="text-xs text-white/40 font-rubik">AI agent — RAG-powered</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-white/40 hover:text-white/80 transition-colors p-1 -mr-1 rounded"
              aria-label="Close chat"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3 min-h-0">
            {messages.length === 0 && (
              <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center">
                <span className="text-2xl">👋</span>
                <p className="text-white/60 text-sm font-rubik">
                  Hey! Ask me anything about Atharva's work, projects, or writing.
                </p>
              </div>
            )}
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`rounded-xl px-3 py-2 text-sm font-rubik max-w-[82%] leading-relaxed break-words ${
                    msg.role === 'user'
                      ? 'text-[#0F0F10] font-medium'
                      : 'text-white/85 border border-white/10'
                  }`}
                  style={
                    msg.role === 'user'
                      ? { background: '#fdb55e' }
                      : { background: '#1c1c1e' }
                  }
                >
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown
                      components={{
                        a: ({ href, children }) => (
                          <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[#fdb55e] underline underline-offset-2"
                          >
                            {children}
                          </a>
                        ),
                        code: ({ children, className }) => {
                          const isBlock = className?.includes('language-');
                          return isBlock ? (
                            <code className="block bg-black/40 rounded px-3 py-2 mt-1 mb-1 text-xs overflow-x-auto whitespace-pre font-mono text-white/80">
                              {children}
                            </code>
                          ) : (
                            <code className="bg-black/40 rounded px-1 text-xs font-mono text-white/80">
                              {children}
                            </code>
                          );
                        },
                        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc list-inside mb-1 space-y-0.5">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside mb-1 space-y-0.5">{children}</ol>,
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>

                {/* Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-1.5 max-w-[82%] flex flex-wrap gap-1.5">
                    {msg.sources.map(s => (
                      <a
                        key={s.source}
                        href={s.source}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] font-rubik text-white/40 hover:text-[#fdb55e] border border-white/10 rounded-full px-2 py-0.5 transition-colors truncate max-w-[180px]"
                        title={s.title}
                      >
                        {s.title}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div
                  className="rounded-xl px-4 py-3 border border-white/10 flex gap-1 items-center"
                  style={{ background: '#1c1c1e' }}
                >
                  {[0, 1, 2].map(i => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div
            className="shrink-0 border-t border-white/10 px-3 py-3 flex gap-2 items-end"
            style={{ background: '#18181a' }}
          >
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask something…"
              className="flex-1 resize-none bg-transparent text-white/90 text-sm font-rubik placeholder:text-white/30 outline-none leading-relaxed max-h-28 py-1"
              style={{ scrollbarWidth: 'none' }}
            />
            <button
              onClick={send}
              disabled={!input.trim() || loading}
              className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all disabled:opacity-30"
              style={{ background: '#fdb55e' }}
              aria-label="Send message"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1 13L13 7 1 1v4.5l8 1.5-8 1.5V13z" fill="#0F0F10" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Toggle button */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-transform hover:scale-105 active:scale-95"
        style={{ background: '#fdb55e' }}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5l10 10" stroke="#0F0F10" strokeWidth="2" strokeLinecap="round" />
          </svg>
        ) : (
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path
              d="M11 2C6.03 2 2 5.69 2 10.2c0 2.44 1.13 4.63 2.93 6.13L4 20l4.1-1.9A10.2 10.2 0 0011 18.4C15.97 18.4 20 14.71 20 10.2S15.97 2 11 2z"
              fill="#0F0F10"
            />
          </svg>
        )}
      </button>
    </div>
  );
};
