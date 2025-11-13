/* =====================================================
   PURE VOICE → AI → SINGLE FINAL TEXT PRESCRIPTION
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    // ----- MODAL ELEMENTS -----
    const modalEl = document.getElementById("aiPrescriptionModal");
    const modal = new bootstrap.Modal(modalEl);

    const pidEl   = document.getElementById("modalPid");
    const pName   = document.getElementById("pName");
    const pAge    = document.getElementById("pAge");
    const pPhone  = document.getElementById("pPhone");

    const startBtn = document.getElementById("startVoice");
    const stopBtn  = document.getElementById("stopVoice");

    const rawBox   = document.getElementById("voiceRaw");      // Raw voice text
    const aiBtn    = document.getElementById("aiStructureBtn");
    const preview  = document.getElementById("previewBox");     // Final AI text
    const saveBtn  = document.getElementById("savePrescription");


    // ----- GLOBAL VOICE STATE -----
    let recognizer = null;
    let recording = false;
    let finalText = "";


    // =====================================================
    // TOAST
    // =====================================================
    function toast(msg, type="info") {
        const div = document.createElement("div");
        div.className = `alert alert-${type} position-fixed top-0 end-0 mt-3 me-3`;
        div.style.zIndex = 5000;
        div.innerText = msg;
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }


    // =====================================================
    // OPEN MODAL FROM PATIENT CARD
    // =====================================================
    document.querySelectorAll("[data-open-generate]").forEach(btn => {
        btn.addEventListener("click", () => {

            pidEl.value = btn.dataset.pid;
            pName.innerText  = btn.dataset.name;
            pAge.innerText   = btn.dataset.age;
            pPhone.innerText = btn.dataset.phone;

            rawBox.value = "";
            preview.innerHTML = "";
            finalText = "";

            modal.show();
        });
    });


    // =====================================================
    // 1) START VOICE RECORDING (Continuous Mode)
    // =====================================================
    startBtn.addEventListener("click", () => {

        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return toast("Voice input not supported in this browser", "danger");

        recognizer = new SR();
        recognizer.lang = "en-IN";
        recognizer.interimResults = true;
        recognizer.continuous = true;     // <<< FIXES AUTO-STOP

        recording = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;

        rawBox.value = "";
        finalText = "";
        preview.innerHTML = "";

        recognizer.onresult = (event) => {

            let chunk = "";

            for (let i = 0; i < event.results.length; i++) {
                const txt = event.results[i][0].transcript;

                // Add only FINAL text into finalText (prevents duplicates)
                if (event.results[i].isFinal) {
                    finalText += txt + " ";
                }

                chunk = txt;
            }

            // Live preview while speaking (no resetting)
            rawBox.value = finalText + " " + chunk;
        };

        recognizer.onend = () => {
            if (recording) {
                // Restart automatically while breathing
                try { recognizer.start(); } catch {}
            }
        };

        recognizer.onerror = (err) => {
            toast("Voice error: " + err.error, "danger");
        };

        recognizer.start();
        toast("🎤 Recording… Speak your full prescription", "success");
    });


    // =====================================================
    // 2) STOP VOICE
    // =====================================================
    stopBtn.addEventListener("click", () => {

        recording = false;

        if (recognizer) {
            try { recognizer.stop(); } catch {}
        }

        startBtn.disabled = false;
        stopBtn.disabled = true;

        toast("⛔ Voice recording stopped", "info");
    });


    // =====================================================
    // 3) AI STRUCTURE (Send → AI → formatted)
    // =====================================================
    aiBtn.addEventListener("click", async () => {

        if (!finalText.trim())
            return toast("Speak prescription first!", "warning");

        preview.innerHTML = "⏳ Processing with AI…";

        const resp = await fetch("/doctor/ai/structure", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ text: finalText })
        });

        const data = await resp.json();

        if (data.status !== "success") {
            preview.innerHTML = "❌ AI Error";
            return;
        }

        preview.innerText = data.structured;
    });


    // =====================================================
    // 4) SAVE PRESCRIPTION
    // =====================================================
    saveBtn.addEventListener("click", async () => {

        if (!preview.innerText.trim())
            return toast("Generate AI preview first!", "warning");

        const payload = {
            patient_id: parseInt(pidEl.value),
            final_text: preview.innerText.trim()
        };

        const resp = await fetch("/doctor/add-prescription-ai", {
            method:"POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(payload)
        });

        const data = await resp.json();

        if (data.status !== "success") {
            toast(data.message, "danger");
            return;
        }

        toast("Prescription saved!", "success");
        modal.hide();

        // Auto-open PDF
        if (data.prescription_id) {
            window.open(`/doctor/prescription/${data.prescription_id}/pdf`, "_blank");
        }
    });

});
