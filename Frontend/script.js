document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-upload");
  const fileLabel = document.getElementById("file-upload-label");

  // Highlight drop area when dragging file over it
  ["dragenter", "dragover"].forEach(event => {
    dropZone.addEventListener(event, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("highlight");
    });
  });

  ["dragleave", "drop"].forEach(event => {
    dropZone.addEventListener(event, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove("highlight");
    });
  });

  // Handle dropped files
  dropZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  });

  // Handle file input selection
  fileInput.addEventListener("change", (e) => {
    if (fileInput.files.length > 0) {
      uploadFile(fileInput.files[0]);
    }
  });

  // Upload file function
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        alert("Error: " + error.detail);
        return;
      }

      const result = await response.json();
      alert("✅ " + result.message + "\nSaved as: " + result.saved_as);
      loadDocuments();
    } catch (err) {
      console.error("Upload failed:", err);
      alert("❌ Upload failed, check console for details.");
    }
  }
});

const fileListContainer = document.getElementById("file-list");
// Create the popup menu ONCE when page loads
const fileMenu = document.createElement("div");
fileMenu.className = "file-menu";
fileMenu.style.display = "none"; // hidden by default
fileMenu.innerHTML = `
  <button class="menu-rename">Rename</button>
  <button class="menu-delete">Delete</button>
`;
document.body.appendChild(fileMenu);

// Hide the menu when clicking anywhere else
document.addEventListener("click", (e) => {
  if (!fileMenu.contains(e.target)) {
    fileMenu.style.display = "none";
  }
});

async function loadDocuments() {
  try {
    const res = await fetch(`/documents?ts=${Date.now()}`, { cache: "no-store" });
    const docs = await res.json();

    const fileList = document.getElementById("file-list");
    fileList.innerHTML = ""; // clear old entries

    docs.forEach((doc, index) => {
      const fileItem = document.createElement("div");
      fileItem.classList.add("file-item");
      fileItem.id = `file-item-${index}`;

      fileItem.innerHTML = `
        <div class="file-info">
          <img src="./Resources/Icon/file.svg" alt="File Icon" class="file-icon" />
          <span class="file-name">${doc.source}</span>
        </div>
        <button class="file-setting">
          <img src="./Resources/Icon/dots.svg" alt="Settings" class="settings-icon"/>
        </button>
      `;

      fileList.appendChild(fileItem);

      // 🎯 Attach event listener for the settings button
      const settingsBtn = fileItem.querySelector(".file-setting");
      settingsBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // prevent global click handler

        // Position the menu near the button
        const rect = settingsBtn.getBoundingClientRect();
        fileMenu.style.top = rect.bottom + "px";
        fileMenu.style.left = rect.left + "px";
        fileMenu.style.display = "block";

        // Store which file is selected (could be used later)
        fileMenu.dataset.fileIndex = index;
        fileMenu.dataset.fileName = doc.source;
      });
    });

    console.log("Documents loaded");
  } catch (err) {
    console.error("Failed to load documents:", err);
  }
}




// Initialize
loadDocuments();

document.addEventListener("DOMContentLoaded", () => {
  loadDocuments(); // fetch documents immediately when page is ready
});













const chatHistory = document.getElementById("chatHistory");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const documentSelector = document.getElementById("documentSelector");

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // Render user message
  appendMessage("user", message);
  userInput.value = "";

  let endpoint = "/ask";
  let body = { question: message };

  if (documentSelector.value) {
    endpoint = "/search-doc";
    body = { document_id: parseInt(documentSelector.value), query: message };
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      throw new Error("Server error: " + response.statusText);
    }

    const data = await response.json();
    const reply = data.answer || data.result || JSON.stringify(data);

    appendMessage("assistant", reply);
  } catch (error) {
    appendMessage("assistant", "⚠️ Error: " + error.message);
  }
}

// Add message to history
function appendMessage(sender, text) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  msg.textContent = text;
  chatHistory.appendChild(msg);
  chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll
}

// Send on button click
sendBtn.addEventListener("click", sendMessage);

// Send on Enter key
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});