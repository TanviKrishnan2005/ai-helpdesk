
import { useState } from "react";
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

  const openTickets = tickets.filter(
    (ticket) => ticket.status?.toLowerCase() === "open"
  ).length;

  const progressTickets = tickets.filter(
    (ticket) => ticket.status?.toLowerCase() === "in progress"
  ).length;

  const resolvedTickets = tickets.filter(
    (ticket) => ticket.status?.toLowerCase() === "resolved"
  ).length;

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

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not update ticket status.");
      }

      // Notify the parent component to reload the ticket list.
      window.dispatchEvent(new Event("tickets-updated"));

      setSelectedTicket((current) =>
        current?.id === ticketId
          ? { ...current, status: newStatus }
          : current
      );

      setStatusMessage(`Ticket #${ticketId} updated to ${newStatus}.`);
    } catch (error) {
      setStatusMessage(error.message || "Something went wrong.");
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

      <div className="full-ticket-list">
        {tickets.length === 0 ? (
          <div className="empty-chat">
            <div className="large-ai-icon">□</div>
            <h2>No tickets yet</h2>
            <p>Your support requests will appear here.</p>
          </div>
        ) : (
          tickets.map((ticket) => (
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
                  onClick={() =>
                    setSelectedTicket(
                      selectedTicket?.id === ticket.id ? null : ticket
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
                      <strong>Description:</strong> {ticket.description}
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
                  <span className="sr-only">Update ticket status</span>
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
