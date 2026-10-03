function TicketForm({
  subject,
  setSubject,
  description,
  setDescription,
  category,
  setCategory,
  priority,
  setPriority,
  onCreate,
  onCancel,
  loading,
  message,
}) {
  return (
    <div className="ticket-form">

      <div className="section-heading">
        <div>
          <p className="eyebrow">NEW REQUEST</p>
          <h3>Create a support ticket</h3>
        </div>
      </div>

      <div className="form-group">
        <label>Subject</label>

        <input
          type="text"
          placeholder="What do you need help with?"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Description</label>

        <textarea
          placeholder="Describe your problem..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="form-row">

        <div className="form-group">
          <label>Category</label>

          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="General">General</option>
            <option value="Account">Account</option>
            <option value="Network">Network</option>
            <option value="Software">Software</option>
            <option value="Payment">Payment</option>
          </select>
        </div>

        <div className="form-group">
          <label>Priority</label>

          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>

      </div>

      {message && (
        <p className="ticket-form-message">
          {message}
        </p>
      )}

      <div className="ticket-form-actions">

        <button
          className="cancel-button"
          onClick={onCancel}
        >
          Cancel
        </button>

        <button
          className="new-ticket"
          onClick={onCreate}
          disabled={loading}
        >
          {loading ? "Creating..." : "Create Ticket"}
        </button>

      </div>

    </div>
  );
}

export default TicketForm;