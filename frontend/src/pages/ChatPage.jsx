import { useState, useRef, useEffect, useCallback } from 'react'
import Sidebar from '../components/Sidebar'
import UserAvatar from '../components/UserAvatar'
import ReactMarkdown from 'react-markdown'
import api from '../api'

function TypewriterMarkdown({ content, streaming }) {
  const [displayedContent, setDisplayedContent] = useState('');

  useEffect(() => {
    if (!streaming) {
      setDisplayedContent(content);
      return;
    }

    if (displayedContent.length >= content.length) return;

    // Calculate how many characters to add to catch up smoothly
    const diff = content.length - displayedContent.length;
    // Semakin besar pembagi, semakin sedikit karakter yang ditambahkan (lebih lambat).
    // Dibuat cepat agar tampilan mengikuti stream AI (±1 detik) tanpa tertinggal lalu melompat.
    const charsToAdd = Math.max(3, Math.ceil(diff / 6));

    const timeout = setTimeout(() => {
      setDisplayedContent(prev => content.slice(0, prev.length + charsToAdd));
    }, 30);

    return () => clearTimeout(timeout);
  }, [content, streaming, displayedContent]);

  useEffect(() => {
    if (!streaming && displayedContent !== content) {
      setDisplayedContent(content);
    }
  }, [streaming, content, displayedContent]);

  return (
    <div className={`prose-chat ${streaming ? 'streaming' : ''}`}>
      <ReactMarkdown>{displayedContent}</ReactMarkdown>
    </div>
  );
}

export default function ChatPage({ user }) {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const username = user?.username

  useEffect(() => {
    if (username) loadSessions()
  }, [username])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea — tidak ada ruang kosong berlebih
  const autoResize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const scrollH = el.scrollHeight
    const maxH = 120
    if (scrollH <= maxH) {
      el.style.height = scrollH + 'px'
      el.style.overflowY = 'hidden'
    } else {
      el.style.height = maxH + 'px'
      el.style.overflowY = 'auto'
    }
  }, [])

  useEffect(() => {
    autoResize()
  }, [input, autoResize])

  async function loadSessions() {
    try {
      const res = await api.get(`/users/${username}/sessions`)
      setSessions(res.data.data || [])
    } catch {}
  }

  async function loadSessionMessages(sessionId) {
    setActiveSessionId(sessionId)
    setMobileHistoryOpen(false)
    try {
      const res = await api.get(`/users/${username}/sessions/${sessionId}/messages`)
      const data = res.data.data
      const msgs = (data.messages || []).map(m => ({ role: m.role, content: m.content, intent: m.intent }))
      setMessages(msgs)
    } catch {}
  }

  async function sendMessage() {
    if (!input.trim() || streaming) return
    const text = input.trim()
    setInput('')

    const userMsg = { role: 'user', content: text }
    const aiMsg = { role: 'assistant', content: '' }
    setMessages(prev => [...prev, userMsg, aiMsg])
    setStreaming(true)

    // Build history (exclude the last 2 just added)
    const history = messages.map(m => ({ role: m.role, content: m.content }))

    try {
      const body = {
        username,
        message: text,
        session_id: activeSessionId,
        history,
        user_profile: JSON.parse(localStorage.getItem('fitmind_profile') || 'null'),
      }

      const API_URL = import.meta.env.VITE_API_URL || '/api'
      const response = await fetch(`${API_URL}/chat/session/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('fitmind_token') || ''}`,
        },
        body: JSON.stringify(body),
      })

      if (response.status === 401) {
        localStorage.removeItem('fitmind_token')
        localStorage.removeItem('fitmind_user')
        localStorage.removeItem('fitmind_profile')
        window.location.assign('/login')
        return
      }
      if (!response.ok || !response.body) throw new Error('Chat tidak tersedia')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') continue
          try {
            const json = JSON.parse(raw)
            if (json.chunk) {
              setMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: updated[updated.length - 1].content + json.chunk,
                }
                return updated
              })
            }
            if (json.session_id) {
              setActiveSessionId(json.session_id)
            }
          } catch {}
        }
      }
      await loadSessions()
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...updated[updated.length - 1], content: 'Terjadi error saat menghubungi AI.' }
        return updated
      })
    } finally {
      setStreaming(false)
    }
  }

  function newChat() {
    setActiveSessionId(null)
    setMessages([])
    setMobileHistoryOpen(false)
  }

  async function deleteSession(sessionId, e) {
    e.stopPropagation()
    try {
      await api.delete(`/users/${username}/sessions/${sessionId}`)
      setSessions(prev => prev.filter(s => s.id !== sessionId))
      if (activeSessionId === sessionId) newChat()
    } catch {}
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar username={user?.username} avatarData={user?.avatar_data} />

      {/* Mobile Backdrop */}
      {mobileHistoryOpen && (
        <div
          onClick={() => setMobileHistoryOpen(false)}
          style={{ position: 'fixed', inset: 0, top: 72, background: 'rgba(0,0,0,0.6)', zIndex: 99 }}
        />
      )}

      {/* ── Sessions Sidebar ── */}
      <aside className={`chat-sessions-sidebar ${mobileHistoryOpen ? 'open' : ''}`}>
        <div style={{ paddingLeft: 2, marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: '#525252', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>
            Riwayat Chat
          </div>
          <button className="btn-primary" style={{ width: '100%', padding: '8px 12px' }} onClick={newChat}>
            + Chat Baru
          </button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {sessions.map(s => (
            <div key={s.id}
              onClick={() => loadSessionMessages(s.id)}
              style={{
                padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                background: activeSessionId === s.id ? 'rgba(34,197,94,0.08)' : 'transparent',
                border: `1px solid ${activeSessionId === s.id ? 'rgba(34,197,94,0.2)' : 'transparent'}`,
                transition: 'all 0.15s',
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13, color: activeSessionId === s.id ? '#22c55e' : '#f5f5f5',
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: 2,
                }}>
                  {s.title || 'Sesi tanpa judul'}
                </div>
                <div style={{ fontSize: 11, color: '#525252' }}>{s.message_count} pesan</div>
              </div>
              <button
                onClick={(e) => deleteSession(s.id, e)}
                style={{ background: 'none', border: 'none', color: '#525252', cursor: 'pointer', fontSize: 14, padding: '0 0 0 6px', lineHeight: 1 }}
              >
                ×
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div style={{ fontSize: 13, color: '#525252', textAlign: 'center', marginTop: 20 }}>
              Belum ada riwayat chat.
            </div>
          )}
        </div>
      </aside>

      {/* ── Chat area ── */}
      <main className="chat-main" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {/* Mobile History Toggle Header */}
        <div className="mobile-history-toggle" style={{
          padding: '12px 16px',
          borderBottom: '1px solid #2a2a2a',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#0a0a0a',
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#a3a3a3' }}>
            {activeSessionId ? 'Percakapan Aktif' : 'Percakapan Baru'}
          </span>
          <button onClick={() => setMobileHistoryOpen(true)} style={{
            background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.25)',
            padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer'
          }}>
            Riwayat
          </button>
        </div>

        {/* Messages */}
        <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '32px 40px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: '25vh' }}>
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 10 }}>
                FitMind<span style={{ color: '#22c55e' }}>AI</span>
              </div>
              <p style={{ fontSize: 15, color: '#a3a3a3', maxWidth: 360, margin: '0 auto' }}>
                Tanyakan tentang latihan, nutrisi, program gym, atau analisis tubuh Anda.
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginTop: 24 }}>
                {[
                  'Latihan untuk otot dada',
                  'Program latihan 4 hari seminggu',
                  'Rekomendasikan program untuk pemula',
                  'Makanan tinggi protein bebas gluten',
                ].map(suggestion => (
                  <button key={suggestion}
                    onClick={() => { setInput(suggestion) }}
                    className="btn-ghost" style={{ fontSize: 13 }}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className="chat-message-row" style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              {msg.role === 'assistant' && (
                <div style={{
                  width: 28, height: 28, marginRight: 10, flexShrink: 0, marginTop: 2,
                }}>
                  <img src="/pp-ai.png" alt="FitMindAI" style={{ width: '100%', height: '100%', objectFit: 'contain', filter: 'hue-rotate(-75deg) saturate(.85)' }} />
                </div>
              )}
              <div className={`chat-bubble ${msg.role === 'user' ? 'from-user' : 'from-ai'}`} style={{
                maxWidth: '68%',
                background: msg.role === 'user' ? '#173b31' : '#1c2026',
                border: `1px solid ${msg.role === 'user' ? '#275c47' : '#303842'}`,
                borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                padding: '12px 16px',
                fontSize: 14,
                lineHeight: 1.65,
              }}>
                {msg.role === 'assistant' ? (
                  msg.content ? (
                    i === messages.length - 1 ? (
                      <TypewriterMarkdown content={msg.content} streaming={streaming} />
                    ) : (
                      <div className="prose-chat">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )
                  ) : (
                    streaming && i === messages.length - 1 && (
                      <div className="prose-chat streaming">
                        <div className="typing-indicator">
                          <span></span><span></span><span></span>
                        </div>
                      </div>
                    )
                  )
                ) : (
                  <span style={{ color: '#f5f5f5' }}>{msg.content}</span>
                )}
              </div>
              {msg.role === 'user' && (
                <span className="chat-user-avatar">
                  <UserAvatar username={user?.username} avatarData={user?.avatar_data} size={28} />
                </span>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-composer" style={{
          padding: '16px 40px 28px',
          borderTop: '1px solid #2a2a2a',
          background: '#0a0a0a',
        }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', maxWidth: 760, margin: '0 auto' }}>
            <textarea
              ref={textareaRef}
              className="input-field"
              rows={1}
              placeholder="Tanyakan sesuatu kepada FitMind AI..."
              value={input}
              onChange={e => {
                setInput(e.target.value)
              }}
              onKeyDown={handleKeyDown}
              disabled={streaming}
              style={{
                resize: 'none',
                height: '44px',
                minHeight: '44px',
                maxHeight: '120px',
                overflowY: 'hidden',
                lineHeight: '1.5',
                opacity: streaming ? 0.6 : 1,
                cursor: streaming ? 'not-allowed' : 'text',
                padding: '11px 14px',
              }}
            />
            <button className="btn-primary" onClick={sendMessage} disabled={streaming || !input.trim()}
              style={{ padding: '11px 20px', flexShrink: 0, height: '44px' }}>
              Kirim
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
