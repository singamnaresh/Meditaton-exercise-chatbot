const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");

let synth = window.speechSynthesis;
let recognition;
let alarmSound;
let lastPoseFeedback = ""; // 🔁 For image context memory

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
    body: JSON.stringify({
      message: message,
      pose_context: lastPoseFeedback // 🔁 Include pose context
    }),
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

function setAlarm(minutes) {
  const milliseconds = minutes * 60 * 1000;
  setTimeout(() => {
    addMessage("⏰ Time’s up! Starting your meditation or exercise now.", "bot");

    if (alarmSound) {
      alarmSound.loop = true;
      alarmSound.play().then(() => {
        console.log("🔔 Alarm is ringing.");
      }).catch(err => {
        console.error("🔇 Failed to play alarm:", err);
        addMessage("🔇 Audio playback was blocked. Please click anywhere first.", "bot");
      });

      document.getElementById("stopAlarmBtn").style.display = "inline-block";
    }
  }, milliseconds);
}

function setAlarmFromInput() {
  const minutes = parseInt(document.getElementById("alarmInput").value);
  if (!isNaN(minutes) && minutes > 0) {
    alert(`✅ Alarm set for ${minutes} minute(s)!`);
    setAlarm(minutes);
  } else {
    alert("❌ Please enter a valid number of minutes.");
  }
}

function stopAlarm() {
  if (alarmSound) {
    alarmSound.pause();
    alarmSound.currentTime = 0;
    document.getElementById("stopAlarmBtn").style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  alarmSound = new Audio("static/meditation.mp3");
  document.body.addEventListener(
    "click",
    () => {
      alarmSound
        .play()
        .then(() => {
          alarmSound.pause();
          alarmSound.currentTime = 0;
          console.log("🔊 Audio unlocked by click");
        })
        .catch((err) => {
          console.error("Audio unlock failed on click.", err);
        });
    },
    { once: true }
  );
});

// ✅ Enhanced Pose Upload Handler (shows feedback only in chat)
document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const fileInput = document.getElementById("poseInput");
  const file = fileInput.files[0];

  if (!file) {
    addMessage("❌ Please select a file first.", "bot");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  addMessage("📸 Uploading and analyzing your exercise pose...", "user");

  fetch("/analyze_pose", {
    method: "POST",
    body: formData,
  })
    .then(async (res) => {
      const contentType = res.headers.get("content-type");
      if (res.ok && contentType && contentType.includes("application/json")) {
        return res.json();
      } else {
        const text = await res.text();
        throw new Error(`Expected JSON, got: ${text.slice(0, 100)}`);
      }
    })
    .then((data) => {
      const feedback = data.result || "✅ Posture feedback received.";
      lastPoseFeedback = feedback;
  
      let content = `🤖 Bot:<br>${formatPoints(feedback)}`;
  
      if (data.image_url) {
        content += `<br><img src="${data.image_url}" alt="Correct Pose" style="max-width:200px;border-radius:10px;margin-top:5px;">`;
      }
  
      addMessage(content, "bot");
  
      // Only speak if feedback is safe text
      if (typeof feedback === "string" && feedback.length < 500) {
        speakText(feedback);
      }
    })
    .catch((err) => {
      console.error("Pose analysis error:", err.message || err);
      addMessage("❌ Error analyzing pose. Please try again.", "bot");
    });

    
});
