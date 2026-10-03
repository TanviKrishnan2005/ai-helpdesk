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
  const openTickets = tickets.filter(
    (ticket) =>
      ticket.status?.toLowerCase() === "open"
  ).length;

  const progressTickets = tickets.filter(
    (ticket) =>
      ticket.status?.toLowerCase() === "in progress"
  ).length;

  const resolvedTickets = tickets.filter(
    (ticket) =>
      ticket.status?.toLowerCase() === "resolved"
  ).length;

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
          onClick={() => {
            setShowTicketForm(true);
          }}
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

      <div className="full-ticket-list">

        {tickets.length === 0 ? (

          <div className="empty-chat">

            <div className="large-ai-icon">
              □
            </div>

            <h2>No tickets yet</h2>

            <p>
              Your support requests will appear here.
            </p>

          </div>

        ) : (

          tickets.map((ticket) => (

            <div
              className="full-ticket"
              key={ticket.id}
            >

              <div className="full-ticket-id">
                #{ticket.id}
              </div>

              <div className="full-ticket-main">

                <h3>{ticket.subject}</h3>

                <p>{ticket.description}</p>

                <div className="ticket-meta">

                  <span>
                    {ticket.category}
                  </span>

                  <span>
                    {ticket.priority} priority
                  </span>

                </div>

              </div>

              <div className="ticket-status">

                <i
                  className={`status ${
                    ticket.status?.toLowerCase()
                  }`}
                ></i>

                {ticket.status}

              </div>

            </div>

          ))

        )}

      </div>

    </section>
  );
}

export default Tickets;