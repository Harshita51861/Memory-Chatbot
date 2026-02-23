// frontend/src/App.js

import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import AdminDashboard from './components/AdminDashboard';
import './App.css';

function App() {
  const [view, setView] = useState('chat'); // 'chat' or 'admin'
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🧠 Memory Chatbot</h1>
        <p className="subtitle">Long-term memory AI that remembers across conversations</p>
        
        <div className="nav-buttons">
          <button 
            className={view === 'chat' ? 'active' : ''}
            onClick={() => setView('chat')}
          >
            💬 Chat
          </button>
          <button 
            className={view === 'admin' ? 'active' : ''}
            onClick={() => setView('admin')}
          >
            🔐 Admin Dashboard
          </button>
        </div>
      </header>

      <main className="App-main">
        {view === 'chat' ? (
          <ChatInterface />
        ) : (
          <AdminDashboard 
            isLoggedIn={isAdminLoggedIn}
            setIsLoggedIn={setIsAdminLoggedIn}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>Built with governed long-term memory • No GPU required • CPU-only processing</p>
      </footer>
    </div>
  );
}

export default App;
