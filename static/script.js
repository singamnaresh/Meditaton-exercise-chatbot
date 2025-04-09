const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");

let synth = window.speechSynthesis;
let recognition;
if ("webkitSpeechRecognition" in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";
  recognition.onresult = (event) => {
    input.value = event.results[0][0].transcript;
    sendMessage();
  };
}

function startListening() {
  if (recognition) recognition.start();
}

function stopSpeaking() {
  synth.cancel();
}

function addMessage(content, className) {
  const msg = document.createElement("div");
  msg.className = `message ${className}`;
  msg.innerHTML = content.replace(/\n/g, "<br>");
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
  const message = input.value.trim();
  if (!message) return;
  addMessage("🧘 You: " + message, "user");
  input.value = "";

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })
    .then((res) => res.json())
    .then((data) => {
      addMessage("🤖 Bot:<br>" + formatPoints(data.response), "bot");
      speakText(data.response);
    })
    .catch(() => addMessage("❌ Network error!", "bot"));
}

function handleKeyPress(e) {
  if (e.key === "Enter") sendMessage();
}

function formatPoints(text) {
  return text
    .split("\n")
    .map((point) => `🔹 ${point.trim()}`)
    .join("<br>");
}

function speakText(text) {
  stopSpeaking();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "en-US";
  synth.speak(utter);
}
