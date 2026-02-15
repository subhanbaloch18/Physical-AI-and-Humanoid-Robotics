import React from 'react';
import Layout from '@theme/Layout';
import ChatBot from '../components/ChatBot/ChatBot';
import '../components/ChatBot/styles.css';

const ChatPage = () => {
  return (
    <Layout title="RAG Chat" description="AI-powered documentation assistant">
      <div className="chat-page-wrapper">
        <div className="chat-page-header">
          <div className="chat-page-badge">
            <span className="chat-page-status-dot" />
            AI Assistant Online
          </div>
          <h1 className="chat-page-title">RAG Agent Assistant</h1>
          <p className="chat-page-subtitle">
            Ask questions about Physical AI & Humanoid Robotics and get
            intelligent, context-aware answers from our documentation.
          </p>
        </div>

        <ChatBot
          initialQueryType="mixed"
          initialQueryMode="standard"
          enableTextSelection={true}
          showSourceCitations={true}
        />
      </div>
    </Layout>
  );
};

export default ChatPage;
