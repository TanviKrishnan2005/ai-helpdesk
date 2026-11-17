import { useState } from "react";

function Sidebar({
  activePage,
  setActivePage,
  ticketCount,
  currentUser,
  conversations = [],
  activeConversationId,
  createConversation,
  openConversation,
  deleteConversation,
  sidebarOpen,
  setSidebarOpen,
}) {
  const [conversationToDelete, setConversationToDelete] = useState(null);

  const userName = currentUser?.name || "User";
  const userInitial = userName.charAt(0).toUpperCase();
  const userRole = currentUser?.role || "User";

  const confirmDelete = () => {
    if (conversationToDelete !== null) {
      deleteConversation(conversationToDelete);
      setConversationToDelete(null);
    }
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={closeSidebar}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">H</div>
          <div>
            <strong>helpdesk</strong>
            <span>support workspace</span>
          </div>

          <button
            className="sidebar-close-button"
            onClick={closeSidebar}
            aria-label="Close navigation menu"
          >
            ×
          </button>
        </div>

        <div className="nav-section">
          <p className="nav-label">WORKSPACE</p>

          <button
            className={`nav-item ${activePage === "overview" ? "active" : ""}`}
            onClick={() => setActivePage("overview")}
          >
            <span>⌂</span>
            Overview
          </button>

          <button
            className={`nav-item ${activePage === "assistant" ? "active" : ""}`}
            onClick={() => setActivePage("assistant")}
          >
            <span>✦</span>
            AI Assistant
          </button>

          <button
            className={`nav-item ${activePage === "tickets" ? "active" : ""}`}
            onClick={() => setActivePage("tickets")}
          >
            <span>□</span>
            My Tickets
            <b>{ticketCount}</b>
          </button>
        </div>

        {/* Conversation History */}
        <div className="nav-section conversation-section">
          <div className="conversation-heading">
            <p className="nav-label">YOUR CHATS</p>
          </div>

          <button
            className="new-chat-button"
            onClick={createConversation}
            title="Start a new chat"
          >
            + New Chat
          </button>

          <div className="conversation-list">
            {conversations.length === 0 ? (
              <p className="empty-conversations">No conversations yet</p>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`conversation-item ${
                    activeConversationId === conversation.id ? "active" : ""
                  }`}
                >
                  <button
                    className="conversation-open"
                    onClick={() => openConversation(conversation.id)}
                    title={conversation.title}
                  >
                    <span>◷</span>
                    <span className="conversation-title">
                      {conversation.title}
                    </span>
                  </button>

                  <button
                    className="delete-conversation"
                    onClick={() => setConversationToDelete(conversation.id)}
                    title="Delete conversation"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Resources */}
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

        {/* Sidebar Footer */}
        <div className="sidebar-bottom">
          <div className="mini-status">
            <span></span>
            All systems operational
          </div>

          <div className="profile">
            <div className="avatar">{userInitial}</div>
            <div>
              <strong>{userName}</strong>
              <small>{userRole}</small>
            </div>
            <span className="dots">•••</span>
          </div>
        </div>

        {/* Custom Delete Modal */}
        {conversationToDelete !== null && (
          <div
            className="delete-modal-overlay"
            onClick={() => setConversationToDelete(null)}
          >
            <div
              className="delete-modal"
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-modal-title"
            >
              <div className="delete-modal-icon">!</div>

              <h3 id="delete-modal-title">Delete conversation?</h3>

              <p>
                Are you sure you want to delete this conversation?
                This action cannot be undone.
              </p>

              <div className="delete-modal-actions">
                <button
                  className="delete-cancel-button"
                  onClick={() => setConversationToDelete(null)}
                >
                  Cancel
                </button>

                <button
                  className="delete-confirm-button"
                  onClick={confirmDelete}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}

export default Sidebar;
