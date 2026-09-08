const API_BASE_URL = "http://127.0.0.1:8000";

// ================================================================
// TOKEN
// ================================================================

function getToken() {
  return localStorage.getItem("aura_token");
}

// ================================================================
// AUTH HEADER
// ================================================================

function getAuthHeaders() {
  const token = getToken();

  if (!token) {
    throw new Error("You are not logged in.");
  }

  return {
    Authorization: `Bearer ${token}`
  };
}

// ================================================================
// HANDLE JSON RESPONSE
// ================================================================

async function getResponseData(response) {
  let data = {};

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(
      data.detail ||
        data.message ||
        data.error ||
        `Request failed with status ${response.status}.`
    );
  }

  return data;
}

// ================================================================
// REGISTER
// ================================================================

export async function registerUser(
  username,
  email,
  password
) {
  const response = await fetch(
    `${API_BASE_URL}/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        username,
        email,
        password
      })
    }
  );

  return await getResponseData(response);
}

// ================================================================
// LOGIN
// ================================================================

export async function loginUser(
  email,
  password
) {
  const response = await fetch(
    `${API_BASE_URL}/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email,
        password
      })
    }
  );

  return await getResponseData(response);
}

// ================================================================
// ASK AURA
// ================================================================

export async function askAURA(
  question,
  conversationId = null,
  documentId = null
) {
  const response = await fetch(
    `${API_BASE_URL}/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        question,
        conversation_id: conversationId,
        document_id: documentId
      })
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// CHAT HISTORY
// ================================================================

export async function getChatHistory() {
  const response = await fetch(
    `${API_BASE_URL}/history`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// GET DOCUMENTS
// ================================================================

export async function getDocuments() {
  const response = await fetch(
    `${API_BASE_URL}/documents`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// UPLOAD PDF
// ================================================================

export async function uploadPDF(file) {
  if (!file) {
    throw new Error("Please select a PDF file.");
  }

  const formData = new FormData();

  formData.append("pdf", file);

  const response = await fetch(
    `${API_BASE_URL}/upload-pdf`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders()
      },
      body: formData
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// DELETE PDF
// ================================================================

export async function deletePDF(documentId) {
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// DELETE ONE CHAT
// ================================================================

export async function deleteChat(chatId) {
  const response = await fetch(
    `${API_BASE_URL}/history/${chatId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// DELETE ALL CHAT HISTORY
// ================================================================

export async function deleteAllChats() {
  const response = await fetch(
    `${API_BASE_URL}/history`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// IMAGE ANALYSIS
// ================================================================

export async function askImage(
  question,
  image,
  conversationId = null
) {
  if (!image) {
    throw new Error("Please select an image.");
  }

  const formData = new FormData();

  formData.append(
    "question",
    question || "Describe and analyze this image."
  );

  formData.append(
    "image",
    image
  );

  if (
    conversationId !== null &&
    conversationId !== undefined
  ) {
    formData.append(
      "conversation_id",
      String(conversationId)
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/ask-image`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders()
      },
      body: formData
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// CONVERSATIONS
// ================================================================

export async function createConversation(
  title = "New conversation"
) {
  const response = await fetch(
    `${API_BASE_URL}/conversations`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        title
      })
    }
  );

  return await getResponseData(response);
}

// ================================================================
// GET ALL CONVERSATIONS
// ================================================================

export async function getConversations() {
  const response = await fetch(
    `${API_BASE_URL}/conversations`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  return await getResponseData(response);
}

// ================================================================
// GET ONE CONVERSATION
// ================================================================

export async function getConversation(
  conversationId
) {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  return await getResponseData(response);
}

// ================================================================
// DELETE ONE CONVERSATION
// ================================================================

export async function deleteConversation(
  conversationId
) {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  return await getResponseData(response);
}

// ================================================================
// DELETE ALL CONVERSATIONS
// ================================================================

export async function deleteAllConversations() {
  const response = await fetch(
    `${API_BASE_URL}/conversations`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders()
      }
    }
  );

  return await getResponseData(response);
}

// ================================================================
// PDF SUMMARY
// ================================================================

export async function summarizePDF(file) {
  if (!file) {
    throw new Error("Please select a PDF file.");
  }

  const formData = new FormData();

  formData.append(
    "pdf",
    file
  );

  const response = await fetch(
    `${API_BASE_URL}/summarize-pdf`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders()
      },
      body: formData
    }
  );

  return await getResponseData(response);
}

// ================================================================
// PDF QUIZ
// ================================================================

export async function generateQuiz(
  file,
  numberOfQuestions = 5
) {
  if (!file) {
    throw new Error("Please select a PDF file.");
  }

  const formData = new FormData();

  formData.append(
    "pdf",
    file
  );

  formData.append(
    "number_of_questions",
    numberOfQuestions
  );

  const response = await fetch(
    `${API_BASE_URL}/generate-quiz`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders()
      },
      body: formData
    }
  );

  return await getResponseData(response);
}

// ================================================================
// SPEECH TO TEXT
// ================================================================

export async function transcribeAudio(
  audioFile
) {
  if (!audioFile) {
    throw new Error("No audio file selected.");
  }

  const formData = new FormData();

  formData.append(
    "audio",
    audioFile
  );

  const response = await fetch(
    `${API_BASE_URL}/transcribe`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders()
      },
      body: formData
    }
  );

  return await getResponseData(response);
}

// ================================================================
// VOICE ASK
// ================================================================

export async function voiceAsk(
  audioFile,
  conversationId = null
) {
  if (!audioFile) {
    throw new Error("No audio file selected.");
  }

  const formData = new FormData();

  formData.append(
    "audio",
    audioFile
  );

  if (
    conversationId !== null &&
    conversationId !== undefined
  ) {
    formData.append(
      "conversation_id",
      String(conversationId)
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/voice-ask`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders()
      },
      body: formData
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  return await getResponseData(response);
}

// ================================================================
// TEXT TO SPEECH
// ================================================================

export async function speakText(text) {
  if (!text || !text.trim()) {
    throw new Error("Text cannot be empty.");
  }

  const response = await fetch(
    `${API_BASE_URL}/speak`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        text
      })
    }
  );

  if (response.status === 401) {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  if (!response.ok) {
    let message =
      "Text-to-speech failed.";

    try {
      const data =
        await response.json();

      message =
        data.detail ||
        data.message ||
        message;
    } catch {
      // Ignore JSON parsing failure.
    }

    throw new Error(message);
  }

  return await response.blob();
}