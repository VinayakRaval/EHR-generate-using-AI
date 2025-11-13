document.addEventListener("DOMContentLoaded", () => {

  const modal = new bootstrap.Modal(document.getElementById("generatePrescriptionModal"));
  const openBtn = document.getElementById("openGeneratePrescription");

  const searchInput = document.getElementById("searchPatient");
  const resultsBox = document.getElementById("patientSearchResults");
  const selectedPatient = document.getElementById("selectedPatientId");

  const voiceBtn = document.getElementById("startVoiceBtn");
  const voiceOutput = document.getElementById("voiceOutput");
  const saveBtn = document.getElementById("savePrescriptionBtn");

  let recognition = null;

  // -------------------------------
  // 1) OPEN MODAL
  // -------------------------------
  openBtn.addEventListener("click", () => {
    modal.show();
    setTimeout(() => searchInput.focus(), 150);
  });

  // -------------------------------
  // 2) LIVE SEARCH PATIENT
  // -------------------------------
  let timer = null;
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.trim();

    if (timer) clearTimeout(timer);

    if (q.length < 2) {
      resultsBox.innerHTML = "";
      return;
    }

    timer = setTimeout(async () => {
      const res = await fetch(`/doctor/search-patients?q=${encodeURIComponent(q)}`);
      const data = await res.json();

      resultsBox.innerHTML = "";

      if (!data.data || data.data.length === 0) {
        resultsBox.innerHTML = `<div class="list-group-item">No results</div>`;
        return;
      }

      data.data.forEach(p => {
        const btn = document.createElement("button");
        btn.className = "list-group-item list-group-item-action";
        btn.innerHTML = `${p.first_name} ${p.last_name}`;
        btn.onclick = () => {
          selectedPatient.value = p.patient_id;
          searchInput.value = `${p.first_name} ${p.last_name}`;
          resultsBox.innerHTML = "";
        };
        resultsBox.appendChild(btn);
      });
    }, 300);
  });

  // -------------------------------
  // 3) VOICE TO TEXT
  // -------------------------------
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = "en-US";
    recognition.interimResults = true;

    recognition.onstart = () => {
      voiceBtn.innerText = "🎙 Listening...";
      voiceBtn.classList.add("btn-warning");
    };

    recognition.onend = () => {
      voiceBtn.innerText = "🎤 Start Voice Input";
      voiceBtn.classList.remove("btn-warning");
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join("");
      voiceOutput.value = transcript;
    };

  } else {
    voiceBtn.disabled = true;
    voiceBtn.innerText = "Voice Not Supported";
  }

  voiceBtn.addEventListener("click", () => {
    try {
      recognition.start();
    } catch (e) {}
  });

  // -------------------------------
  // 4) SAVE PRESCRIPTION
  // -------------------------------
  saveBtn.addEventListener("click", async () => {

    if (!selectedPatient.value) {
      alert("Please select a patient first.");
      return;
    }
    if (!voiceOutput.value.trim()) {
      alert("Please speak the prescription first.");
      return;
    }

    const payload = {
      patient_id: parseInt(selectedPatient.value),
      diagnosis: "Voice Generated Diagnosis",
      prescription_text: voiceOutput.value,
      medicines: []   // Auto-extract later if you want
    };

    const res = await fetch("/doctor/add-prescription", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.status === "success") {
      alert("Prescription Added Successfully!");
      modal.hide();
      voiceOutput.value = "";
      selectedPatient.value = "";
      searchInput.value = "";
    } else {
      alert(data.message);
    }
  });

});
