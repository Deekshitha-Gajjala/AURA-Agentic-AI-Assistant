import React, { useState } from "react";

import {
  Plus,
  Home,
  Library,
  Settings,
  FileText,
  MessageSquare,
  Trash2,
  MoreHorizontal,
} from "lucide-react";

function Sidebar({
  onNewChat,
  onDeleteChat,
  onDeleteAllChats,
  conversations = [],
  currentConversationId = null,
  onSelectConversation,
  uploadedFiles = [],
  uploadedDocuments = [],
  selectedDocumentId = null,
  onSelectDocument,
  onDeleteDocument,
  darkMode = false,
  onLogout,
}) {
  const chats = Array.isArray(conversations)
    ? conversations
    : [];

  const documents = Array.isArray(uploadedDocuments)
    ? uploadedDocuments
    : [];

  const files = Array.isArray(uploadedFiles)
    ? uploadedFiles
    : [];

  const [profileOpen, setProfileOpen] = useState(false);

  const getTitle = (chat) => {
    const title =
      chat?.title ||
      chat?.name ||
      "New conversation";

    return String(title).trim() || "New conversation";
  };

  const formatDate = (value) => {
    if (!value) return "";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "";
    }

    const now = new Date();

    const sameDay =
      date.getFullYear() === now.getFullYear() &&
      date.getMonth() === now.getMonth() &&
      date.getDate() === now.getDate();

    if (sameDay) {
      return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
      });
    }

    return date.toLocaleDateString([], {
      day: "numeric",
      month: "short",
    });
  };

  const handleDeleteAll = () => {
    if (!chats.length) return;

    if (
      typeof onDeleteAllChats ===
      "function"
    ) {
      onDeleteAllChats();
    }
  };

  return (
    <>
      <style>{`
        .aura-sidebar {
          width: 356px;
          min-width: 356px;
          height: 100vh;
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          background: #f7f7f8;
          border-right: 1px solid #e5e5e7;
          overflow: hidden;
          color: #202123;
        }

        .aura-header {
          padding: 28px 24px 22px;
        }

        .aura-brand {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .aura-mark {
          width: 46px;
          height: 46px;
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #171717;
          color: white;
          font-size: 21px;
          font-weight: 700;
        }

        .aura-name {
          font-size: 24px;
          line-height: 1.1;
          font-weight: 700;
          letter-spacing: -.4px;
        }

        .aura-tag {
          margin-top: 5px;
          color: #737783;
          font-size: 15px;
        }

        .aura-new {
          width: calc(100% - 32px);
          margin: 0 16px 16px;
          height: 54px;
          border: 0;
          border-radius: 12px;
          background: #171717;
          color: white;
          display: flex;
          align-items: center;
          gap: 15px;
          padding: 0 18px;
          font-size: 17px;
          font-weight: 600;
          cursor: pointer;
        }

        .aura-new:hover {
          background: #292929;
        }

        .aura-nav {
          padding: 8px 16px 0;
        }

        .aura-nav-btn {
          width: 100%;
          height: 50px;
          border: 0;
          border-radius: 11px;
          background: transparent;
          display: flex;
          align-items: center;
          gap: 15px;
          padding: 0 16px;
          color: #30333a;
          font-size: 16px;
          text-align: left;
          cursor: pointer;
        }

        .aura-nav-btn:hover {
          background: #ededee;
        }

        .aura-nav-btn.active {
          background: #e6e6e8;
          color: #171717;
          font-weight: 600;
        }

        .aura-scroll {
          flex: 1;
          min-height: 0;
          overflow-y: auto;
          padding: 24px 16px 18px;
        }

        .aura-section {
          margin-bottom: 24px;
        }

        .aura-section-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 14px 9px;
          color: #8a8f9b;
          font-size: 13px;
          font-weight: 700;
          letter-spacing: .5px;
          text-transform: uppercase;
        }

        .aura-more {
          border: 0;
          background: transparent;
          color: #9296a0;
          cursor: pointer;
          padding: 3px;
          border-radius: 6px;
        }

        .aura-more:hover {
          background: #e7e7e8;
        }

        .aura-list {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .aura-file {
          width: 100%;
          box-sizing: border-box;
          min-height: 44px;
          display: flex;
          align-items: center;
          gap: 3px;
          padding: 4px 5px 4px 9px;
          border: 0;
          border-radius: 9px;
          background: transparent;
          color: #555963;
        }

        .aura-file:hover {
          background: #ededee;
        }

        .aura-file.active {
          background: #e6e6e8;
          color: #171717;
          font-weight: 600;
        }

        .aura-file-select {
          min-width: 0;
          flex: 1;
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 5px 2px;
          border: 0;
          background: transparent;
          color: inherit;
          font: inherit;
          text-align: left;
          cursor: pointer;
        }

        .aura-file-name {
          min-width: 0;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .aura-file-check {
          flex: 0 0 auto;
          font-size: 14px;
          color: #171717;
        }

        .aura-file-delete {
          width: 32px;
          height: 32px;
          flex: 0 0 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 0;
          border-radius: 7px;
          background: transparent;
          color: #8b8f98;
          cursor: pointer;
          opacity: 0;
        }

        .aura-file:hover .aura-file-delete,
        .aura-file.active .aura-file-delete {
          opacity: 1;
        }

        .aura-file-delete:hover {
          background: #dedee0;
          color: #b42318;
        }

        .aura-chat {
          width: 100%;
          min-height: 54px;
          box-sizing: border-box;
          border: 0;
          border-radius: 10px;
          background: transparent;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 7px 6px 7px 10px;
          text-align: left;
          cursor: pointer;
          color: #3b3e46;
        }

        .aura-chat:hover {
          background: #ececee;
        }

        .aura-chat.active {
          background: #e3e3e5;
          color: #171717;
        }

        .aura-chat-icon {
          width: 28px;
          flex: 0 0 28px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #5e626b;
        }

        .aura-chat-body {
          min-width: 0;
          flex: 1;
        }

        .aura-chat-title {
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
          font-size: 14px;
          font-weight: 500;
        }

        .aura-chat-date {
          margin-top: 3px;
          color: #9699a2;
          font-size: 11px;
        }

        .aura-chat-delete {
          width: 32px;
          height: 32px;
          flex: 0 0 32px;
          border: 0;
          border-radius: 7px;
          background: transparent;
          color: #8b8f98;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          opacity: 0;
        }

        .aura-chat:hover .aura-chat-delete,
        .aura-chat.active .aura-chat-delete {
          opacity: 1;
        }

        .aura-chat-delete:hover {
          background: #dedee0;
          color: #b42318;
        }

        .aura-empty {
          padding: 9px 14px;
          color: #9296a0;
          font-size: 13px;
          line-height: 1.45;
        }

        .aura-footer {
          border-top: 1px solid #e3e3e5;
          padding: 13px 16px 16px;
        }

        .aura-profile {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 10px;
        }

        .aura-avatar {
          width: 42px;
          height: 42px;
          border-radius: 50%;
          background: #e6e6e8;
          color: #555861;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          font-weight: 600;
        }

        .aura-profile-name {
          font-size: 15px;
          font-weight: 600;
        }

        .aura-profile-type {
          margin-top: 3px;
          font-size: 12px;
          color: #8a8e98;
        }

        .aura-profile {
          position: relative;
          width: 100%;
          box-sizing: border-box;
          border: 0;
          background: transparent;
          text-align: left;
          cursor: pointer;
          border-radius: 10px;
        }

        .aura-profile-info {
          min-width: 0;
        }

        .aura-profile:hover {
          background: #ededee;
        }

        .aura-profile-menu {
          position: absolute;
          left: 16px;
          right: 16px;
          bottom: 78px;
          background: #ffffff;
          border: 1px solid #dedee2;
          border-radius: 10px;
          padding: 6px;
          box-shadow: 0 10px 28px rgba(0,0,0,.12);
          z-index: 30;
        }

        .aura-logout-btn {
          width: 100%;
          border: 0;
          background: transparent;
          border-radius: 7px;
          padding: 9px 10px;
          text-align: left;
          font-size: 14px;
          cursor: pointer;
          color: #202123;
        }

        .aura-logout-btn:hover {
          background: #f0f0f1;
        }

        .aura-dark .aura-sidebar {
          background: #17191c;
          border-right-color: #2d3035;
          color: #eceff1;
        }

        .aura-dark .aura-name,
        .aura-dark .aura-profile-name {
          color: #f1f3f4;
        }

        .aura-dark .aura-tag,
        .aura-dark .aura-profile-type,
        .aura-dark .aura-empty,
        .aura-dark .aura-chat-date {
          color: #9298a2;
        }

        .aura-dark .aura-nav-btn {
          color: #d4d8dd;
        }

        .aura-dark .aura-nav-btn:hover,
        .aura-dark .aura-file:hover,
        .aura-dark .aura-chat:hover {
          background: #22252a;
        }

        .aura-dark .aura-nav-btn.active,
        .aura-dark .aura-file.active,
        .aura-dark .aura-chat.active {
          background: #2a2e34;
          color: #fff;
        }

        .aura-dark .aura-file,
        .aura-dark .aura-chat {
          color: #dfe3e7;
        }

        .aura-dark .aura-file-name,
        .aura-dark .aura-chat-title {
          color: #e7eaed;
        }

        .aura-dark .aura-footer {
          border-top-color: #2d3035;
        }

        .aura-dark .aura-avatar {
          background: #30343a;
          color: #e7eaed;
        }

        .aura-dark .aura-profile:hover {
          background: #24272c;
        }

        .aura-dark .aura-profile-menu {
          background: #22252a;
          border-color: #3a3e45;
          box-shadow: 0 12px 30px rgba(0,0,0,.35);
        }

        .aura-dark .aura-logout-btn {
          color: #f0f2f4;
        }

        .aura-dark .aura-logout-btn:hover {
          background: #30343a;
        }

        .aura-dark .aura-section-head {
          color: #8f959f;
        }

        .aura-dark .aura-file-delete,
        .aura-dark .aura-chat-delete,
        .aura-dark .aura-more {
          color: #8f959f;
        }

        .aura-dark .aura-file-delete:hover,
        .aura-dark .aura-chat-delete:hover,
        .aura-dark .aura-more:hover {
          background: #30343a;
          color: #fff;
        }

        @media (max-width: 900px) {
          .aura-sidebar {
            width: 300px;
            min-width: 300px;
          }
        }
      `}</style>

      <aside className="aura-sidebar">
        <div className="aura-header">
          <div className="aura-brand">
            <div className="aura-mark">A</div>

            <div>
              <div className="aura-name">AURA</div>
              <div className="aura-tag">
                Research, explained.
              </div>
            </div>
          </div>
        </div>

        <button
          type="button"
          className="aura-new"
          onClick={onNewChat}
        >
          <Plus size={22} strokeWidth={2} />
          <span>New chat</span>
        </button>

        <nav className="aura-nav">
          <button
            type="button"
            className="aura-nav-btn active"
            onClick={onNewChat}
          >
            <Home size={21} strokeWidth={1.8} />
            <span>Home</span>
          </button>

          <button
            type="button"
            className="aura-nav-btn"
          >
            <Library size={21} strokeWidth={1.8} />
            <span>Library</span>
          </button>

          <button
            type="button"
            className="aura-nav-btn"
          >
            <Settings size={21} strokeWidth={1.8} />
            <span>Settings</span>
          </button>
        </nav>

        <div className="aura-scroll">
          <section className="aura-section">
            <div className="aura-section-head">
              <span>Documents</span>
            </div>

            {documents.length > 0 ? (
              <div className="aura-list">
                {documents.map((document) => {
                  const id = document?.id;

                  const active =
                    Number(id) ===
                    Number(selectedDocumentId);

                  return (
                    <div
                      className={
                        active
                          ? "aura-file active"
                          : "aura-file"
                      }
                      key={id}
                    >
                      <button
                        type="button"
                        className="aura-file-select"
                        onClick={() =>
                          onSelectDocument?.(id)
                        }
                        title={
                          active
                            ? "Selected PDF"
                            : "Use this PDF"
                        }
                      >
                        <FileText
                          size={18}
                          strokeWidth={1.8}
                        />

                        <span className="aura-file-name">
                          {document?.filename ||
                            "Untitled PDF"}
                        </span>

                        {active && (
                          <span className="aura-file-check">
                            ✓
                          </span>
                        )}
                      </button>

                      <button
                        type="button"
                        className="aura-file-delete"
                        title="Delete PDF"
                        onClick={(event) => {
                          event.stopPropagation();
                          onDeleteDocument?.(id);
                        }}
                      >
                        <Trash2
                          size={15}
                          strokeWidth={1.8}
                        />
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : files.length > 0 ? (
              <div className="aura-list">
                {files.map((file, index) => (
                  <div
                    className="aura-file"
                    key={`${file}-${index}`}
                  >
                    <FileText
                      size={18}
                      strokeWidth={1.8}
                    />

                    <span className="aura-file-name">
                      {file}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="aura-empty">
                No documents uploaded yet.
              </div>
            )}
          </section>

          <section className="aura-section">
            <div className="aura-section-head">
              <span>Recent</span>

              {chats.length > 0 && (
                <button
                  type="button"
                  className="aura-more"
                  title="Delete all conversations"
                  onClick={handleDeleteAll}
                >
                  <MoreHorizontal size={18} />
                </button>
              )}
            </div>

            <div className="aura-list">
              {chats.length > 0 ? (
                chats.map((chat) => {
                  const id = chat?.id;

                  const active =
                    Number(id) ===
                    Number(currentConversationId);

                  return (
                    <div
                      className={
                        active
                          ? "aura-chat active"
                          : "aura-chat"
                      }
                      key={id}
                      role="button"
                      tabIndex={0}
                      onClick={() =>
                        onSelectConversation?.(id)
                      }
                      onKeyDown={(event) => {
                        if (
                          event.key === "Enter" ||
                          event.key === " "
                        ) {
                          event.preventDefault();
                          onSelectConversation?.(id);
                        }
                      }}
                    >
                      <div className="aura-chat-icon">
                        <MessageSquare
                          size={18}
                          strokeWidth={1.8}
                        />
                      </div>

                      <div className="aura-chat-body">
                        <div className="aura-chat-title">
                          {getTitle(chat)}
                        </div>

                        <div className="aura-chat-date">
                          {formatDate(
                            chat?.updated_at ||
                              chat?.created_at
                          )}
                        </div>
                      </div>

                      <button
                        type="button"
                        className="aura-chat-delete"
                        title="Delete conversation"
                        onClick={(event) => {
                          event.stopPropagation();
                          onDeleteChat?.(id);
                        }}
                      >
                        <Trash2
                          size={16}
                          strokeWidth={1.8}
                        />
                      </button>
                    </div>
                  );
                })
              ) : (
                <div className="aura-empty">
                  Your conversations will appear here.
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="aura-footer">
          {profileOpen && (
            <div className="aura-profile-menu">
              <button
                type="button"
                className="aura-logout-btn"
                onClick={() => {
                  setProfileOpen(false);
                  onLogout?.();
                }}
              >
                Log out
              </button>
            </div>
          )}

          <button
            type="button"
            className="aura-profile"
            onClick={() => setProfileOpen((previous) => !previous)}
            aria-expanded={profileOpen}
            title="Account"
          >
            <div className="aura-avatar">D</div>

            <div className="aura-profile-info">
              <div className="aura-profile-name">
                Deekshitha
              </div>

              <div className="aura-profile-type">
                Personal
              </div>
            </div>
          </button>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
