import { useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  const handleSend = () => {
    if (!message.trim()) return;

    setMessages([
      ...messages,
      {
        type: "user",
        text: message,
      },
      {
        type: "ai",
        text: "I'm checking that for you. AI support will be connected here.",
      },
    ]);

    setMessage("");
  };

  return (
    <div className="app">
      <header className="navbar">
        <div className="logo">
          <span>AI</span> Helpdesk
        </div>

        <nav>
          <button>Help Center</button>
          <button>My Tickets</button>
        </nav>
      </header>

      <main className="main">
        <section className="hero">
          <p className="tag">INTELLIGENT SUPPORT</p>

          <h1>
            How can we
            <br />
            help you?
          </h1>

          <p className="subtitle">
            Ask a question and our AI assistant will help you find
            the right solution.
          </p>
        </section>

        <section className="chat-container">
          <div className="chat-header">
            <div>
              <h2>AI Support Assistant</h2>
              <p>
                <span className="status-dot"></span>
                Online
              </p>
            </div>
          </div>

          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome">
                <div className="bot-icon">✦</div>

                <h3>Hi! How can I help?</h3>

                <p>
                  Describe your issue and I'll help you find a solution.
                </p>

                <div className="suggestions">
                  <button onClick={() => setMessage("I forgot my password")}>
                    🔐 Password issue
                  </button>

                  <button onClick={() => setMessage("My Wi-Fi is not working")}>
                    📶 Network issue
                  </button>

                  <button onClick={() => setMessage("I need software support")}>
                    💻 Software issue
                  </button>
                </div>
              </div>
            )}

            {messages.map((msg, index) => (
              <div
                key={index}
                className={`message ${
                  msg.type === "user" ? "user-message" : "ai-message"
                }`}
              >
                <div className="message-label">
                  {msg.type === "user" ? "You" : "AI Assistant"}
                </div>

                <div className="message-text">{msg.text}</div>
              </div>
            ))}
          </div>

          <div className="input-area">
            <input
              type="text"
              placeholder="Describe your problem..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />

            <button onClick={handleSend}>Send ↑</button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;