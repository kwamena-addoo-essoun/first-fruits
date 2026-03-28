import React, { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../utils/api';
import './ChatBot.css';

const WELCOME_MESSAGE = {
  role: 'assistant',
  content: "Hi! I'm your HourStack assistant. I can see your live earnings, projects, and invoices. Ask me anything — for example:\n• \"How much have I earned this month?\"\n• \"Do I have any uninvoiced hours?\"\n• \"How do I create an invoice?\"",
};

export default function ChatBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, open]);

  // Focus textarea when chat opens
  useEffect(() => {
    if (open) {
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [open]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text };
    const updatedMessages = [...messages, userMsg];

    setMessages(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      // Only send actual conversation messages (skip the welcome message)
      const conversationHistory = updatedMessages.filter(
        (m) => !(m === WELCOME_MESSAGE)
      );
      const res = await chatAPI.sendMessage(conversationHistory);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.data.reply },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          content: detail || 'Something went wrong. Please try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {open && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <div className="chatbot-header-info">
              <div className="chatbot-avatar">🤖</div>
              <div>
                <h4>HourStack Assistant</h4>
                <p>Knows your live data</p>
              </div>
            </div>
            <button className="chatbot-close" onClick={() => setOpen(false)} title="Close">
              ✕
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="chat-typing">
                <span /><span /><span />
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chatbot-input-row">
            <textarea
              ref={textareaRef}
              rows={1}
              placeholder="Ask anything…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className="chatbot-send"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              title="Send"
            >
              ➤
            </button>
          </div>
          <div className="chatbot-footer-hint">Powered by GPT-4o mini · Enter to send</div>
        </div>
      )}

      <button
        className="chatbot-toggle"
        onClick={() => setOpen((o) => !o)}
        title={open ? 'Close assistant' : 'Open assistant'}
      >
        {open ? '✕' : '💬'}
      </button>
    </>
  );
}
