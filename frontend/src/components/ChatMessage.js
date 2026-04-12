import React from 'react';
import { formatRelative, parseISO } from 'date-fns';

const roleLabels = {
  user: 'Guardian',
  assistant: 'Ghost',
};

const ChatMessage = ({ message, onRegenerate }) => {
  const timestamp = message.timestamp
    ? formatRelative(parseISO(message.timestamp), new Date())
    : '';
  const isUser = message.role === 'user';
  return (
    <article className={`chat-message ${isUser ? 'chat-message--user' : 'chat-message--assistant'}`}>
      <header className="chat-message__meta">
        <span className="chat-message__role">{roleLabels[message.role] || 'System'}</span>
        {timestamp && <span className="chat-message__timestamp">{timestamp}</span>}
      </header>
      <p className="chat-message__content">{message.content}</p>
      {!isUser && (
        <div className="chat-message__actions">
          <button onClick={() => navigator.clipboard?.writeText?.(message.content || '')}>Copy</button>
          {onRegenerate && <button onClick={() => onRegenerate(message)}>Regenerate</button>}
        </div>
      )}
    </article>
  );
};

export default ChatMessage;
