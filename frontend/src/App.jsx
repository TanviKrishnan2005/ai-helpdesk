
import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

import Auth from "./components/Auth";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Overview from "./components/Overview";
import Assistant from "./components/Assistant";
import Tickets from "./components/Tickets";

const API_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "helpdesk_token";

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

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

  // Attach or remove the saved JWT for API requests.
  const setAuthToken = (token) => {
    if (token) {
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common.Authorization;
    }
  };

  // Check the saved token when the application opens.
  useEffect(() => {
    const checkAuthentication = async () => {
      const token = localStorage.getItem(TOKEN_KEY);

      if (!token) {
        setAuthChecking(false);
        return;
      }

      setAuthToken(token);

      try {
        const response = await axios.get(`${API_URL}/auth/me`);
        setCurrentUser(response.data);
      } catch (error) {
        localStorage.removeItem(TOKEN_KEY);
        setAuthToken(null);
        setCurrentUser(null);
      } finally {
        setAuthChecking(false);
      }
    };

    checkAuthentication();
  }, []);

  // Save the token after a successful login.
  const handleLogin = (loginData) => {
    localStorage.setItem(TOKEN_KEY, loginData.access_token);
    setAuthToken(loginData.access_token);

    setCurrentUser(loginData.user);
    setActivePage("overview");
  };

  // Clear the local session when the user logs out.
  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setCurrentUser(null);

    setTickets([]);
    setMessages([]);
    setMessage("");
    setShowTicketForm(false);
    setTicketMessage("");
    setSubject("");
    setDescription("");
    setCategory("General");
    setPriority("Medium");
    setActivePage("overview");
  };

  // Load tickets belonging to the authenticated user.
  const fetchTickets = useCallback(async () => {
    if (!localStorage.getItem(TOKEN_KEY)) {
      setTickets([]);
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/tickets/`);
      setTickets(response.data);
    } catch (error) {
      console.error("Failed to fetch tickets:", error);

      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  }, []);

  // Load tickets after authentication succeeds.
  useEffect(() => {
    if (currentUser) {
      fetchTickets();
    } else {
      setTickets([]);
    }
  }, [currentUser, fetchTickets]);

  // Refresh the ticket list when a ticket is updated elsewhere.
  useEffect(() => {
    const handleTicketsUpdated = () => {
      fetchTickets();
    };

    window.addEventListener("tickets-updated", handleTicketsUpdated);

    return () => {
      window.removeEventListener(
        "tickets-updated",
        handleTicketsUpdated
      );
    };
  }, [fetchTickets]);

  // Create a ticket from the Tickets page.
  const createTicket = async () => {
    if (!subject.trim() || !description.trim()) {
      setTicketMessage("Please enter a subject and description.");
      return;
    }

    setTicketLoading(true);
    setTicketMessage("");

    try {
      await axios.post(`${API_URL}/tickets/`, null, {
        params: {
          subject: subject.trim(),
          description: description.trim(),
          category,
          priority,
        },
      });

      setSubject("");
      setDescription("");
      setCategory("General");
      setPriority("Medium");
      setShowTicketForm(false);

      await fetchTickets();
      setTicketMessage("");
    } catch (error) {
      console.error("Failed to create ticket:", error);

      if (error.response?.status === 401) {
        handleLogout();
      } else {
        setTicketMessage(
          error.response?.data?.detail ||
            "Unable to create ticket. Please try again."
        );
      }
    } finally {
      setTicketLoading(false);
    }
  };

  // Send a message to the AI support assistant.
  const sendMessage = async (text = message) => {
    if (!text.trim() || loading) return;

    const userMessage = text.trim();

    setMessages((previous) => [
      ...previous,
      { type: "user", text: userMessage },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat/`, null, {
        params: { message: userMessage },
      });

      setMessages((previous) => [
        ...previous,
        {
          type: "ai",
          text: response.data.response,
        },
      ]);

      // The AI may have created a support ticket.
      if (response.data.resolved === false) {
        await fetchTickets();
      }
    } catch (error) {
      console.error("Failed to send message:", error);

      setMessages((previous) => [
        ...previous,
        {
          type: "ai",
          text: "I couldn't reach the support service. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Keep the application hidden while checking the saved session.
  if (authChecking) {
    return (
      <div className="auth-loading">
        Checking your session...
      </div>
    );
  }

  // Users must sign in before accessing the dashboard.
  if (!currentUser) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        ticketCount={tickets.length}
      />

      <main className="main-content">
        <Topbar
          activePage={activePage}
          currentUser={currentUser}
          onLogout={handleLogout}
        />

        {activePage === "overview" && (
          <Overview
            currentUser={currentUser}
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
