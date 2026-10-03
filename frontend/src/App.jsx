import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Overview from "./components/Overview";
import Assistant from "./components/Assistant";
import Tickets from "./components/Tickets";

function App() {
  const [activePage, setActivePage] = useState("overview");

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const [tickets, setTickets] = useState([]);
  const [showTicketForm, setShowTicketForm] = useState(false);

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("General");
  const [priority, setPriority] = useState("Medium");

  const [ticketLoading, setTicketLoading] = useState(false);
  const [ticketMessage, setTicketMessage] = useState("");

  // Get tickets from backend
  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const response = await axios.get(
          "http://127.0.0.1:8000/tickets/"
        );

        setTickets(response.data);
      } catch (error) {
        console.error(
          "Failed to fetch tickets:",
          error
        );
      }
    };

    fetchTickets();
  }, []);

  const createTicket = async () => {
    if (!subject.trim() || !description.trim()) {
      setTicketMessage(
        "Please enter a subject and description."
      );
      return;
    }

    setTicketLoading(true);
    setTicketMessage("");

    try {
      await axios.post(
        "http://127.0.0.1:8000/tickets/",
        null,
        {
          params: {
            subject: subject.trim(),
            description: description.trim(),
            category,
            priority,
          },
        }
      );

      setSubject("");
      setDescription("");
      setCategory("General");
      setPriority("Medium");

      const response = await axios.get(
        "http://127.0.0.1:8000/tickets/"
      );

      setTickets(response.data);

      setShowTicketForm(false);
    } catch (error) {
      console.error(
        "Failed to create ticket:",
        error
      );

      setTicketMessage(
        "Unable to create ticket. Please try again."
      );
    } finally {
      setTicketLoading(false);
    }
  };

  // Send message to backend
  const sendMessage = async (text = message) => {
    if (!text.trim() || loading) return;

    const userMessage = text.trim();

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: userMessage,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/chat/",
        null,
        {
          params: {
            message: userMessage,
          },
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: response.data.response,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: "I couldn't reach the support service. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">

      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        ticketCount={tickets.length}
      />

      <main className="main-content">

        <Topbar activePage={activePage} />

        {activePage === "overview" && (
          <Overview
            message={message}
            setMessage={setMessage}
            sendMessage={sendMessage}
            setActivePage={setActivePage}
            tickets={tickets}
          />
        )}

        {activePage === "assistant" && (
          <Assistant
            messages={messages}
            message={message}
            setMessage={setMessage}
            sendMessage={sendMessage}
            loading={loading}
          />
        )}

        {activePage === "tickets" && (
          <Tickets
            tickets={tickets}
            setActivePage={setActivePage}
            showTicketForm={showTicketForm}
            setShowTicketForm={setShowTicketForm}
            subject={subject}
            setSubject={setSubject}
            description={description}
            setDescription={setDescription}
            category={category}
            setCategory={setCategory}
            priority={priority}
            setPriority={setPriority}
            createTicket={createTicket}
            ticketLoading={ticketLoading}
            ticketMessage={ticketMessage}
          />
        )}

      </main>

    </div>
  );
}

export default App;