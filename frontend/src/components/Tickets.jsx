
import { useMemo, useState } from "react";
import TicketForm from "./TicketForm";


function Tickets({
  tickets,
  setActivePage,
  showTicketForm,
  setShowTicketForm,
  subject,
  setSubject,
  description,
  setDescription,
  category,
  setCategory,
  priority,
  setPriority,
  createTicket,
  ticketLoading,
  ticketMessage,
}) {
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [updatingTicketId, setUpdatingTicketId] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");

  const openTickets = tickets.filter(
    (ticket) => ticket.status?.toLowerCase() === "open"
  ).length;

  const progressTickets = tickets.filter(
    (ticket) => ticket.status?.toLowerCase() === "in progress"
  ).length;

  const resolvedTickets = tickets.filter(
    (ticket) => ticket.status?.toLowerCase() === "resolved"
  ).length;

  const categories = useMemo(
    () =>
      [...new Set(
        tickets
          .map((ticket) => ticket.category)
          .filter(Boolean)
      )].sort(),
    [tickets]
  );

  const filteredTickets = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return tickets.filter((ticket) => {
      const matchesSearch =
        !query ||
        String(ticket.id).includes(query) ||
        ticket.subject?.toLowerCase().includes(query) ||
        ticket.description?.toLowerCase().includes(query);

      const matchesStatus =
        statusFilter === "All" ||
        ticket.status?.toLowerCase() === statusFilter.toLowerCase();

      const matchesPriority =
        priorityFilter === "All" ||
        ticket.priority?.toLowerCase() === priorityFilter.toLowerCase();

      const matchesCategory =
        categoryFilter === "All" ||
        ticket.category?.toLowerCase() === categoryFilter.toLowerCase();

      return (
        matchesSearch &&
        matchesStatus &&
        matchesPriority &&
        matchesCategory
      );
    });
  }, [
    tickets,
    searchQuery,
    statusFilter,
    priorityFilter,
    categoryFilter,
  ]);

  const hasActiveFilters =
    searchQuery.trim() !== "" ||
    statusFilter !== "All" ||
    priorityFilter !== "All" ||
    categoryFilter !== "All";

  function clearFilters() {
    setSearchQuery("");
    setStatusFilter("All");
    setPriorityFilter("All");
    setCategoryFilter("All");
  }

  async function updateStatus(ticketId, newStatus) {
    const token = localStorage.getItem("helpdesk_token");

    if (!token) {
      setStatusMessage("Please log in again.");
      return;
    }

    setUpdatingTicketId(ticketId);
    setStatusMessage("");

    try {
      const params = new URLSearchParams({ status: newStatus });

      const response = await fetch(
        `http://127.0.0.1:8000/tickets/${ticketId}/status?${params}`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not update ticket status."
        );
      }

      window.dispatchEvent(new Event("tickets-updated"));

      setSelectedTicket((current) =>
        current?.id === ticketId
          ? { ...current, status: newStatus }
          : current
      );

      setStatusMessage(
        `Ticket #${ticketId} updated to ${newStatus}.`
      );
    } catch (error) {
      setStatusMessage(
        error.message || "Something went wrong."
      );
    } finally {
      setUpdatingTicketId(null);
    }
  }

  return (
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
          onClick={() => setShowTicketForm(true)}
        >
          <span>+</span>
          New request
        </button>
      </div>

      {showTicketForm && (
        <TicketForm
          subject={subject}
          setSubject={setSubject}
          description={description}
          setDescription={setDescription}
          category={category}
          setCategory={setCategory}
          priority={priority}
          setPriority={setPriority}
          onCreate={createTicket}
          onCancel={() => setShowTicketForm(false)}
          loading={ticketLoading}
          message={ticketMessage}
        />
      )}

      <div className="ticket-summary">
        <div>
          <span>OPEN</span>
          <strong>{openTickets}</strong>
        </div>

        <div>
          <span>IN PROGRESS</span>
          <strong>{progressTickets}</strong>
        </div>

        <div>
          <span>RESOLVED</span>
          <strong>{resolvedTickets}</strong>
        </div>
      </div>

      {statusMessage && (
        <p role="status" className="ticket-feedback">
          {statusMessage}
        </p>
      )}

      <div className="ticket-filters">
        <div className="ticket-search">
          <label htmlFor="ticket-search">Search tickets</label>
          <input
            id="ticket-search"
            type="search"
            placeholder="Search by ID, subject or description..."
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </div>

        <div className="ticket-filter-row">
          <div className="ticket-filter">
            <label htmlFor="ticket-status-filter">Status</label>
            <select
              id="ticket-status-filter"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="All">All statuses</option>
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>

          <div className="ticket-filter">
            <label htmlFor="ticket-priority-filter">Priority</label>
            <select
              id="ticket-priority-filter"
              value={priorityFilter}
              onChange={(event) =>
                setPriorityFilter(event.target.value)
              }
            >
              <option value="All">All priorities</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>

          <div className="ticket-filter">
            <label htmlFor="ticket-category-filter">Category</label>
            <select
              id="ticket-category-filter"
              value={categoryFilter}
              onChange={(event) =>
                setCategoryFilter(event.target.value)
              }
            >
              <option value="All">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              className="ticket-clear-filters"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          )}
        </div>

        <p className="ticket-result-count" aria-live="polite">
          Showing {filteredTickets.length} of {tickets.length} tickets
        </p>
      </div>

      <div className="full-ticket-list">
        {tickets.length === 0 ? (
          <div className="empty-chat">
            <div className="large-ai-icon">□</div>
            <h2>No tickets yet</h2>
            <p>Your support requests will appear here.</p>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="empty-chat">
            <div className="large-ai-icon">⌕</div>
            <h2>No matching tickets</h2>
            <p>
              Try changing your search or removing some filters.
            </p>
            <button
              type="button"
              className="ticket-details-button"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          </div>
        ) : (
          filteredTickets.map((ticket) => (
            <div className="full-ticket" key={ticket.id}>
              <div className="full-ticket-id">#{ticket.id}</div>

              <div className="full-ticket-main">
                <h3>{ticket.subject}</h3>
                <p>{ticket.description}</p>

                <div className="ticket-meta">
                  <span>{ticket.category}</span>
                  <span>{ticket.priority} priority</span>
                </div>

                <button
                  type="button"
                  className="ticket-details-button"
                  aria-expanded={selectedTicket?.id === ticket.id}
                  onClick={() =>
                    setSelectedTicket(
                      selectedTicket?.id === ticket.id
                        ? null
                        : ticket
                    )
                  }
                >
                  {selectedTicket?.id === ticket.id
                    ? "Hide details"
                    : "View details"}
                </button>

                {selectedTicket?.id === ticket.id && (
                  <div className="ticket-details">
                    <p>
                      <strong>Ticket ID:</strong> #{ticket.id}
                    </p>
                    <p>
                      <strong>Description:</strong>{" "}
                      {ticket.description}
                    </p>
                    <p>
                      <strong>Category:</strong> {ticket.category}
                    </p>
                    <p>
                      <strong>Priority:</strong> {ticket.priority}
                    </p>
                    <p>
                      <strong>Status:</strong> {ticket.status}
                    </p>
                    <p>
                      <strong>Created:</strong>{" "}
                      {ticket.created_at
                        ? new Date(ticket.created_at).toLocaleString()
                        : "Not available"}
                    </p>
                  </div>
                )}
              </div>

              <div className="ticket-status">
                <i
                  className={`status ${
                    ticket.status?.toLowerCase().replace(/\s+/g, "-")
                  }`}
                />

                <span>{ticket.status}</span>

                <label>
                  <span className="sr-only">
                    Update ticket status
                  </span>
                  <select
                    value={ticket.status || "Open"}
                    disabled={updatingTicketId === ticket.id}
                    onChange={(event) =>
                      updateStatus(ticket.id, event.target.value)
                    }
                  >
                    <option value="Open">Open</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Resolved">Resolved</option>
                  </select>
                </label>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default Tickets;
