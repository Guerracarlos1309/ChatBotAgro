function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => addMessage(data.response, "bot"))
    .catch((error) => {
      console.error("Error:", error);
      addMessage("Error al conectar con el servidor.", "bot");
    });
}

function addMessage(text, sender) {
  const chatBox = document.getElementById("chat-box");
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${sender}`;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  const formattedText = text
    .replace(/\n/g, "<br>")
    .replace(/• /g, "👉 ")
    .replace(/\*(.*?)\*/g, "<strong>$1</strong>");

  let i = 0;
  const interval = setInterval(() => {
    msgDiv.innerHTML = formattedText.slice(0, i);
    i++;
    chatBox.scrollTop = chatBox.scrollHeight;
    if (i > formattedText.length) clearInterval(interval);
  }, 5);
}

document.getElementById("reset-btn").addEventListener("click", () => {
  fetch("/reset", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      const chatBox = document.getElementById("chat-box");
      chatBox.innerHTML = "";
      addMessage(data.response, "bot");
    })
    .catch((error) => {
      console.error("Error al restablecer:", error);
    });
});

document
  .getElementById("user-input")
  .addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
  });
