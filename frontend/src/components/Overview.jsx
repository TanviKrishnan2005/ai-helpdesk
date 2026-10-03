function Overview({
  message,
  setMessage,
  sendMessage,
  setActivePage,
  tickets,
}) {
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
    <section className="page">

      <div className="welcome-row">

        <div>
          <p className="eyebrow">
            MONDAY, SEPTEMBER 21
          </p>

          <h1>
            Good evening, Tanvi.
          </h1>

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
          <p className="eyebrow">
            QUICK START
          </p>

          <h3>
            What do you need help with?
          </h3>
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

            <div className="quick-icon">
              {item.icon}
            </div>

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
          <p className="eyebrow">
            YOUR ACTIVITY
          </p>

          <h3>
            Recent tickets
          </h3>
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

        {tickets.length === 0 ? (
          <div className="ticket-row">

            <span>-</span>

            <span className="ticket-subject">
              No tickets yet
            </span>

            <span>-</span>

            <span className="muted">
              -
            </span>

          </div>
        ) : (
          tickets.slice(0, 3).map((ticket) => (
            <div
              className="ticket-row"
              key={ticket.id}
            >

              <span className="ticket-id">
                #{ticket.id}
              </span>

              <span className="ticket-subject">
                {ticket.subject}
              </span>

              <span>
                <i
                  className={`status ${
                    ticket.status?.toLowerCase()
                  }`}
                ></i>

                {ticket.status}
              </span>

              <span className="muted">
                {ticket.created_at
                  ? new Date(
                      ticket.created_at
                    ).toLocaleDateString()
                  : "-"}
              </span>

            </div>
          ))
        )}

      </div>

    </section>
  );
}

export default Overview;