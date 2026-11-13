
function Sidebar({
  activePage,
  setActivePage,
  ticketCount,
  currentUser,
}) {
  const userName = currentUser?.name || "User";
  const userInitial = userName.charAt(0).toUpperCase();
  const userRole = currentUser?.role || "User";

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
          <div className="avatar">
            {userInitial}
          </div>

          <div>
            <strong>{userName}</strong>
            <small>{userRole}</small>
          </div>

          <span className="dots">•••</span>
        </div>

      </div>

    </aside>
  );
}

export default Sidebar;
