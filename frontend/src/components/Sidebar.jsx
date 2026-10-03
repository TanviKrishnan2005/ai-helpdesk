function Sidebar({ activePage, setActivePage, ticketCount }) {
  return (
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
          <b>{ticketCount}</b>
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
  );
}

export default Sidebar;