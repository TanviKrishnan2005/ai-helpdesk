
import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

import Auth from "./components/Auth";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Overview from "./components/Overview";
import Assistant from "./components/Assistant";
import Tickets from "./components/Tickets";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Allow enough time for a free Render instance to wake up.
axios.defaults.timeout = 120000;

const TOKEN_KEY = "helpdesk_token";
const MAX_HISTORY_MESSAGES = 30;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [authConnectionFailed, setAuthConnectionFailed] = useState(false);
  const [serviceError, setServiceError] = useState("");

  const [activePage, setActivePage] = useState("overview");

  // Responsive sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Conversation history
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [loadingConversationId, setLoadingConversationId] = useState(null);

  // Keep track of the currently open conversation.
  const activeConversationRef = useRef(null);

  const [tickets, setTickets] = useState([]);
  const [showTicketForm, setShowTicketForm] = useState(false);

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("General");
  const [priority, setPriority] = useState("Medium");

  const [ticketLoading, setTicketLoading] = useState(false);
  const [ticketMessage, setTicketMessage] = useState("");

  // Attach or remove the saved JWT.
  const setAuthToken = (token) => {
    if (token) {
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common.Authorization;
    }
  };

  // Fetch saved conversations.
  const fetchConversations = useCallback(async () => {
    if (!localStorage.getItem(TOKEN_KEY)) {
      setConversations([]);
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/conversations/`);
      setConversations(response.data);
    } catch (error) {
      console.error("Failed to fetch conversations:", error);

      if (error.response?.status === 401) {
        handleLogout();
      } else {
        setServiceError(
          !error.response
            ? "Can't connect to the helpdesk server. Check your internet connection and try again."
            : "Conversation history is temporarily unavailable. Please try again."
        );
      }
    }
  }, []);

  // Check authentication when the application opens.
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
        if (error.response?.status === 401) {
          // Only clear the session when the server confirms the token is invalid.
          localStorage.removeItem(TOKEN_KEY);
          setAuthToken(null);
          setCurrentUser(null);
        } else {
          // Keep the token when the server is temporarily unreachable.
          setAuthConnectionFailed(true);
          setServiceError(
            !error.response
              ? "Can't reach the helpdesk server. Check your connection and try again."
              : "The helpdesk server is temporarily unavailable. Please try again."
          );
        }
      } finally {
        setAuthChecking(false);
      }
    };

    checkAuthentication();
  }, []);

  // Fetch conversations after login.
  useEffect(() => {
    if (currentUser) {
      fetchConversations();
    } else {
      setConversations([]);
    }
  }, [currentUser, fetchConversations]);

  // Save token after successful login.
  const handleLogin = (loginData) => {
    localStorage.setItem(TOKEN_KEY, loginData.access_token);
    setAuthToken(loginData.access_token);

    setCurrentUser(loginData.user);
    setActivePage("overview");
  };

  // Logout and clear local application state.
  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setCurrentUser(null);

    setTickets([]);
    setMessages([]);
    setMessage("");

    setConversations([]);
    setActiveConversationId(null);
    activeConversationRef.current = null;

    setLoading(false);
    setLoadingConversationId(null);

    setShowTicketForm(false);
    setTicketMessage("");
    setSubject("");
    setDescription("");
    setCategory("General");
    setPriority("Medium");

    setActivePage("overview");
    setSidebarOpen(false);
  };

  // Fetch tickets belonging to the authenticated user.
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
      } else {
        setServiceError(
          !error.response
            ? "Can't connect to the helpdesk server. Check your internet connection and try again."
            : "Tickets are temporarily unavailable. Please try again."
        );
      }
    }
  }, []);

  // Fetch tickets after authentication.
  useEffect(() => {
    if (currentUser) {
      fetchTickets();
    } else {
      setTickets([]);
    }
  }, [currentUser, fetchTickets]);

  // Listen for ticket updates.
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

  // Create a new conversation.
  const createConversation = async () => {
    try {
      const response = await axios.post(`${API_URL}/conversations/`, {
        title: "New Chat",
      });

      const newId = response.data.id;
      setServiceError("");

      activeConversationRef.current = newId;
      setActiveConversationId(newId);
      setMessages([]);
      setMessage("");
      setActivePage("assistant");

      await fetchConversations();

      return newId;
    } catch (error) {
      console.error("Failed to create conversation:", error);
      setServiceError(
        !error.response
          ? "Can't connect to the helpdesk server. Check your internet connection and try again."
          : "Couldn't create a new conversation. Please try again."
      );
      return null;
    }
  };

  // Open an existing conversation.
  const openConversation = async (id) => {
    try {
      const response = await axios.get(
        `${API_URL}/conversations/${id}`
      );

      activeConversationRef.current = id;
      setActiveConversationId(id);

      setMessages(
        response.data.messages.map((msg) => ({
          type: msg.role === "user" ? "user" : "ai",
          text: msg.content,
        }))
      );

      setMessage("");
      setActivePage("assistant");
      setServiceError("");
    } catch (error) {
      console.error("Failed to open conversation:", error);
      setServiceError(
        !error.response
          ? "Can't connect to the helpdesk server. Check your internet connection and try again."
          : "Couldn't open this conversation. Please try again."
      );
    }
  };

  // Delete a conversation.
  const deleteConversation = async (id) => {
    try {
      await axios.delete(`${API_URL}/conversations/${id}`);

      if (activeConversationRef.current === id) {
        activeConversationRef.current = null;
        setActiveConversationId(null);
        setMessages([]);
      }

      await fetchConversations();
      setServiceError("");
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      setServiceError(
        !error.response
          ? "Can't connect to the helpdesk server. Check your internet connection and try again."
          : "Couldn't delete this conversation. Please try again."
      );
    }
  };

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
      setServiceError("");
    } catch (error) {
      console.error("Failed to create ticket:", error);

      if (error.response?.status === 401) {
        handleLogout();
      } else if (!error.response) {
        setTicketMessage("Can't connect to the helpdesk server. Check your connection and try again.");
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

  // Save a message to the database.
  const saveConversationMessage = async (conversationId, role, content) => {
    await axios.post(
      `${API_URL}/conversations/${conversationId}/messages`,
      {
        role,
        content,
      }
    );
  };

  // Send a message and save the conversation.
  const sendMessage = async (text = message) => {
    if (typeof text !== "string" || !text.trim() || loading) {
      return;
    }

    const userMessage = text.trim();

    const conversationHistory = messages
      .slice(-MAX_HISTORY_MESSAGES)
      .filter(
        (msg) =>
          (msg.type === "user" || msg.type === "ai") &&
          typeof msg.text === "string" &&
          msg.text.trim()
      )
      .map((msg) => ({
        role: msg.type === "user" ? "user" : "assistant",
        content: msg.text,
      }));

    setMessage("");
    setLoading(true);

    let conversationId = activeConversationRef.current;

    try {
      // Create a conversation if this is a new chat.
      if (!conversationId) {
        conversationId = await createConversation();

        if (!conversationId) {
          throw new Error("Could not create conversation.");
        }
      }

      // Show the user's message immediately, before waiting for the
      // database save or the AI response.
      if (activeConversationRef.current === conversationId) {
        setMessages((previous) => [
          ...previous,
          { type: "user", text: userMessage },
        ]);
      }

      // Show the typing indicator only after the user's message is visible.
      setLoadingConversationId(conversationId);

      // Save the user's message in the background of the chat flow.
      await saveConversationMessage(
        conversationId,
        "user",
        userMessage
      );

      // Get the AI response.
      const response = await axios.post(
        `${API_URL}/chat/`,
        {
          history: conversationHistory,
        },
        {
          params: {
            message: userMessage,
          },
        }
      );

      const aiMessage = {
        type: "ai",
        text: response.data.response,
        sources: response.data.sources ?? [],
        resolved: response.data.resolved,
        confidence: response.data.confidence,
        ticket_id: response.data.ticket_id,
      };

      // Only show the response in the conversation that requested it.
      if (activeConversationRef.current === conversationId) {
        setMessages((previous) => [
          ...previous,
          aiMessage,
        ]);
      }

      // Hide the typing indicator as soon as the AI response is displayed.
      setLoadingConversationId(null);

      // Save the AI response to its original conversation.
      await saveConversationMessage(
        conversationId,
        "assistant",
        aiMessage.text
      );

      await fetchConversations();
      setServiceError("");

      // Refresh tickets if the assistant escalated the issue.
      if (response.data.resolved === false) {
        await fetchTickets();
      }
    } catch (error) {
      console.error("Failed to send message:", error);

      const errorText = !error.response
        ? "I couldn't connect to the support server. Check your internet connection and try again."
        : error.response.status >= 500
          ? "The support service is temporarily unavailable. Please try again in a moment."
          : error.response.data?.detail || "I couldn't process that message. Please try again.";

      if (!error.response || error.response.status >= 500) {
        setServiceError(errorText);
      }

      if (
        conversationId &&
        activeConversationRef.current === conversationId
      ) {
        setMessages((previous) => [
          ...previous,
          {
            type: "ai",
            text: errorText,
          },
        ]);
      }
    } finally {
      setLoading(false);
      setLoadingConversationId(null);
    }
  };

  // Show loading while checking authentication.
  if (authChecking) {
    return (
      <div className="auth-loading">
        Checking your session...
      </div>
    );
  }

  // If authentication could not be checked because the server is down,
  // preserve the saved session and let the user retry instead of logging out.
  if (authConnectionFailed && !currentUser) {
    return (
      <div className="auth-loading" style={{ padding: "24px", textAlign: "center" }}>
        <h2>Helpdesk temporarily unavailable</h2>
        <p>{serviceError || "We couldn't connect to the server."}</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          style={{ marginTop: "12px", padding: "10px 18px", cursor: "pointer" }}
        >
          Try again
        </button>
      </div>
    );
  }

  // Require login.
  if (!currentUser) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        setActivePage={(page) => {
          setActivePage(page);
          setSidebarOpen(false);
        }}
        ticketCount={tickets.length}
        currentUser={currentUser}
        conversations={conversations}
        activeConversationId={activeConversationId}
        createConversation={async () => {
          await createConversation();
          setSidebarOpen(false);
        }}
        openConversation={async (id) => {
          await openConversation(id);
          setSidebarOpen(false);
        }}
        deleteConversation={deleteConversation}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
      />

      <main className="main-content">
        {serviceError && (
          <div
            role="alert"
            style={{
              margin: "12px 20px 0",
              padding: "12px 16px",
              border: "1px solid #f0c36d",
              borderRadius: "8px",
              background: "#fff8e7",
              color: "#754c00",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "12px",
              fontSize: "13px",
            }}
          >
            <span>{serviceError}</span>
            <button
              type="button"
              onClick={() => setServiceError("")}
              aria-label="Dismiss error message"
              style={{ border: 0, background: "transparent", cursor: "pointer", fontSize: "18px" }}
            >
              ×
            </button>
          </div>
        )}

        <Topbar
          activePage={activePage}
          currentUser={currentUser}
          onLogout={handleLogout}
          onMenuClick={() => setSidebarOpen((previous) => !previous)}
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
            loading={
              loadingConversationId === activeConversationId &&
              loadingConversationId !== null
            }
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
