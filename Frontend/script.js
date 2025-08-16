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

// List of selected documents
let selectedDocuments = [];

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

      // Click on file item selects/deselects it
      fileItem.addEventListener("click", () => {
        const fileName = doc.source;

        // Toggle selection class
        fileItem.classList.toggle("selected");

        // Add/remove from selectedDocuments array
        if (selectedDocuments.includes(fileName)) {
          selectedDocuments = selectedDocuments.filter(name => name !== fileName);
        } else {
          selectedDocuments.push(fileName);
        }

        console.log("Selected documents:", selectedDocuments);
      });

      // Settings button click (existing)
      const settingsBtn = fileItem.querySelector(".file-setting");
      settingsBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // prevent file-item click
        const rect = settingsBtn.getBoundingClientRect();
        fileMenu.style.top = rect.bottom + "px";
        fileMenu.style.left = rect.left + "px";
        fileMenu.style.display = "block";

        fileMenu.dataset.fileIndex = index;
        fileMenu.dataset.fileName = doc.source;
      });
    });

    console.log("Documents loaded");
  } catch (err) {
    console.error("Failed to load documents:", err);
  }
}


// Attach handler to the Rename button
fileMenu.querySelector(".menu-rename").addEventListener("click", async () => {
  const oldName = fileMenu.dataset.fileName;
  oldName_no_ext = oldName.split('.').slice(0, -1).join('.');
  const ext = oldName.split('.').pop();
  const newName = prompt("Enter new name for the file:", oldName_no_ext);
  newName = newName + '.' + ext;

  if (!newName || newName === oldName) {
    fileMenu.style.display = "none"; // just hide menu
    return;
  }

  try {
    const formData = new FormData();
    formData.append("document_name", oldName);
    formData.append("new_name", newName);

    const res = await fetch("/document/rename", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Rename failed");
    }

    const data = await res.json();
    console.log("Renamed:", data);

    fileMenu.style.display = "none";

    // Refresh the document list so the new name appears
    loadDocuments();

  } catch (err) {
    alert("Error renaming file: " + err.message);
    console.error(err);
    fileMenu.style.display = "none";
  }
});

// Attach handler to the Delete button
fileMenu.querySelector(".menu-delete").addEventListener("click", async () => {
  const fileName = fileMenu.dataset.fileName;

  const confirmed = confirm(`Are you sure you want to delete "${fileName}"?`);
  if (!confirmed) {
    fileMenu.style.display = "none"; // hide menu if cancelled
    return;
  }

  try {
    const formData = new FormData();
    formData.append("document_name", fileName);

    const res = await fetch("/document/delete", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Delete failed");
    }

    const data = await res.json();
    console.log("Deleted:", data);

    fileMenu.style.display = "none";

    // Refresh the document list so the deleted file disappears
    loadDocuments();

  } catch (err) {
    alert("Error deleting file: " + err.message);
    console.error(err);
    fileMenu.style.display = "none";
  }
});


document.getElementById("question-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const textarea = document.getElementById("question");
  const question = textarea.value.trim();
  if (!question) return;

  const container = document.getElementById("message-container");
  const submitButton = document.querySelector("#question-form button");

  // 1️⃣ Disable button
  submitButton.disabled = true;
  submitButton.style.opacity = "0.6"; 

  // 2️⃣ Add user message immediately
  const userMsg = document.createElement("div");
  userMsg.classList.add("message", "user");
  userMsg.textContent = question;
  container.appendChild(userMsg);
  container.scrollTop = container.scrollHeight;

  textarea.value = ""; // clear input

  // 3️⃣ Add temporary bot typing message
  const botMsg = document.createElement("div");
  botMsg.classList.add("message", "bot");
  botMsg.textContent = "Typing...";
  container.appendChild(botMsg);
  container.scrollTop = container.scrollHeight;

  try {
    let res;
    if (selectedDocuments.length > 0) {
      // Send to /search-doc with FormData
      const formData = new FormData();
      selectedDocuments.forEach(doc => formData.append("document_names", doc));
      formData.append("query", question);

      console.log("Sending to /search-doc with FormData: ", formData);

      res = await fetch("/search-doc", {
        method: "POST",
        body: formData
      });
    } else {
      // Send to /ask as before
      res = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(question)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to process question");
    }

    const data = await res.json();

    // 4️⃣ Replace typing with actual answer
    botMsg.textContent = "";
    let i = 0;
    const answer = data.answer;
    const typingInterval = setInterval(() => {
      if (i < answer.length) {
        botMsg.textContent += answer[i];
        i++;
        container.scrollTop = container.scrollHeight;
      } else {
        clearInterval(typingInterval);
      }
    }, 20);

    // 5️⃣ Refresh history
    await loadHistory();

  } catch (err) {
    botMsg.textContent = "Error: " + err.message;
    console.error(err);
  } finally {
    // 6️⃣ Re-enable button
    submitButton.disabled = false;
    submitButton.style.opacity = "1";
  }
});


async function loadHistory() {
  try {
    const res = await fetch(`/history?ts=${Date.now()}`, { cache: "no-store" });
    const history = await res.json();

    const container = document.getElementById("message-container");
    container.innerHTML = ""; // Clear previous messages

    // Reverse to show oldest first
    history.reverse().forEach(entry => {
      const userMsg = document.createElement("div");
      userMsg.classList.add("message", "user");
      userMsg.textContent = entry.question;
      container.appendChild(userMsg);

      const botMsg = document.createElement("div");
      botMsg.classList.add("message", "bot");
      botMsg.textContent = entry.answer;
      container.appendChild(botMsg);
    });

    container.scrollTop = container.scrollHeight; // scroll to bottom
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}

let searchMatches = [];
let currentMatchIndex = -1;
let lastQuery = "";

const searchInput = document.getElementById("search");
const container = document.getElementById("message-container");

const nextBtn = document.createElement("button");
nextBtn.textContent = "Next";
nextBtn.style.display = "none";

const prevBtn = document.createElement("button");
prevBtn.textContent = "Previous";
prevBtn.style.display = "none";

document.getElementById("search-form").appendChild(prevBtn);
document.getElementById("search-form").appendChild(nextBtn);

function highlightMessage(msg) {
  container.querySelectorAll(".message").forEach(m => m.style.background = "");
  container.querySelectorAll(".message").forEach(m => m.style.border = "0px");
  if (!msg) return;
  msg.style.background = "#599be7ff";
  msg.style.border = "2px solid #f39c12"; // add a visible border
  msg.scrollIntoView({ behavior: "smooth", block: "center" });
}

function runSearch() {
  const query = searchInput.value.trim().toLowerCase();

  if (!query) {
    // Clear matches and highlights
    searchMatches = [];
    currentMatchIndex = -1;
    nextBtn.style.display = "none";
    prevBtn.style.display = "none";
    lastQuery = "";

    // Remove highlight from any messages
    container.querySelectorAll(".message").forEach(m => m.style.background = "");
    container.querySelectorAll(".message").forEach(m => m.style.border = "0px");

    return;
  }

  // Only re-run search if the query changed
  if (query !== lastQuery) {
    const messages = Array.from(container.querySelectorAll(".message"));
    searchMatches = messages.filter(msg => msg.textContent.toLowerCase().includes(query));
    currentMatchIndex = searchMatches.length ? 0 : -1;
    lastQuery = query;

    // Show/hide navigation buttons
    if (searchMatches.length > 1) {
      nextBtn.style.display = "inline-block";
      prevBtn.style.display = "inline-block";
    } else {
      nextBtn.style.display = "none";
      prevBtn.style.display = "none";
    }
  }

  highlightMessage(searchMatches[currentMatchIndex]);
}

function nextMatch() {
  if (!searchMatches.length) return;
  currentMatchIndex = (currentMatchIndex + 1) % searchMatches.length;
  highlightMessage(searchMatches[currentMatchIndex]);
}

function prevMatch() {
  if (!searchMatches.length) return;
  currentMatchIndex = (currentMatchIndex - 1 + searchMatches.length) % searchMatches.length;
  highlightMessage(searchMatches[currentMatchIndex]);
}

searchInput.addEventListener("input", runSearch);

nextBtn.addEventListener("click", nextMatch);
prevBtn.addEventListener("click", prevMatch);

const searchForm = document.getElementById("search-form");
searchForm.addEventListener("submit", (e) => {
  e.preventDefault(); // prevent page reload
  runSearch();        // run search without clearing input
});


// Auto-resize question textarea
const textarea = document.getElementById("question");

function autoResize() {
  this.style.height = "auto"; // reset height
  this.style.height = this.scrollHeight + "px"; // set to fit content
}

textarea.addEventListener("input", autoResize);

// Initialize
loadDocuments();
loadHistory();

document.addEventListener("DOMContentLoaded", () => {
  loadDocuments(); // fetch documents immediately when page is ready
  loadHistory();
});