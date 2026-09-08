import { useRef, useState } from "react";
import {
  Paperclip,
  Image as ImageIcon,
  Mic,
  ArrowUp,
  X
} from "lucide-react";

function ChatInput({
  value,
  onChange,
  onSend,
  onVoice,
  onFileUpload,
  pendingImage,
  pendingImagePreview,
  onRemoveImage,
  loading
}) {
  const pdfInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const textareaRef = useRef(null);
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false);

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  const handlePdfChange = (event) => {
    const file = event.target.files?.[0];
    if (file) onFileUpload(file, false);
    event.target.value = "";
    setAttachmentMenuOpen(false);
  };

  const handleImageChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileUpload(file, true);
      requestAnimationFrame(() => textareaRef.current?.focus());
    }
    event.target.value = "";
    setAttachmentMenuOpen(false);
  };

  return (
    <>
      <style>{`
        .composer-shell {
          position: absolute;
          left: 50%;
          bottom: 18px;
          transform: translateX(-50%);
          width: min(860px, calc(100% - 48px));
          z-index: 30;
        }

        .composer-box {
          background: #ffffff;
          border: 1px solid #d9d9d9;
          border-radius: 22px;
          box-shadow: 0 8px 28px rgba(0,0,0,0.08);
          overflow: visible;
          padding: 10px 12px 9px;
        }

        .composer-attachment {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 7px 8px 11px 4px;
        }

        .composer-attachment-preview {
          width: 58px;
          height: 58px;
          flex: 0 0 58px;
          border-radius: 11px;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f1f1f1;
          color: #666;
        }

        .composer-attachment-preview img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
        }

        .composer-attachment-info {
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .composer-attachment-info strong {
          font-size: 14px;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: #202020;
        }

        .composer-attachment-info span {
          font-size: 13px;
          color: #7a7a7a;
        }

        .composer-remove {
          margin-left: auto;
          width: 34px;
          height: 34px;
          border: 0;
          border-radius: 50%;
          background: transparent;
          color: #666;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .composer-remove:hover {
          background: #f1f1f1;
          color: #111;
        }

        .composer-box textarea {
          width: 100%;
          min-height: 52px;
          max-height: 150px;
          resize: none;
          border: 0;
          outline: 0;
          background: transparent;
          padding: 8px 8px 4px;
          box-sizing: border-box;
          font: inherit;
          font-size: 17px;
          line-height: 1.45;
          color: #222;
        }

        .composer-box textarea::placeholder {
          color: #8b8b8b;
          opacity: 1;
        }

        .composer-toolbar {
          height: 42px;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .composer-toolbar-spacer {
          flex: 1;
        }

        .composer-icon-button {
          width: 40px;
          height: 40px;
          border: 0;
          background: transparent;
          color: #222;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .composer-icon-button:hover:not(:disabled) {
          background: #f2f2f2;
        }

        .composer-plus {
          font-size: 32px;
          font-weight: 300;
          line-height: 1;
          margin-top: -3px;
        }

        .composer-send-button {
          width: 42px;
          height: 42px;
          border: 0;
          border-radius: 50%;
          background: #2f6fd6;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          margin-left: 3px;
        }

        .composer-send-button.inactive {
          background: #dfe2e8;
          color: #9aa0aa;
          cursor: default;
        }

        .attachment-menu {
          position: absolute;
          left: 4px;
          bottom: calc(100% + 8px);
          width: 170px;
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 14px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.12);
          padding: 6px;
          z-index: 40;
        }

        .attachment-menu button {
          width: 100%;
          border: 0;
          background: transparent;
          border-radius: 9px;
          padding: 10px;
          display: flex;
          align-items: center;
          gap: 10px;
          text-align: left;
          color: #222;
          cursor: pointer;
          font-size: 14px;
        }

        .attachment-menu button:hover {
          background: #f3f3f3;
        }

        .composer-hint {
          text-align: center;
          font-size: 12px;
          color: #9aa0aa;
          margin-top: 10px;
        }

        .aura-dark .composer-box {
          background: #1a1d21 !important;
          border-color: #373b42 !important;
          box-shadow: 0 8px 28px rgba(0,0,0,.28);
        }

        .aura-dark .composer-box textarea {
          color: #f1f3f4 !important;
        }

        .aura-dark .composer-box textarea::placeholder {
          color: #8d939c !important;
        }

        .aura-dark .composer-icon-button {
          color: #f1f3f4 !important;
        }

        .aura-dark .composer-icon-button:hover:not(:disabled) {
          background: #2a2e34 !important;
        }

        .aura-dark .composer-remove:hover {
          background: #2a2e34;
          color: #fff;
        }

        .aura-dark .attachment-menu {
          background: #22252a;
          border-color: #3a3e45;
        }

        .aura-dark .attachment-menu button {
          color: #f1f3f4;
        }

        .aura-dark .attachment-menu button:hover {
          background: #30343a;
        }

        @media (max-width: 700px) {
          .composer-shell {
            width: calc(100% - 24px);
            bottom: 10px;
          }

          .composer-attachment-info span {
            display: none;
          }
        }
      `}</style>

      <div className="composer-shell">
      {attachmentMenuOpen && (
        <div className="attachment-menu">
          <button
            type="button"
            onClick={() => pdfInputRef.current?.click()}
          >
            <Paperclip size={17} />
            <span>Attach PDF</span>
          </button>

          <button
            type="button"
            onClick={() => imageInputRef.current?.click()}
          >
            <ImageIcon size={17} />
            <span>Add image</span>
          </button>
        </div>
      )}

      <input
        ref={pdfInputRef}
        type="file"
        accept="application/pdf,.pdf"
        onChange={handlePdfChange}
        style={{ display: "none" }}
      />

      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageChange}
        style={{ display: "none" }}
      />

      <div className="composer-box">
        {pendingImage && (
          <div className="composer-attachment">
            <div className="composer-attachment-preview">
              {pendingImagePreview ? (
                <img
                  src={pendingImagePreview}
                  alt="Selected image"
                />
              ) : (
                <ImageIcon size={22} />
              )}
            </div>

            <div className="composer-attachment-info">
              <strong>{pendingImage.name}</strong>
              <span>Type your question below, then press Send.</span>
            </div>

            <button
              type="button"
              className="composer-remove"
              onClick={onRemoveImage}
              disabled={loading}
              title="Remove image"
            >
              <X size={18} />
            </button>
          </div>
        )}

        <textarea
          ref={textareaRef}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything"
          disabled={loading}
          rows={1}
          aria-label="Ask anything"
        />

        <div className="composer-toolbar">
          <button
            type="button"
            className="composer-icon-button"
            onClick={() => setAttachmentMenuOpen((open) => !open)}
            disabled={loading}
            title="Attach"
            aria-label="Attach"
          >
            <span className="composer-plus">+</span>
          </button>

          <div className="composer-toolbar-spacer" />

          <button
            type="button"
            className={`composer-icon-button voice-button ${loading ? "disabled" : ""}`}
            onClick={onVoice}
            disabled={loading}
            title="Voice input"
            aria-label="Voice input"
          >
            <Mic size={22} strokeWidth={1.9} />
          </button>

          <button
            type="button"
            className={`composer-send-button ${!value.trim() || loading ? "inactive" : ""}`}
            onClick={onSend}
            disabled={!value.trim() || loading}
            title="Send"
            aria-label="Send"
          >
            <ArrowUp size={24} strokeWidth={2.2} />
          </button>
        </div>
      </div>

      <div className="composer-hint">
        AURA can search the web, read documents, analyze images and query your data.
      </div>
      </div>
    </>
  );
}

export default ChatInput;
