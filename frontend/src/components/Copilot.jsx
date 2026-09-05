import { useState } from 'react';
import { askCopilot } from '../services/api';
import { ArrowUp, Bot, MessageCircle, Sparkles, X } from 'lucide-react';
const replies = {
  'Can I trust this media?': 'I would not treat this media as fully verified yet. Several synthetic-media indicators were detected, while the earliest available source could not be independently confirmed.',
  'Why was this flagged?': 'The strongest signals are high-frequency pixel anomalies, facial texture artifacts, and a missing original metadata trail.',
  'What should I verify next?': 'Find the earliest upload, compare against reputable coverage, and request the original file whenever possible.'
};
export default function Copilot({ analysis }) {
  const [open, setOpen] = useState(false); const [messages, setMessages] = useState([]); const [input, setInput] = useState('');
  const ask = async (q) => { if (!q.trim()) return; setMessages(m => [...m, { who:'you', text:q }]); setInput(''); try { const result = await askCopilot(q, analysis || {}); setMessages(m => [...m, { who:'ai', text: result.answer }]); } catch { setMessages(m => [...m, { who:'ai', text: replies[q] || 'Please corroborate the evidence with an independent source.' }]); } };
  return <aside className={`copilot ${open ? 'expanded' : ''}`} aria-live="polite" aria-label="AI Copilot assistant">
    {open && <div className="copilot-panel"><div className="copilot-head"><span><Bot size={19} aria-hidden="true"/><b>ThelivLens Copilot</b><small>Ask questions about this analysis.</small></span><button onClick={() => setOpen(false)} aria-label="Close Copilot"><X size={18} aria-hidden="true"/></button></div><div className="chat-body" role="log" aria-label="Copilot conversation">{messages.length === 0 && <><p className="ai-message">I'm here to make the evidence easier to understand.</p><div className="suggestions" role="list" aria-label="Suggested questions">{Object.keys(replies).map(q => <button key={q} onClick={() => ask(q)} role="listitem">{q}</button>)}</div></>}{messages.map((m,i) => <p key={i} className={`${m.who}-message`} role="log">{m.text}</p>)}</div><form className="chat-input" onSubmit={e => {e.preventDefault(); ask(input)}}><label htmlFor="copilot-input" className="sr-only">Ask the Copilot a question</label><input id="copilot-input" value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask about this analysis" aria-label="Ask the Copilot"/><button aria-label="Send message"><ArrowUp size={17} aria-hidden="true"/></button></form></div>}
    <button className="copilot-trigger" onClick={() => setOpen(!open)} aria-label={open ? 'Close AI Copilot' : 'Open AI Copilot'} aria-expanded={open}>{open ? <X size={20} aria-hidden="true"/> : <><Sparkles size={18} aria-hidden="true"/><span>Ask Copilot</span></>}</button>
  </aside>;
}
