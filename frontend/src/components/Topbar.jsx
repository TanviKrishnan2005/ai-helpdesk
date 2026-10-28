
function Topbar({ activePage, currentUser, onLogout }) {
  const pageNames = {
    overview: "Overview",
    assistant: "AI Assistant",
    tickets: "Tickets",
  };

  const userName = currentUser?.name || "User";
  const initial = userName.charAt(0).toUpperCase();

  return (
    <header className="topbar">
      <div className="breadcrumbs">
        Workspace <span>/</span>{" "}
        {pageNames[activePage] || activePage}
      </div>

      <div className="top-actions">
        <span className="top-user-name">{userName}</span>

        <div className="top-avatar" title={userName}>
          {initial}
        </div>

        <button
          type="button"
          className="logout-button"
          onClick={onLogout}
          title="Sign out of your account"
        >
          Log out
        </button>
      </div>
    </header>
  );
}

export default Topbar;
