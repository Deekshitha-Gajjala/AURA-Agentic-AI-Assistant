import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function ChatWindow({
  messages = [],
  loading = false
}) {
  return (
    <main className="chat-window">

      {messages.length === 0 ? (

        <div className="welcome-area">

          <div className="welcome-icon">
            <Bot
              size={22}
              strokeWidth={1.7}
            />
          </div>

          <h1>
            Good evening, Deekshitha
          </h1>

          <p>
            What would you like to explore?
          </p>

        </div>

      ) : (

        <div className="messages-container">

          {messages.map((message) => (

            <div
              key={message.id}
              className={`message-row ${
                message.role === "user"
                  ? "user-message"
                  : "assistant-message"
              }`}
            >

              <div className="message-avatar">

                {message.role === "user" ? (

                  <User
                    size={16}
                    strokeWidth={1.8}
                  />

                ) : (

                  <Bot
                    size={16}
                    strokeWidth={1.8}
                  />

                )}

              </div>


              <div className="message-content">

                <div className="message-name">
                  {message.role === "user"
                    ? "You"
                    : "AURA"}
                </div>


                <div className="message-text">

                  {message.role === "user" ? (

                    message.content

                  ) : (

                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                    >
                      {message.content}
                    </ReactMarkdown>

                  )}

                </div>

              </div>

            </div>

          ))}


          {loading && (

            <div className="message-row assistant-message">

              <div className="message-avatar">

                <Bot
                  size={16}
                  strokeWidth={1.8}
                />

              </div>


              <div className="message-content">

                <div className="message-name">
                  AURA
                </div>


                <div className="typing-indicator">

                  <span></span>
                  <span></span>
                  <span></span>

                </div>

              </div>

            </div>

          )}

        </div>

      )}

    </main>
  );
}

export default ChatWindow;