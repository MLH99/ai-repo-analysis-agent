const apiKeyInput = document.getElementById("apiKey");
const gitUrlInput = document.getElementById("gitUrl");
const branchInput = document.getElementById("branch");
const modelInput = document.getElementById("model");
const questionInput = document.getElementById("question");
const indexBtn = document.getElementById("indexBtn");
const askBtn = document.getElementById("askBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const indexSteps = document.getElementById("indexSteps");
const askSteps = document.getElementById("askSteps");
const indexStatus = document.getElementById("indexStatus");
const chatMessages = document.getElementById("chatMessages");

let indexed = false;
let busy = false;
let conversationHistory = [];

function setStepState(container, step, status) {
  const item = container.querySelector(`[data-step="${step}"]`);
  if (!item) return;

  item.classList.remove("active", "done");
  if (status === "running") item.classList.add("active");
  if (status === "done") item.classList.add("done");
}

function resetSteps(container) {
  container.querySelectorAll("li").forEach((item) => {
    item.classList.remove("active", "done");
  });
}

function setBusy(isBusy) {
  busy = isBusy;
  indexBtn.disabled = isBusy;
  askBtn.disabled = isBusy || !indexed;
}

function getApiKey() {
  return apiKeyInput.value.trim();
}

function getGitUrl() {
  return gitUrlInput.value.trim();
}

function renderChatMessages() {
  chatMessages.innerHTML = "";

  if (conversationHistory.length === 0) {
    chatMessages.innerHTML =
      '<p class="chat-empty">Ask a question about the indexed repository. Follow-up questions are supported.</p>';
    return;
  }

  for (const message of conversationHistory) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${message.role}`;
    bubble.textContent = message.content;
    chatMessages.appendChild(bubble);
  }

  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(role, content, extraClass = "") {
  conversationHistory.push({ role, content });
  renderChatMessages();

  if (extraClass) {
    const lastBubble = chatMessages.lastElementChild;
    if (lastBubble) lastBubble.classList.add(extraClass);
  }
}

function updateLastAssistantMessage(content, extraClass = "") {
  const last = conversationHistory[conversationHistory.length - 1];
  if (!last || last.role !== "assistant") return;

  last.content = content;
  renderChatMessages();

  if (extraClass) {
    const lastBubble = chatMessages.lastElementChild;
    if (lastBubble) lastBubble.classList.add(extraClass);
  }
}

function clearChat() {
  conversationHistory = [];
  renderChatMessages();
  askSteps.classList.add("hidden");
  resetSteps(askSteps);
}

async function consumeEventStream(response, onProgress) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;

      const payload = JSON.parse(line.slice(5).trim());
      const result = onProgress(payload);
      if (result === "stop") return payload;
    }
  }

  return null;
}

async function indexRepository() {
  const gitUrl = getGitUrl();
  const apiKey = getApiKey();

  if (!apiKey) {
    indexStatus.textContent = "Please enter your OpenAI API key.";
    indexStatus.className = "status-text error";
    return;
  }

  if (!gitUrl) {
    indexStatus.textContent = "Please enter a Git repository URL.";
    indexStatus.className = "status-text error";
    return;
  }

  setBusy(true);
  indexed = false;
  clearChat();
  resetSteps(indexSteps);
  indexStatus.textContent = "Starting indexing...";
  indexStatus.className = "status-text";

  const payload = {
    git_url: gitUrl,
    branch: branchInput.value.trim() || null,
    repo_path: "repo",
    openai_api_key: apiKey,
  };

  try {
    const response = await fetch("/index/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Indexing failed");
    }

    const finalEvent = await consumeEventStream(response, (event) => {
      if (event.type === "error") {
        throw new Error(event.message);
      }

      if (event.type === "complete") {
        return "stop";
      }

      setStepState(indexSteps, event.step, event.status);
      indexStatus.textContent = event.message;
      return null;
    });

    if (finalEvent?.type === "complete") {
      indexed = true;
      const result = finalEvent.result;
      indexStatus.textContent = `Indexed ${result.files_indexed} files (${result.chunks_created} chunks). Ready to chat.`;
      indexStatus.className = "status-text success";
    }
  } catch (error) {
    indexStatus.textContent = error.message;
    indexStatus.className = "status-text error";
  } finally {
    setBusy(false);
    askBtn.disabled = !indexed;
  }
}

async function askAgent() {
  const question = questionInput.value.trim();
  const apiKey = getApiKey();

  if (!apiKey) {
    appendMessage("assistant", "Please enter your OpenAI API key.", "error");
    return;
  }

  if (!question) {
    return;
  }

  if (!indexed) {
    appendMessage("assistant", "Index the repository first.", "error");
    return;
  }

  const historyForRequest = conversationHistory.map((message) => ({
    role: message.role,
    content: message.content,
  }));

  appendMessage("user", question);
  questionInput.value = "";

  setBusy(true);
  resetSteps(askSteps);
  askSteps.classList.remove("hidden");
  appendMessage("assistant", "Working...", "loading");

  const payload = {
    question,
    history: historyForRequest,
    repo_path: "repo",
    model: modelInput.value.trim() || "gpt-4o-mini",
    mode: "graph",
    openai_api_key: apiKey,
  };

  try {
    const response = await fetch("/ask/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Request failed");
    }

    const finalEvent = await consumeEventStream(response, (event) => {
      if (event.type === "error") {
        throw new Error(event.message);
      }

      if (event.type === "complete") {
        return "stop";
      }

      setStepState(askSteps, event.step, event.status);
      return null;
    });

    if (finalEvent?.type === "complete") {
      updateLastAssistantMessage(finalEvent.result.answer);
    }
  } catch (error) {
    updateLastAssistantMessage(error.message, "error");
  } finally {
    setBusy(false);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

indexBtn.addEventListener("click", indexRepository);
askBtn.addEventListener("click", askAgent);
clearChatBtn.addEventListener("click", clearChat);

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (!busy && indexed) {
      askAgent();
    }
  }
});

fetch("/health")
  .then((response) => response.json())
  .then((health) => {
    if (health.index_exists) {
      indexed = true;
      askBtn.disabled = false;
      indexStatus.textContent = "Existing index detected. You can chat or re-index.";
      indexStatus.className = "status-text success";
    }
  })
  .catch(() => {
    indexStatus.textContent = "API unavailable. Start the server first.";
    indexStatus.className = "status-text error";
  });

renderChatMessages();
