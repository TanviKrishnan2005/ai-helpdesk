function Assistant({
  messages,
  message,
  setMessage,
  sendMessage,
  loading,
}) {
  return (
    <section className="page assistant-page">

      <div className="assistant-top">

        <div>

          <p className="eyebrow">
            AI SUPPORT
          </p>

          <h1>
            Support Assistant
          </h1>

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

            <div className="large-ai-icon">
              ✦
            </div>

            <h2>
              What can we help with?
            </h2>

            <p>
              Ask about accounts, networks, software,
              access, or any other support issue.
            </p>

            <div className="suggestion-list">

              <button
                onClick={() =>
                  sendMessage(
                    "I can't access my account"
                  )
                }
              >
                I can't access my account
                <span>→</span>
              </button>

              <button
                onClick={() =>
                  sendMessage(
                    "My Wi-Fi isn't working"
                  )
                }
              >
                My Wi-Fi isn't working
                <span>→</span>
              </button>

              <button
                onClick={() =>
                  sendMessage(
                    "I need software support"
                  )
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
                  msg.type === "user"
                    ? "from-user"
                    : "from-ai"
                }`}
              >

                <div className="message-meta">
                  {msg.type === "user"
                    ? "YOU"
                    : "AI SUPPORT"}
                </div>

                <div className="message-bubble">
                  {msg.text}
                </div>

              </div>
            ))}

            {loading && (
              <div className="conversation-message from-ai">

                <div className="message-meta">
                  AI SUPPORT
                </div>

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
            onChange={(e) =>
              setMessage(e.target.value)
            }
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
  );
}

export default Assistant;