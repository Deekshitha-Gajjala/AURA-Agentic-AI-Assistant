import {
  useEffect,
  useRef,
  useState
} from "react";

import Sidebar from "./components/Sidebar";
import FeatureCards from "./components/FeatureCards";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import AuthPage from "./components/AuthPage";

import {
  askAURA,
  getChatHistory,
  getDocuments,
  uploadPDF,
  getConversations,
  getConversation,
  deleteConversation,
  deleteChat,
  deleteAllConversations,
  deletePDF,
  askImage,
  voiceAsk
} from "./services/api";


const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


function App() {

  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [isAuthenticated, setIsAuthenticated] =
    useState(
      Boolean(
        localStorage.getItem("aura_token")
      )
    );


  // ============================================================
  // CHAT
  // ============================================================

  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  // ============================================================
  // THEME
  // ============================================================

  const [darkMode, setDarkMode] =
    useState(
      localStorage.getItem("aura_theme") === "dark"
    );

  useEffect(() => {
    localStorage.setItem(
      "aura_theme",
      darkMode ? "dark" : "light"
    );
  }, [darkMode]);


  // ============================================================
  // CONVERSATIONS
  // ============================================================

  const [conversations, setConversations] =
    useState([]);

  const [currentConversationId, setCurrentConversationId] =
    useState(null);

  const [loadingConversation, setLoadingConversation] =
    useState(false);


  // ============================================================
  // UPLOADED FILES
  // ============================================================

  const [uploadedFiles, setUploadedFiles] =
    useState([]);

  const [uploadedDocuments, setUploadedDocuments] =
    useState([]);

  const [selectedDocumentId, setSelectedDocumentId] =
    useState(null);

  const [selectedDocumentName, setSelectedDocumentName] =
    useState("");


  // ============================================================
  // PENDING IMAGE ATTACHMENT
  // ============================================================

  const [pendingImage, setPendingImage] =
    useState(null);

  const [pendingImagePreview, setPendingImagePreview] =
    useState("");


  // ============================================================
  // VOICE
  // ============================================================

  const [isRecording, setIsRecording] =
    useState(false);

  const [voiceStatus, setVoiceStatus] =
    useState("");

  const mediaRecorderRef =
    useRef(null);

  const audioChunksRef =
    useRef([]);

  const streamRef =
    useRef(null);


  // ============================================================
  // CHAT SCROLL
  // ============================================================

  const chatEndRef =
    useRef(null);


  // ============================================================
  // AUTO-SCROLL CHAT
  // ============================================================

  useEffect(() => {

    const frame =
      requestAnimationFrame(() => {

        chatEndRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "end"
        });

      });

    return () =>
      cancelAnimationFrame(frame);

  }, [
    messages,
    loading,
    voiceStatus
  ]);


  // ============================================================
  // LOAD DATA AFTER LOGIN
  // ============================================================

  useEffect(() => {

    if (!isAuthenticated) {
      return;
    }

    loadConversations();
    loadDocuments();

  }, [isAuthenticated]);


  // ============================================================
  // CLEANUP MICROPHONE
  // ============================================================

  useEffect(() => {

    return () => {

      if (mediaRecorderRef.current) {

        try {

          if (
            mediaRecorderRef.current.state !==
            "inactive"
          ) {
            mediaRecorderRef.current.stop();
          }

        } catch (error) {
          console.error(
            "Recorder cleanup error:",
            error
          );
        }

      }


      if (streamRef.current) {

        streamRef.current
          .getTracks()
          .forEach(
            (track) => track.stop()
          );

      }

    };

  }, []);


  // ============================================================
  // CLEANUP IMAGE PREVIEW
  // ============================================================

  useEffect(() => {
    return () => {
      if (pendingImagePreview) {
        URL.revokeObjectURL(pendingImagePreview);
      }
    };
  }, [pendingImagePreview]);


  // ============================================================
  // LOAD CONVERSATIONS
  // ============================================================

  const loadConversations = async () => {

    try {
      let modern = [];
      let history = [];

      try {
        const data = await getConversations();
        modern = Array.isArray(data?.conversations)
          ? data.conversations
          : [];
      } catch (error) {
        console.warn("Conversation endpoint unavailable:", error);
      }

      try {
        const historyData = await getChatHistory();
        history = Array.isArray(historyData?.history)
          ? historyData.history
          : [];
      } catch (error) {
        console.warn("History endpoint unavailable:", error);
      }

      const merged = new Map();

      // New conversation records.
      modern.forEach((conversation) => {
        if (conversation?.id === null || conversation?.id === undefined) return;
        merged.set(String(conversation.id), {
          ...conversation,
          id: conversation.id,
          title: conversation.title || "New conversation"
        });
      });

      // Legacy chat_history records. These are included even when the
      // modern conversation endpoint returns some records, so older chats
      // never disappear from the Recent list.
      history.forEach((item) => {
        const id = item?.conversation_id ?? item?.id;
        if (id === null || id === undefined) return;

        const key = String(id);
        const existing = merged.get(key);
        const question = String(item?.question || "New conversation").trim();
        const legacyTitle = question.length > 60
          ? `${question.slice(0, 60)}...`
          : question;

        if (existing) {
          merged.set(key, {
            ...existing,
            title: existing.title || legacyTitle,
            updated_at: existing.updated_at || item?.created_at,
            created_at: existing.created_at || item?.created_at
          });
        } else {
          merged.set(key, {
            id,
            title: legacyTitle || "New conversation",
            created_at: item?.created_at,
            updated_at: item?.created_at,
            legacy: true
          });
        }
      });

      const loaded = Array.from(merged.values()).sort((a, b) =>
        new Date(b.updated_at || b.created_at || 0) -
        new Date(a.updated_at || a.created_at || 0)
      );

      setConversations(loaded);

    } catch (error) {
      console.error("CONVERSATIONS ERROR:", error);

      if (error.message?.includes("session has expired")) {
        handleLogout();
      }
    }

  };

  // ============================================================
  // OPEN CONVERSATION
  // ============================================================

  const handleOpenConversation = async (conversationId) => {

    if (conversationId === null || conversationId === undefined || loadingConversation) {
      return;
    }

    try {
      setLoadingConversation(true);

      let conversationMessages = [];
      let resolvedConversationId = conversationId;

      try {
        const data = await getConversation(conversationId);
        conversationMessages = Array.isArray(data?.messages)
          ? data.messages
          : [];
      } catch (conversationError) {
        // Older chats may exist only in chat_history.
        const historyData = await getChatHistory();
        const history = Array.isArray(historyData?.history)
          ? historyData.history
          : [];

        const matching = history.filter((item) =>
          String(item?.conversation_id ?? item?.id) === String(conversationId)
        );

        if (!matching.length) {
          throw conversationError;
        }

        conversationMessages = matching;
        resolvedConversationId = matching[0]?.conversation_id ?? matching[0]?.id;
      }

      const loadedMessages = [];

      conversationMessages.forEach((item) => {
        loadedMessages.push({
          id: `user-${item.id}`,
          role: "user",
          content: item.question || ""
        });

        loadedMessages.push({
          id: `assistant-${item.id}`,
          role: "assistant",
          content: item.answer || ""
        });
      });

      setCurrentConversationId(resolvedConversationId);
      setMessages(loadedMessages);
      setInput("");
      setPendingImage(null);
      setPendingImagePreview("");

    } catch (error) {
      console.error("OPEN CONVERSATION ERROR:", error);

      if (error.message?.includes("session has expired")) {
        handleLogout();
        return;
      }

      setMessages([{
        id: `conversation-error-${Date.now()}`,
        role: "assistant",
        content: "I couldn't open this conversation. Please try again."
      }]);
    } finally {
      setLoadingConversation(false);
    }
  };

  // ============================================================
  // LOAD DOCUMENTS
  // ============================================================

  const loadDocuments = async () => {

    try {

      const data =
        await getDocuments();

      const documents =
        data.documents || [];

      setUploadedDocuments(
        documents
      );

      setUploadedFiles(
        documents.map(
          (document) =>
            document.filename
        )
      );

      if (selectedDocumentId !== null) {
        const selected = documents.find(
          (document) =>
            Number(document.id) ===
            Number(selectedDocumentId)
        );

        if (selected) {
          setSelectedDocumentName(
            selected.filename
          );
        } else {
          setSelectedDocumentId(null);
          setSelectedDocumentName("");
        }
      }

    } catch (error) {

      console.error(
        "DOCUMENT ERROR:",
        error
      );


      if (
        error.message?.includes(
          "session has expired"
        )
      ) {

        handleLogout();

      }

    }

  };


  // ============================================================
  // DELETE PDF
  // ============================================================

  const handleDeleteDocument = async (documentId) => {

    try {
      await deletePDF(documentId);

      if (Number(selectedDocumentId) === Number(documentId)) {
        setSelectedDocumentId(null);
        setSelectedDocumentName("");
      }

      await loadDocuments();

    } catch (error) {

      console.error("DELETE PDF ERROR:", error);

      if (error.message?.includes("session has expired")) {
        handleLogout();
      }

    }
  };


  // ============================================================
  // SELECT PDF
  // ============================================================

  const handleSelectDocument = (
    documentId
  ) => {
    const selected = uploadedDocuments.find(
      (document) =>
        Number(document.id) ===
        Number(documentId)
    );

    if (!selected) {
      return;
    }

    setSelectedDocumentId(
      selected.id
    );

    setSelectedDocumentName(
      selected.filename
    );

    setInput("");
  };


  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin = () => {

    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      console.error(
        "Login completed but token was not found."
      );

      return;

    }


    setIsAuthenticated(true);
    setMessages([]);
    setInput("");

  };


  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {

    localStorage.removeItem(
      "aura_token"
    );

    localStorage.removeItem(
      "aura_user"
    );


    setIsAuthenticated(false);
    setMessages([]);
    setInput("");
    setUploadedFiles([]);
    setUploadedDocuments([]);
    setSelectedDocumentId(null);
    setSelectedDocumentName("");
    setPendingImage(null);
    setPendingImagePreview("");


    // Stop microphone if active

    if (mediaRecorderRef.current) {

      try {

        if (
          mediaRecorderRef.current.state !==
          "inactive"
        ) {
          mediaRecorderRef.current.stop();
        }

      } catch (error) {
        console.error(
          "Recorder logout error:",
          error
        );
      }

    }


    if (streamRef.current) {

      streamRef.current
        .getTracks()
        .forEach(
          (track) => track.stop()
        );

      streamRef.current = null;

    }


    setIsRecording(false);
    setVoiceStatus("");

  };


  // ============================================================
  // NEW CHAT
  // ============================================================

  const handleNewChat = () => {

    setCurrentConversationId(null);
    setMessages([]);
    setInput("");
    setSelectedDocumentId(null);
    setSelectedDocumentName("");
    setPendingImage(null);
    setPendingImagePreview("");

  };


  // ============================================================
  // DELETE CURRENT CHAT
  // ============================================================

  const handleDeleteChat = async (conversationId = null) => {

    const idToDelete =
      conversationId ?? currentConversationId;

    if (idToDelete === null || idToDelete === undefined) {
      handleNewChat();
      return;
    }

    try {
      await deleteConversation(idToDelete);

      setConversations((previous) =>
        previous.filter(
          (conversation) =>
            Number(conversation.id) !== Number(idToDelete)
        )
      );

      if (
        Number(currentConversationId) === Number(idToDelete)
      ) {
        handleNewChat();
      }

      // Refresh in case the list came from legacy /history data.
      await loadConversations();

    } catch (error) {
      console.error(
        "DELETE CONVERSATION ERROR:",
        error
      );

      if (
        error.message?.includes(
          "session has expired"
        )
      ) {
        handleLogout();
      }
    }
  };

  // ============================================================
  // DELETE ALL CONVERSATIONS
  // ============================================================

  const handleDeleteAllConversations = async () => {

    try {

      await deleteAllConversations();

      setConversations([]);
      handleNewChat();

    } catch (error) {

      console.error(
        "DELETE ALL CONVERSATIONS ERROR:",
        error
      );

      if (
        error.message?.includes(
          "session has expired"
        )
      ) {
        handleLogout();
      }

    }

  };


  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const handleSend = async () => {

    const text = input.trim();

    if (!text || loading) {
      return;
    }

    const token =
      localStorage.getItem("aura_token");

    if (!token) {
      handleLogout();
      return;
    }

    const imageToSend = pendingImage;
    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text
    };

    setMessages((previous) => [
      ...previous,
      userMessage
    ]);

    setInput("");
    setPendingImage(null);
    setPendingImagePreview("");
    setLoading(true);

    try {

      if (imageToSend) {

        const data =
          await askImage(
            text,
            imageToSend.file,
            currentConversationId
          );

        if (data.conversation_id) {
          setCurrentConversationId(
            data.conversation_id
          );
        }

        await loadConversations();

        setMessages((previous) => [
          ...previous,
          {
            id:
              `assistant-${Date.now()}`,
            role:
              "assistant",
            content:
              data.answer ||
              "AURA could not generate an image analysis."
          }
        ]);

      } else {

        const data =
          await askAURA(
            text,
            currentConversationId,
            selectedDocumentId
          );

        if (data.conversation_id) {
          setCurrentConversationId(
            data.conversation_id
          );
        }

        await loadConversations();

        setMessages((previous) => [
          ...previous,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content:
              data.answer ||
              "AURA did not return an answer."
          }
        ]);

      }

    } catch (error) {

      console.error("AURA ERROR:", error);

      if (
        error.message?.includes("session has expired")
      ) {
        handleLogout();
        return;
      }

      setMessages((previous) => [
        ...previous,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            error.message ||
            "Sorry, something went wrong."
        }
      ]);

    } finally {
      setLoading(false);
    }

  };


  // ============================================================
  // FEATURE CARDS
  // ============================================================

  const handleFeatureSelect = (
    feature
  ) => {

    const prompts = {

      web:
        "Search the web for the latest information",

      youtube:
        "Find relevant YouTube videos",

      pdf:
        "I want to ask questions about my PDFs",

      sql:
        "I want to query my data",

      ocr:
        "I want to analyze an image"

    };


    setInput(
      prompts[feature] || ""
    );

  };


  // ============================================================
  // FILE UPLOAD
  // ============================================================

  const handleFileUpload = async (
    file,
    isImage = false
  ) => {

    if (!file) {
      return;
    }


    // ==========================================================
    // IMAGE - OCR + VISION
    // ==========================================================

    if (isImage) {

      const token =
        localStorage.getItem("aura_token");

      if (!token) {
        handleLogout();
        return;
      }

      if (!file.type.startsWith("image/")) {
        return;
      }

      if (file.size > 15 * 1024 * 1024) {
        setMessages((previous) => [
          ...previous,
          {
            id: `image-error-${Date.now()}`,
            role: "assistant",
            content: "Please select an image smaller than 15 MB."
          }
        ]);
        return;
      }

      if (pendingImagePreview) {
        URL.revokeObjectURL(pendingImagePreview);
      }

      const previewUrl = URL.createObjectURL(file);

      setPendingImage({
        file,
        name: file.name
      });
      setPendingImagePreview(previewUrl);

      return;

    }


    // ==========================================================

    // ==========================================================

    if (
      file.type !==
      "application/pdf"
    ) {

      setMessages(
        (previous) => [
          ...previous,

          {

            id:
              `pdf-error-${Date.now()}`,

            role:
              "assistant",

            content:
              "Please select a PDF file."

          }

        ]
      );


      return;

    }


    // ==========================================================
    // AUTH CHECK
    // ==========================================================

    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      handleLogout();

      return;

    }


    // ==========================================================
    // SHOW UPLOADING
    // ==========================================================

    setMessages(
      (previous) => [
        ...previous,

        {

          id:
            `upload-${Date.now()}`,

          role:
            "user",

          content:
            `Uploading ${file.name}...`

        }

      ]
    );


    setLoading(true);


    try {

      const data =
        await uploadPDF(file);


      console.log(
        "PDF RESPONSE:",
        data
      );


      if (
        data.document_id !== undefined &&
        data.document_id !== null
      ) {
        setSelectedDocumentId(
          data.document_id
        );

        setSelectedDocumentName(
          data.filename || file.name
        );
      }

      await loadDocuments();


      setMessages(
        (previous) => [
          ...previous,
          {
            id:
              `pdf-success-${Date.now()}`,
            role:
              "assistant",
            content:
              `${file.name} is ready and selected. Type your question below and press Send.`
          }
        ]
      );


    } catch (error) {

      console.error(
        "PDF ERROR:",
        error
      );


      if (
        error.message?.includes(
          "session has expired"
        )
      ) {

        handleLogout();

        return;

      }


      setMessages(
        (previous) => [
          ...previous,

          {

            id:
              `pdf-error-${Date.now()}`,

            role:
              "assistant",

            content:
              `PDF upload failed.\n\n${error.message}`

          }

        ]
      );


    } finally {

      setLoading(false);

    }

  };


  // ============================================================
  // REMOVE PENDING IMAGE
  // ============================================================

  const removePendingImage = () => {
    if (pendingImagePreview) {
      URL.revokeObjectURL(pendingImagePreview);
    }

    setPendingImage(null);
    setPendingImagePreview("");
  };


  // ============================================================
  // VOICE - GET AUTH TOKEN
  // ============================================================

  const getVoiceToken = () => {

    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      handleLogout();

      throw new Error(
        "Your session has expired. Please log in again."
      );

    }


    return token;

  };


  // ============================================================
  // VOICE - TEXT TO SPEECH
  // ============================================================

  const speakAnswer = async (
    answer
  ) => {

    if (!answer) {
      return;
    }


    const token =
      getVoiceToken();


    try {

      setVoiceStatus(
        "Generating voice response..."
      );


      const response =
        await fetch(
          `${API_BASE_URL}/speak`,
          {

            method:
              "POST",

            headers: {

              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`

            },

            body:
              JSON.stringify({
                text: answer
              })

          }
        );


      if (!response.ok) {

        const errorText =
          await response.text();

        throw new Error(
          errorText ||
          `Voice response failed (${response.status})`
        );

      }


      const contentType =
        response.headers.get(
          "content-type"
        );


      if (
        !contentType ||
        !contentType.includes(
          "audio"
        )
      ) {

        throw new Error(
          "AURA returned an invalid audio response."
        );

      }


      const audioBlob =
        await response.blob();


      if (
        !audioBlob ||
        audioBlob.size === 0
      ) {

        throw new Error(
          "AURA returned an empty audio response."
        );

      }


      const audioUrl =
        URL.createObjectURL(
          audioBlob
        );


      const audio =
        new Audio(audioUrl);


      audio.onended = () => {

        URL.revokeObjectURL(
          audioUrl
        );

        setVoiceStatus("");

      };


      audio.onerror = () => {

        URL.revokeObjectURL(
          audioUrl
        );

        setVoiceStatus("");

        console.error(
          "Audio playback failed."
        );

      };


      await audio.play();


      setVoiceStatus(
        "Playing AURA's response..."
      );


    } catch (error) {

      console.error(
        "TEXT TO SPEECH ERROR:",
        error
      );


      setVoiceStatus(
        `Voice playback failed: ${error.message}`
      );

    }

  };


  // ============================================================
  // VOICE - SEND RECORDED AUDIO TO BACKEND
  // ============================================================

  const processVoiceRecording = async (
    audioBlob
  ) => {

    if (
      !audioBlob ||
      audioBlob.size === 0
    ) {

      throw new Error(
        "No audio was recorded."
      );

    }


    const token =
      getVoiceToken();


    setLoading(true);


    setVoiceStatus(
      "Understanding your voice..."
    );


    try {

      // A Blob has no useful filename/extension when appended to FormData.
      // The backend validates the audio extension, so convert it to a File.
      const blobType =
        audioBlob.type ||
        "audio/webm";

      let extension = "webm";

      if (blobType.includes("ogg")) {
        extension = "ogg";
      } else if (blobType.includes("mp4") || blobType.includes("m4a")) {
        extension = "m4a";
      } else if (blobType.includes("mpeg") || blobType.includes("mp3")) {
        extension = "mp3";
      }

      const audioFile =
        new File(
          [audioBlob],
          `aura-recording.${extension}`,
          { type: blobType }
        );

      const data =
        await voiceAsk(
          audioFile,
          currentConversationId
        );

      if (data.conversation_id) {
        setCurrentConversationId(
          data.conversation_id
        );
      }

      await loadConversations();


      const transcript =
        data.transcript?.trim();


      const answer =
        data.answer?.trim();


      if (!transcript) {

        throw new Error(
          "AURA could not understand the recording."
        );

      }


      // ----------------------------------------------------------
      // ADD TRANSCRIPT TO CHAT
      // ----------------------------------------------------------

      setMessages(
        (previous) => [

          ...previous,

          {

            id:
              `voice-user-${Date.now()}`,

            role:
              "user",

            content:
              transcript

          },

          {

            id:
              `voice-assistant-${Date.now() + 1}`,

            role:
              "assistant",

            content:
              answer ||
              "AURA did not return an answer."

          }

        ]
      );


      setVoiceStatus(
        "Voice response ready."
      );


      // ----------------------------------------------------------
      // SPEAK ANSWER
      // ----------------------------------------------------------

      if (answer) {

        await speakAnswer(
          answer
        );

      }


    } finally {

      setLoading(false);

    }

  };


  // ============================================================
  // VOICE - START RECORDING
  // ============================================================

  const startRecording = async () => {

    if (
      isRecording ||
      loading
    ) {
      return;
    }


    if (
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia
    ) {

      setVoiceStatus(
        "Your browser does not support microphone recording."
      );

      return;

    }


    try {

      getVoiceToken();


      setVoiceStatus(
        "Requesting microphone access..."
      );


      const stream =
        await navigator.mediaDevices
          .getUserMedia({
            audio: true
          });


      streamRef.current =
        stream;


      audioChunksRef.current =
        [];


      let mimeType =
        "audio/webm";


      if (
        MediaRecorder.isTypeSupported(
          "audio/webm;codecs=opus"
        )
      ) {

        mimeType =
          "audio/webm;codecs=opus";

      } else if (
        MediaRecorder.isTypeSupported(
          "audio/webm"
        )
      ) {

        mimeType =
          "audio/webm";

      } else if (
        MediaRecorder.isTypeSupported(
          "audio/ogg;codecs=opus"
        )
      ) {

        mimeType =
          "audio/ogg;codecs=opus";

      } else {

        mimeType =
          "";

      }


      const recorder =
        mimeType
          ? new MediaRecorder(
              stream,
              {
                mimeType
              }
            )
          : new MediaRecorder(
              stream
            );


      mediaRecorderRef.current =
        recorder;


      recorder.ondataavailable =
        (event) => {

          if (
            event.data &&
            event.data.size > 0
          ) {

            audioChunksRef.current.push(
              event.data
            );

          }

        };


      recorder.onerror =
        (event) => {

          console.error(
            "MEDIA RECORDER ERROR:",
            event
          );

          setVoiceStatus(
            "Microphone recording failed."
          );

        };


      recorder.onstop =
        async () => {

          try {

            const actualMimeType =
              recorder.mimeType ||
              mimeType ||
              "audio/webm";


            const audioBlob =
              new Blob(
                audioChunksRef.current,
                {
                  type:
                    actualMimeType
                }
              );


            audioChunksRef.current =
              [];


            if (streamRef.current) {

              streamRef.current
                .getTracks()
                .forEach(
                  (track) =>
                    track.stop()
                );

              streamRef.current =
                null;

            }


            mediaRecorderRef.current =
              null;


            await processVoiceRecording(
              audioBlob
            );


          } catch (error) {

            console.error(
              "VOICE PROCESSING ERROR:",
              error
            );


            setVoiceStatus(
              `Voice input failed: ${error.message}`
            );


            setLoading(false);

          }

        };


      recorder.start();


      setIsRecording(true);

      setVoiceStatus(
        "Listening... click Voice again to stop."
      );


    } catch (error) {

      console.error(
        "MICROPHONE ERROR:",
        error
      );


      if (
        error.name ===
        "NotAllowedError"
      ) {

        setVoiceStatus(
          "Microphone permission was denied. Please allow microphone access in your browser."
        );

      } else if (
        error.name ===
        "NotFoundError"
      ) {

        setVoiceStatus(
          "No microphone was found."
        );

      } else {

        setVoiceStatus(
          `Unable to start microphone: ${error.message}`
        );

      }

    }

  };


  // ============================================================
  // VOICE - STOP RECORDING
  // ============================================================

  const stopRecording = () => {

    const recorder =
      mediaRecorderRef.current;


    if (!recorder) {
      return;
    }


    if (
      recorder.state ===
      "recording"
    ) {

      setIsRecording(false);

      setVoiceStatus(
        "Processing your voice..."
      );


      recorder.stop();

    }

  };


  // ============================================================
  // VOICE BUTTON
  // ============================================================

  const handleVoice = () => {

    if (loading) {
      return;
    }


    if (isRecording) {

      stopRecording();

    } else {

      startRecording();

    }

  };


  // ============================================================
  // LOGIN PAGE
  // ============================================================

  if (!isAuthenticated) {

    return (
      <AuthPage
        onLogin={
          handleLogin
        }
      />
    );

  }


  // ============================================================
  // MAIN APPLICATION
  // ============================================================

  return (

    <div className={darkMode ? "app aura-dark" : "app"}>

      <style>{`
        .chat-area p {
          margin-top: 0;
          margin-bottom: 8px;
        }

        .chat-area ul,
        .chat-area ol {
          margin-top: 5px;
          margin-bottom: 9px;
          padding-left: 24px;
        }

        .chat-area li {
          margin-bottom: 4px;
          line-height: 1.5;
        }

        .chat-area li p {
          margin: 0;
        }

        .chat-area h1,
        .chat-area h2,
        .chat-area h3,
        .chat-area h4 {
          margin-top: 18px;
          margin-bottom: 8px;
          line-height: 1.3;
        }

        .chat-area h1:first-child,
        .chat-area h2:first-child,
        .chat-area h3:first-child,
        .chat-area h4:first-child {
          margin-top: 0;
        }

        .chat-area > * {
          max-width: 100%;
        }

        .aura-selected-document {
          position: absolute;
          left: 50%;
          bottom: 156px;
          transform: translateX(-50%);
          width: min(1050px, calc(100% - 120px));
          box-sizing: border-box;
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 9px 12px;
          border: 1px solid #dedee2;
          border-radius: 10px;
          background: #f7f7f8;
          color: #555963;
          font-size: 13px;
          z-index: 5;
        }

        .aura-selected-document-dot {
          color: #171717;
          font-size: 8px;
          flex: 0 0 auto;
        }

        .aura-selected-document-text {
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .aura-selected-document-text strong {
          color: #202123;
          font-weight: 600;
        }

        .aura-clear-document {
          margin-left: auto;
          flex: 0 0 auto;
          width: 24px;
          height: 24px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: #777b84;
          font-size: 20px;
          line-height: 1;
          cursor: pointer;
        }

        .aura-clear-document:hover {
          background: #e9e9eb;
          color: #202123;
        }

        .aura-dark {
          background: #111315;
          color: #eceff1;
        }

        .aura-dark .main-area,
        .aura-dark .chat-area,
        .aura-dark .top-bar {
          background: #111315;
          color: #eceff1;
        }

        .aura-dark .theme-button {
          color: #f1f3f4;
          background: #202328;
          border-color: #363a40;
        }

        .aura-dark .aura-selected-document {
          background: #1b1e22;
          border-color: #34383e;
          color: #c7cbd1;
        }

        .aura-dark .aura-selected-document-text strong {
          color: #f1f3f4;
        }

        .aura-dark .aura-clear-document:hover {
          background: #2a2e34;
          color: #fff;
        }

        .aura-dark .chat-area p,
        .aura-dark .chat-area li,
        .aura-dark .chat-area h1,
        .aura-dark .chat-area h2,
        .aura-dark .chat-area h3,
        .aura-dark .chat-area h4 {
          color: #eceff1;
        }

        .aura-dark .chat-input,
        .aura-dark .chat-input-container {
          background: #1a1d21;
          border-color: #373b42;
          color: #f1f3f4;
        }

        .aura-dark .chat-input::placeholder {
          color: #8d939c;
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

        .aura-dark .composer-attachment {
          border-color: #34383e;
        }

        .aura-dark .composer-attachment-preview {
          background: #2a2e34;
          color: #c7cbd1;
        }

        .aura-dark .composer-attachment-info strong {
          color: #f1f3f4;
        }

        .aura-dark .composer-attachment-info span {
          color: #9aa1aa;
        }

        .aura-dark .composer-remove:hover {
          background: #2a2e34;
          color: #fff;
        }

        .aura-dark .attachment-menu {
          background: #22252a;
          border-color: #3a3e45;
          box-shadow: 0 12px 30px rgba(0,0,0,.35);
        }

        .aura-dark .attachment-menu button {
          color: #f1f3f4;
        }

        .aura-dark .attachment-menu button:hover {
          background: #30343a;
        }

        @media (max-width: 900px) {
          .chat-area {
            padding-left: 20px !important;
            padding-right: 20px !important;
          }
        }
      `}</style>


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <Sidebar

        onNewChat={
          handleNewChat
        }

        onDeleteChat={
          handleDeleteChat
        }

        onDeleteAllChats={
          handleDeleteAllConversations
        }

        conversations={
          conversations
        }

        currentConversationId={
          currentConversationId
        }

        onSelectConversation={
          handleOpenConversation
        }

        uploadedFiles={
          uploadedFiles
        }

        uploadedDocuments={
          uploadedDocuments
        }

        selectedDocumentId={
          selectedDocumentId
        }

        onSelectDocument={
          handleSelectDocument
        }

        onDeleteDocument={
          handleDeleteDocument
        }

        darkMode={darkMode}

        onLogout={handleLogout}
      />


      {/* ======================================================
          MAIN AREA
      ====================================================== */}

      <section
        className="main-area"
        style={{
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          height: "100vh",
          overflow: "hidden",
          position: "relative"
        }}
      >


        {/* ====================================================
            TOP BAR
        ==================================================== */}

        <header className="top-bar">

          <div className="top-bar-spacer" />

          <div className="top-bar-actions">

            <button
              type="button"
              className="theme-button"
              title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
              aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
              onClick={() => setDarkMode((previous) => !previous)}
            >
              {darkMode ? "☀" : "◐"}
            </button>

          </div>

        </header>


        {/* ====================================================
            CHAT AREA
        ==================================================== */}

        <div
          className="chat-area"
          style={{
            flex: "1 1 auto",
            minHeight: 0,
            overflowY: "auto",
            overflowX: "hidden",
            paddingBottom: "240px",
            scrollBehavior: "smooth"
          }}
        >

          {messages.length === 0 ? (

            <>

              <div className="welcome-section">

                <div className="welcome-label">
                  AURA
                </div>

                <h1>
                  Good evening, Deekshitha
                </h1>

                <p>
                  What would you like to explore?
                </p>

              </div>


              <FeatureCards
                onFeatureSelect={
                  handleFeatureSelect
                }
              />

            </>

          ) : (

            <ChatWindow
              messages={
                messages
              }
            />

          )}

          <div
            ref={chatEndRef}
            aria-hidden="true"
            style={{
              height: "1px",
              width: "100%"
            }}
          />

        </div>


        {/* ====================================================
            VOICE STATUS
        ==================================================== */}

        {voiceStatus && (

          <div
            className={
              isRecording
                ? "voice-status recording"
                : "voice-status"
            }
          >

            <span>

              {isRecording
                ? "●"
                : "◉"}

            </span>

            {voiceStatus}

          </div>

        )}


        {/* ====================================================
            SELECTED PDF
        ==================================================== */}

        {selectedDocumentId !== null && (
          <div
            className="aura-selected-document"
            title="The next question will be answered using this PDF."
          >
            <span className="aura-selected-document-dot">
              ●
            </span>

            <span className="aura-selected-document-text">
              <strong>Using PDF:</strong>{" "}
              {selectedDocumentName || "Selected document"}
            </span>

            <button
              type="button"
              className="aura-clear-document"
              onClick={() => {
                setSelectedDocumentId(null);
                setSelectedDocumentName("");
              }}
              title="Stop using this PDF"
            >
              ×
            </button>
          </div>
        )}

        {/* ====================================================
            CHAT INPUT
        ==================================================== */}

        <ChatInput

          value={
            input
          }

          onChange={
            setInput
          }

          onSend={
            handleSend
          }

          onVoice={
            handleVoice
          }

          onFileUpload={
            handleFileUpload
          }

          pendingImage={
            pendingImage
          }

          pendingImagePreview={
            pendingImagePreview
          }

          onRemoveImage={
            removePendingImage
          }

          loading={
            loading
          }

        />


      </section>

    </div>

  );

}


export default App;