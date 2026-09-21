import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [activePage, setActivePage] = useState("overview");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text = message) => {
    if (!text.trim() || loading) return;

    const userMessage = text.trim();

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: userMessage,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/chat/",
        null,
        {
          params: {
            message: userMessage,
          },
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: response.data.response,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: "I couldn't reach the support service. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickQuestions = [
    {
      icon: "⌁",
      title: "Account & Access",
      text: "I can't access my account",
    },
    {
      icon: "◌",
      title: "Network",
      text: "My Wi-Fi isn't working",
    },
    {
      icon: "□",
      title: "Software",
      text: "I need help with software",
    },
  ];

  return (
    <div className="app-shell">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-mark">H</div>
          <div>
            <strong>helpdesk</strong>
            <span>support workspace</span>
          </div>
        </div>

        <div className="nav-section">
          <p className="nav-label">WORKSPACE</p>

          <button
            className={`nav-item ${
              activePage === "overview" ? "active" : ""
            }`}
            onClick={() => setActivePage("overview")}
          >
            <span>⌂</span>
            Overview
          </button>

          <button
            className={`nav-item ${
              activePage === "assistant" ? "active" : ""
            }`}
            onClick={() => setActivePage("assistant")}
          >
            <span>✦</span>
            AI Assistant
          </button>

          <button
            className={`nav-item ${
              activePage === "tickets" ? "active" : ""
            }`}
            onClick={() => setActivePage("tickets")}
          >
            <span>□</span>
            My Tickets
            <b>3</b>
          </button>
        </div>

        <div className="nav-section">
          <p className="nav-label">RESOURCES</p>

          <button className="nav-item">
            <span>⌕</span>
            Knowledge Base
          </button>

          <button className="nav-item">
            <span>?</span>
            Help Center
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="mini-status">
            <span></span>
            All systems operational
          </div>

          <div className="profile">
            <div className="avatar">T</div>
            <div>
              <strong>Tanvi</strong>
              <small>Student</small>
            </div>
            <span className="dots">•••</span>
          </div>
        </div>

      </aside>

      {/* MAIN */}
      <main className="main-content">

        {/* TOP BAR */}
        <header className="topbar">
          <div className="breadcrumbs">
            Workspace <span>/</span> {activePage}
          </div>

          <div className="top-actions">
            <button className="icon-button">⌕</button>
            <button className="icon-button">?</button>
            <div className="top-avatar">T</div>
          </div>
        </header>

        {/* OVERVIEW */}
        {activePage === "overview" && (
          <section className="page">

            <div className="welcome-row">
              <div>
                <p className="eyebrow">MONDAY, SEPTEMBER 21</p>
                <h1>Good evening, Tanvi.</h1>
                <p className="page-subtitle">
                  What can we help you sort out today?
                </p>
              </div>

              <button
                className="new-ticket"
                onClick={() => setActivePage("assistant")}
              >
                <span>+</span>
                Ask for help
              </button>
            </div>

            {/* AI HERO */}
            <div className="support-card">

              <div className="support-copy">
                <div className="ai-badge">
                  <span>✦</span>
                  AI SUPPORT
                </div>

                <h2>
                  Start with a question.
                  <br />
                  We'll take it from there.
                </h2>

                <p>
                  Our support assistant searches the help center
                  and guides you through the next step.
                </p>
              </div>

              <div className="question-box">
                <textarea
                  placeholder="Tell us what's going wrong..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                />

                <div className="question-footer">
                  <span>Press Enter to send</span>

                  <button onClick={() => sendMessage()}>
                    Ask AI
                    <span>→</span>
                  </button>
                </div>
              </div>

            </div>

            {/* QUICK ACTIONS */}
            <div className="section-heading">
              <div>
                <p className="eyebrow">QUICK START</p>
                <h3>What do you need help with?</h3>
              </div>
            </div>

            <div className="quick-grid">

              {quickQuestions.map((item) => (
                <button
                  className="quick-card"
                  key={item.title}
                  onClick={() => {
                    setActivePage("assistant");
                    sendMessage(item.text);
                  }}
                >
                  <div className="quick-icon">{item.icon}</div>

                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.text}</p>
                  </div>

                  <span className="arrow">↗</span>
                </button>
              ))}

            </div>

            {/* RECENT TICKETS */}
            <div className="section-heading tickets-heading">
              <div>
                <p className="eyebrow">YOUR ACTIVITY</p>
                <h3>Recent tickets</h3>
              </div>

              <button
                className="view-all"
                onClick={() => setActivePage("tickets")}
              >
                View all →
              </button>
            </div>

            <div className="ticket-table">

              <div className="ticket-row ticket-head">
                <span>TICKET</span>
                <span>SUBJECT</span>
                <span>STATUS</span>
                <span>UPDATED</span>
              </div>

              <div className="ticket-row">
                <span className="ticket-id">#1042</span>
                <span className="ticket-subject">
                  Wi-Fi connection issue
                </span>
                <span>
                  <i className="status open"></i>
                  Open
                </span>
                <span className="muted">Today</span>
              </div>

              <div className="ticket-row">
                <span className="ticket-id">#1041</span>
                <span className="ticket-subject">
                  Password reset
                </span>
                <span>
                  <i className="status resolved"></i>
                  Resolved
                </span>
                <span className="muted">Yesterday</span>
              </div>

              <div className="ticket-row">
                <span className="ticket-id">#1038</span>
                <span className="ticket-subject">
                  Software installation
                </span>
                <span>
                  <i className="status resolved"></i>
                  Resolved
                </span>
                <span className="muted">Sep 18</span>
              </div>

            </div>

          </section>
        )}

        {/* ASSISTANT */}
        {activePage === "assistant" && (
          <section className="page assistant-page">

            <div className="assistant-top">
              <div>
                <p className="eyebrow">AI SUPPORT</p>
                <h1>Support Assistant</h1>
                <p className="page-subtitle">
                  Describe the problem. We'll help you work through it.
                </p>
              </div>

              <div className="online">
                <span></span>
                Online
              </div>
            </div>

            <div className="conversation">

              {messages.length === 0 ? (
                <div className="empty-chat">
                  <div className="large-ai-icon">✦</div>

                  <h2>What can we help with?</h2>

                  <p>
                    Ask about accounts, networks, software,
                    access, or any other support issue.
                  </p>

                  <div className="suggestion-list">
                    <button
                      onClick={() =>
                        sendMessage("I can't access my account")
                      }
                    >
                      I can't access my account
                      <span>→</span>
                    </button>

                    <button
                      onClick={() =>
                        sendMessage("My Wi-Fi isn't working")
                      }
                    >
                      My Wi-Fi isn't working
                      <span>→</span>
                    </button>

                    <button
                      onClick={() =>
                        sendMessage("I need software support")
                      }
                    >
                      I need software support
                      <span>→</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="messages-list">

                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`conversation-message ${
                        msg.type === "user" ? "from-user" : "from-ai"
                      }`}
                    >
                      <div className="message-meta">
                        {msg.type === "user" ? "YOU" : "AI SUPPORT"}
                      </div>

                      <div className="message-bubble">
                        {msg.text}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="conversation-message from-ai">
                      <div className="message-meta">AI SUPPORT</div>
                      <div className="message-bubble typing">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  )}

                </div>
              )}

              <div className="assistant-input">
                <textarea
                  placeholder="Describe your issue..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                />

                <button onClick={() => sendMessage()}>
                  Send
                  <span>→</span>
                </button>
              </div>

            </div>

          </section>
        )}

        {/* TICKETS */}
        {activePage === "tickets" && (
          <section className="page">

            <div className="welcome-row">
              <div>
                <p className="eyebrow">SUPPORT</p>
                <h1>My tickets</h1>
                <p className="page-subtitle">
                  Track your open and resolved support requests.
                </p>
              </div>

              <button
                className="new-ticket"
                onClick={() => setActivePage("assistant")}
              >
                <span>+</span>
                New request
              </button>
            </div>

            <div className="ticket-summary">
              <div>
                <span>OPEN</span>
                <strong>1</strong>
              </div>

              <div>
                <span>IN PROGRESS</span>
                <strong>0</strong>
              </div>

              <div>
                <span>RESOLVED</span>
                <strong>2</strong>
              </div>
            </div>

            <div className="full-ticket-list">

              <div className="full-ticket">
                <div className="full-ticket-id">#1042</div>

                <div className="full-ticket-main">
                  <h3>Wi-Fi connection issue</h3>
                  <p>
                    Unable to connect to the university network.
                  </p>

                  <div className="ticket-meta">
                    <span>Network</span>
                    <span>Medium priority</span>
                  </div>
                </div>

                <div className="ticket-status">
                  <i className="status open"></i>
                  Open
                </div>
              </div>

              <div className="full-ticket">
                <div className="full-ticket-id">#1041</div>

                <div className="full-ticket-main">
                  <h3>Password reset</h3>
                  <p>
                    Unable to reset account password.
                  </p>

                  <div className="ticket-meta">
                    <span>Account</span>
                    <span>Low priority</span>
                  </div>
                </div>

                <div className="ticket-status">
                  <i className="status resolved"></i>
                  Resolved
                </div>
              </div>

              <div className="full-ticket">
                <div className="full-ticket-id">#1038</div>

                <div className="full-ticket-main">
                  <h3>Software installation</h3>
                  <p>
                    Request for approved software installation.
                  </p>

                  <div className="ticket-meta">
                    <span>Software</span>
                    <span>Low priority</span>
                  </div>
                </div>

                <div className="ticket-status">
                  <i className="status resolved"></i>
                  Resolved
                </div>
              </div>

            </div>

          </section>
        )}

      </main>
    </div>
  );
}

export default App;