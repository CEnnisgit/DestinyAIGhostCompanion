import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

const ChatWindow = ({ messages, isLoading, onRegenerate }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <section className="chat-window" aria-label="Conversation">
      {messages.length === 0 && (
        <div className="chat-window__empty">
          <p>Your Ghost is listening. Ask about the latest strike or request mission intel.</p>
        </div>
      )}
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} onRegenerate={onRegenerate} />
      ))}
      <div ref={bottomRef} />
    </section>
  );
};

export default ChatWindow;
