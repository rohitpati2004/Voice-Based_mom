document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const progressContainer = document.getElementById("progressContainer");
    const currentFileName = document.getElementById("currentFileName");
    const progressPercent = document.getElementById("progressPercent");
    const progressBarFill = document.getElementById("progressBarFill");
    const stageText = document.getElementById("stageText");
    const jobList = document.getElementById("jobList");

    const idleState = document.getElementById("idleState");
    const resultContainer = document.getElementById("resultContainer");
    const meetingTitle = document.getElementById("meetingTitle");
    const fileTag = document.getElementById("fileTag");
    const audioPlayer = document.getElementById("audioPlayer");
    const speakerStatsGrid = document.getElementById("speakerStatsGrid");
    const summaryText = document.getElementById("summaryText");
    const keyPointsList = document.getElementById("keyPointsList");
    const decisionsList = document.getElementById("decisionsList");
    const actionTableBody = document.getElementById("actionTableBody");
    const transcriptList = document.getElementById("transcriptList");

    const exportPdfBtn = document.getElementById("exportPdfBtn");
    const exportDocxBtn = document.getElementById("exportDocxBtn");
    const exportJsonBtn = document.getElementById("exportJsonBtn");

    let activeJobId = null;
    let pollingInterval = null;

    // --- File Drag & Drop ---
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#2563EB";
    });
    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "rgba(56, 189, 248, 0.3)";
    });
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "rgba(56, 189, 248, 0.3)";
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // --- Upload File ---
    async function handleFileUpload(file) {
        progressContainer.classList.remove("hidden");
        currentFileName.textContent = file.name;
        progressPercent.textContent = "0%";
        progressBarFill.style.width = "0%";
        stageText.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading file...';

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            if (!res.ok) {
                alert("Upload failed: " + (data.detail || "Unknown error"));
                progressContainer.classList.add("hidden");
                return;
            }

            activeJobId = data.job_id;
            startPollingStatus(data.job_id);
            fetchJobsList();
        } catch (err) {
            alert("Error uploading file: " + err.message);
            progressContainer.classList.add("hidden");
        }
    }

    // --- Poll Job Status ---
    function startPollingStatus(jobId) {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/jobs/${jobId}`);
                if (!res.ok) return;
                const statusData = await res.json();

                progressPercent.textContent = `${statusData.progress}%`;
                progressBarFill.style.width = `${statusData.progress}%`;
                stageText.innerHTML = `<i class="fa-solid fa-gear fa-spin"></i> ${statusData.stage}`;

                if (statusData.status === "COMPLETED") {
                    clearInterval(pollingInterval);
                    progressContainer.classList.add("hidden");
                    fetchJobResult(jobId);
                    fetchJobsList();
                } else if (statusData.status === "FAILED") {
                    clearInterval(pollingInterval);
                    stageText.innerHTML = `<span style="color: #EF4444;"><i class="fa-solid fa-triangle-exclamation"></i> ${statusData.error_message || "Processing Failed"}</span>`;
                    fetchJobsList();
                }
            } catch (err) {
                console.error("Status polling error:", err);
            }
        }, 1500);
    }

    // --- Fetch & Render Job Result ---
    async function fetchJobResult(jobId) {
        activeJobId = jobId;
        try {
            const res = await fetch(`/api/jobs/${jobId}/result`);
            if (!res.ok) return;
            const data = await res.json();

            idleState.classList.add("hidden");
            resultContainer.classList.remove("hidden");

            meetingTitle.textContent = data.meeting_title || "Meeting Minutes";
            fileTag.innerHTML = `<i class="fa-solid fa-file-audio"></i> ${data.filename}`;

            // Load Audio source
            audioPlayer.src = `/api/jobs/${jobId}/media`;

            // Render Speaker Stats
            renderSpeakerStats(data.statistics);

            // Render Summary
            summaryText.textContent = data.summary || "No summary available.";

            // Render Key Points
            renderKeyPoints(data.key_discussion_points);

            // Render Decisions
            renderDecisions(data.decisions);

            // Render Action Items
            renderActionItems(data.action_items);

            // Render Transcript with Timestamp Sync Click Listener
            renderTranscript(data.transcript);

        } catch (err) {
            console.error("Error fetching job result:", err);
        }
    }

    // --- Render Components ---
    function renderSpeakerStats(stats) {
        speakerStatsGrid.innerHTML = "";
        const spkStats = stats?.speaker_statistics || [];
        if (spkStats.length === 0) {
            speakerStatsGrid.innerHTML = "<p>No speaker data available.</p>";
            return;
        }

        spkStats.forEach(s => {
            const card = document.createElement("div");
            card.className = "speaker-card";
            card.innerHTML = `
                <div class="speaker-card-header">
                    <span class="speaker-name">${s.speaker}</span>
                    <span class="speaker-prop" style="color: var(--accent-cyan);">${s.speaking_proportion_percent}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${s.speaking_proportion_percent}%;"></div>
                </div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 6px; display: flex; justify-content: space-between;">
                    <span>Duration: ${s.speaking_duration_formatted}</span>
                    <span>Segments: ${s.segment_count}</span>
                </div>
            `;
            speakerStatsGrid.appendChild(card);
        });
    }

    function renderKeyPoints(keyPoints) {
        keyPointsList.innerHTML = "";
        if (!keyPoints || keyPoints.length === 0) {
            keyPointsList.innerHTML = "<p>No key discussion points identified.</p>";
            return;
        }
        keyPoints.forEach(kp => {
            const div = document.createElement("div");
            div.style.marginBottom = "14px";
            let pointsHtml = (kp.points || []).map(p => `<li style="margin-left: 20px; font-size: 13px; line-height: 1.5;">${p}</li>`).join("");
            div.innerHTML = `<h5 style="color: var(--accent-cyan); font-size: 14px; margin-bottom: 4px;">• ${kp.topic}</h5><ul>${pointsHtml}</ul>`;
            keyPointsList.appendChild(div);
        });
    }

    function renderDecisions(decisions) {
        decisionsList.innerHTML = "";
        if (!decisions || decisions.length === 0) {
            decisionsList.innerHTML = "<p>No specific decisions identified.</p>";
            return;
        }
        decisions.forEach(d => {
            const item = document.createElement("div");
            item.style.padding = "10px";
            item.style.background = "rgba(255,255,255,0.02)";
            item.style.border = "1px solid var(--border-color)";
            item.style.borderRadius = "8px";
            item.style.marginBottom = "8px";
            item.innerHTML = `<strong style="color: var(--accent-cyan);">[${d.timestamp}] ${d.speaker}:</strong> ${d.decision}`;
            decisionsList.appendChild(item);
        });
    }

    function renderActionItems(actions) {
        actionTableBody.innerHTML = "";
        if (!actions || actions.length === 0) {
            actionTableBody.innerHTML = "<tr><td colspan='4'>No action items assigned.</td></tr>";
            return;
        }
        actions.forEach(a => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight: 600; color: var(--accent-cyan);">${a.assignee}</td>
                <td>${a.task}</td>
                <td>${a.timestamp}</td>
                <td><span class="status-tag status-PROCESSING">${a.status}</span></td>
            `;
            actionTableBody.appendChild(tr);
        });
    }

    function renderTranscript(transcript) {
        transcriptList.innerHTML = "";
        if (!transcript || transcript.length === 0) {
            transcriptList.innerHTML = "<p>No transcript entries.</p>";
            return;
        }

        transcript.forEach(seg => {
            const turn = document.createElement("div");
            turn.className = "transcript-turn";
            
            const startM = String(Math.floor(seg.start / 60)).padStart(2, '0');
            const startS = String(Math.floor(seg.start % 60)).padStart(2, '0');
            const endM = String(Math.floor(seg.end / 60)).padStart(2, '0');
            const endS = String(Math.floor(seg.end % 60)).padStart(2, '0');

            turn.innerHTML = `
                <div class="turn-header">
                    <span class="turn-speaker"><i class="fa-solid fa-user"></i> ${seg.speaker}</span>
                    <span class="turn-time"><i class="fa-regular fa-clock"></i> ${startM}:${startS} - ${endM}:${endS} [${seg.language}]</span>
                </div>
                <div class="turn-text">${seg.text}</div>
            `;

            // Interactive Timestamp Synchronization: Click to Play Segment
            turn.addEventListener("click", () => {
                audioPlayer.currentTime = seg.start;
                audioPlayer.play();
                // Highlight turn
                document.querySelectorAll(".transcript-turn").forEach(t => t.style.borderColor = "var(--border-color)");
                turn.style.borderColor = "var(--accent-cyan)";
            });

            transcriptList.appendChild(turn);
        });
    }

    // --- Tab Switching ---
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });

    // --- Export Handlers ---
    exportPdfBtn.addEventListener("click", () => {
        if (activeJobId) window.open(`/api/jobs/${activeJobId}/export/pdf`, "_blank");
    });
    exportDocxBtn.addEventListener("click", () => {
        if (activeJobId) window.open(`/api/jobs/${activeJobId}/export/docx`, "_blank");
    });
    exportJsonBtn.addEventListener("click", () => {
        if (activeJobId) window.open(`/api/jobs/${activeJobId}/export/json`, "_blank");
    });

    // --- Jobs History List ---
    async function fetchJobsList() {
        try {
            const res = await fetch("/api/jobs");
            if (!res.ok) return;
            const jobs = await res.json();

            if (jobs.length === 0) {
                jobList.innerHTML = '<p class="empty-text">No previous recordings found.</p>';
                return;
            }

            jobList.innerHTML = "";
            jobs.forEach(job => {
                const item = document.createElement("div");
                item.className = "job-item";
                item.innerHTML = `
                    <div>
                        <div class="job-item-title">${job.filename}</div>
                        <div style="font-size: 11px; color: var(--text-muted);">${new Date(job.created_at).toLocaleTimeString()}</div>
                    </div>
                    <span class="status-tag status-${job.status}">${job.status}</span>
                `;
                item.addEventListener("click", () => {
                    if (job.status === "COMPLETED") {
                        fetchJobResult(job.job_id);
                    } else if (job.status === "PROCESSING") {
                        startPollingStatus(job.job_id);
                    }
                });
                jobList.appendChild(item);
            });
        } catch (err) {
            console.error("Error fetching job list:", err);
        }
    }

    // Initial Load
    fetchJobsList();
});
