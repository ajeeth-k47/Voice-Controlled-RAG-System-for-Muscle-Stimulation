async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok)
    throw new Error((await res.text()) || `Request failed: ${res.status}`);
  return res.json();
}

function byId(id) {
  return document.getElementById(id);
}
function pathName() {
  return window.location.pathname.toLowerCase();
}

function shuffled(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

// ─── Evaluate page ───

function startEvaluatePage() {
  if (!pathName().endsWith("/evaluate.html")) return;

  const stepTitle = byId("stepTitle");
  const stepCounter = byId("stepCounter");
  const commandLabel = byId("commandLabel");
  const customBlock = byId("customBlock");
  const intendedCommand = byId("intendedCommand");
  const bodyPartSelect = byId("bodyPartSelect");
  const movementVideo = byId("movementVideo");
  const customNoVideo = byId("customNoVideo");
  const wbsContainer = byId("wbsContainer");
  const bpqContainer = byId("bpqContainer");
  const participantId = byId("participantId");
  const submissionComment = byId("submissionComment");
  const prevBtn = byId("prevBtn");
  const nextBtn = byId("nextBtn");
  const statusMsg = byId("statusMsg");

  let config = null;
  let step = 0;
  let answers = {};
  let movementOrder = [];

  const WBS_RUBRIC = {
    5: "Follows well, no redundant/strange movements",
    4: "Generally follows (70–90%), minor errors",
    3: "Follows 40–60%, one or two major errors",
    2: "Some sign of following (20–30%), far from goal",
    1: "Does not follow the instruction at all",
  };
  const BPQ_LABELS = ["Good", "Partially Good", "Bad", "Not Relevant"];

  function current() {
    return movementOrder[step];
  }

  function getAnswer() {
    if (!answers[current().id]) {
      answers[current().id] = {
        wbs: null,
        bpq: {},
        intended_command: "",
        selected_parts: [],
      };
    }
    return answers[current().id];
  }

  function isCustomMovement(mv) {
    return Boolean(mv.custom);
  }

  function getSelectedParts(mv, ans) {
    if (!isCustomMovement(mv)) return mv.body_parts || [];
    return ans.selected_parts || [];
  }

  function renderBodyPartSelect() {
    const mv = current();
    const ans = getAnswer();
    bodyPartSelect.innerHTML = "";

    const parts =
      config && config.available_body_parts ? config.available_body_parts : [];
    for (const bp of parts) {
      const label = document.createElement("label");
      label.className = "bpq-select-row";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = (ans.selected_parts || []).includes(bp);
      cb.addEventListener("change", () => {
        const set = new Set(ans.selected_parts || []);
        if (cb.checked) set.add(bp);
        else set.delete(bp);
        ans.selected_parts = Array.from(set);
        renderBodyPartSelect();
        renderBPQ();
      });
      const text = document.createElement("span");
      text.textContent = bp;
      label.appendChild(cb);
      label.appendChild(text);
      bodyPartSelect.appendChild(label);
    }
  }

  function renderWBS() {
    const ans = getAnswer();
    wbsContainer.innerHTML = "";
    for (const score of [5, 4, 3, 2, 1]) {
      const row = document.createElement("label");
      row.className = "wbs-row" + (ans.wbs === score ? " selected" : "");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "wbs";
      radio.value = score;
      radio.checked = ans.wbs === score;
      radio.addEventListener("change", () => {
        ans.wbs = score;
        renderWBS();
      });
      const text = document.createElement("span");
      text.innerHTML = `<strong>${score}</strong> — ${WBS_RUBRIC[score]}`;
      row.appendChild(radio);
      row.appendChild(text);
      wbsContainer.appendChild(row);
    }
  }

  function renderBPQ() {
    const mv = current();
    const ans = getAnswer();
    bpqContainer.innerHTML = "";

    const partsToRate = getSelectedParts(mv, ans);
    if (isCustomMovement(mv) && partsToRate.length === 0) {
      const empty = document.createElement("p");
      empty.className = "hint";
      empty.textContent = "Select at least one body part above to rate BPQ.";
      bpqContainer.appendChild(empty);
      return;
    }

    for (const bp of partsToRate) {
      const group = document.createElement("div");
      group.className = "bpq-group";

      const title = document.createElement("div");
      title.className = "bpq-title";
      title.textContent = bp;
      group.appendChild(title);

      const row = document.createElement("div");
      row.className = "bpq-row";
      for (const label of BPQ_LABELS) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "bpq-btn" + (ans.bpq[bp] === label ? " active" : "");
        btn.textContent = label;
        btn.addEventListener("click", () => {
          ans.bpq[bp] = label;
          renderBPQ();
        });
        row.appendChild(btn);
      }
      group.appendChild(row);
      bpqContainer.appendChild(group);
    }
  }

  function renderStep() {
    const mv = current();
    stepTitle.textContent = mv.category;
    stepCounter.textContent = `${step + 1} / ${movementOrder.length}`;
    const ans = getAnswer();

    if (isCustomMovement(mv)) {
      commandLabel.innerHTML = `<strong>${mv.command}</strong>`;
      customBlock.style.display = "block";
      movementVideo.style.display = "none";
      customNoVideo.style.display = "block";
      intendedCommand.value = ans.intended_command || "";
      intendedCommand.oninput = () => {
        ans.intended_command = intendedCommand.value;
      };
      renderBodyPartSelect();
    } else {
      commandLabel.innerHTML = `Command: <strong>"${mv.command}"</strong>`;
      customBlock.style.display = "none";
      movementVideo.style.display = "block";
      customNoVideo.style.display = "none";
    }
    if (!isCustomMovement(mv)) {
      movementVideo.src = `/motion/${mv.video}`;
    } else {
      movementVideo.removeAttribute("src");
    }
    renderWBS();
    renderBPQ();
    prevBtn.disabled = step === 0;
    nextBtn.textContent = step === movementOrder.length - 1 ? "Submit" : "Next";
    statusMsg.textContent = "";
  }

  function validate() {
    const mv = current();
    const ans = getAnswer();
    if (!ans.wbs) {
      statusMsg.textContent = "Please select a WBS score before continuing.";
      return false;
    }

    if (isCustomMovement(mv)) {
      if (!(ans.intended_command || "").trim()) {
        statusMsg.textContent =
          "Please enter the intended movement for this custom video.";
        return false;
      }
      const parts = getSelectedParts(mv, ans);
      if (parts.length === 0) {
        statusMsg.textContent =
          "Please select at least one body part to rate for BPQ.";
        return false;
      }
      for (const bp of parts) {
        if (!ans.bpq[bp]) {
          statusMsg.textContent = `Please rate "${bp}" before continuing.`;
          return false;
        }
      }
    } else {
      for (const bp of mv.body_parts || []) {
        if (!ans.bpq[bp]) {
          statusMsg.textContent = `Please rate "${bp}" before continuing.`;
          return false;
        }
      }
    }
    return true;
  }

  prevBtn.addEventListener("click", () => {
    if (step > 0) {
      step--;
      renderStep();
    }
  });

  nextBtn.addEventListener("click", async () => {
    if (!validate()) return;

    if (step < movementOrder.length - 1) {
      step++;
      renderStep();
      return;
    }

    // Build submission in config order
    const responses = config.movements.map((mv) => {
      const ans = answers[mv.id];
      const parts = getSelectedParts(mv, ans);
      return {
        movement_id: mv.id,
        intended_command: isCustomMovement(mv)
          ? (ans.intended_command || "").trim()
          : null,
        wbs: ans.wbs,
        bpq: parts.map((bp) => ({
          body_part: bp,
          label: ans.bpq[bp],
        })),
      };
    });

    const payload = {
      participant_id: (participantId.value || "").trim() || null,
      comment: (submissionComment.value || "").trim() || null,
      responses,
    };

    nextBtn.disabled = true;
    prevBtn.disabled = true;
    statusMsg.textContent = "Submitting...";

    try {
      await fetchJson("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      statusMsg.textContent = "Submitted successfully. Thank you!";
      setTimeout(() => {
        window.location.href = "/";
      }, 1200);
    } catch (err) {
      nextBtn.disabled = false;
      prevBtn.disabled = false;
      statusMsg.textContent = `Submit failed: ${err.message}`;
    }
  });

  fetchJson("/api/config")
    .then((cfg) => {
      config = cfg;
      // Show movements in the same order for every participant:
      // first the 7 predefined movements, then the 3 custom rating pages.
      movementOrder = config.movements;
      renderStep();
    })
    .catch((err) => {
      statusMsg.textContent = `Failed to load: ${err.message}`;
    });
}

// ─── Results page ───

function startResultsPage() {
  if (!pathName().endsWith("/results.html")) return;

  const summaryCards = byId("summaryCards");
  const wbsTbody = document.querySelector("#wbsTable tbody");
  const bpqSummaryHandTbody = document.querySelector("#bpqSummaryHand tbody");
  const bpqSummarySoccerTbody = document.querySelector(
    "#bpqSummarySoccer tbody",
  );
  const customByParticipantTbody = document.querySelector(
    "#customByParticipant tbody",
  );
  const commentsTableBody = document.querySelector("#commentsTable tbody");
  const bpqSection = byId("bpqSection");

  function card(label, value) {
    return `<div class="metric-card"><div class="label">${label}</div><div class="value">${value}</div></div>`;
  }

  fetchJson("/api/results")
    .then((data) => {
      summaryCards.innerHTML = [
        card("Submissions", data.submission_count),
        card("Overall WBS", `${data.overall_wbs} / 5.0`),
      ].join("");

      // WBS table
      wbsTbody.innerHTML = "";
      for (const row of data.wbs_per_movement) {
        const tr = document.createElement("tr");
        const isCustom = Boolean(row.custom);
        const customCmd = isCustom
          ? row.intended_commands && row.intended_commands[0]
            ? row.intended_commands[0]
            : ""
          : "";
        tr.innerHTML = `
          <td>${row.command}${customCmd ? `<div class="hint">Intended: ${customCmd}</div>` : ""}</td>
          <td>${row.category}</td>
          <td>${row.mean_wbs}</td>
          <td>${row.n}</td>
        `;
        wbsTbody.appendChild(tr);
      }

      // BPQ tables
      bpqSummaryHandTbody.innerHTML = "";
      for (const row of data.bpq_summary_hand || []) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.body_part}</td>
          <td>${row.good_pct}</td>
          <td>${row.partial_pct}</td>
          <td>${row.bad_pct}</td>
          <td>${row.relevant_ratings}</td>
          <td>${row.total_ratings}</td>
        `;
        bpqSummaryHandTbody.appendChild(tr);
      }

      bpqSummarySoccerTbody.innerHTML = "";
      for (const row of data.bpq_summary_soccer || []) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.body_part}</td>
          <td>${row.good_pct}</td>
          <td>${row.partial_pct}</td>
          <td>${row.bad_pct}</td>
          <td>${row.relevant_ratings}</td>
          <td>${row.total_ratings}</td>
        `;
        bpqSummarySoccerTbody.appendChild(tr);
      }

      customByParticipantTbody.innerHTML = "";
      for (const sub of data.custom_by_participant || []) {
        const pid = sub.participant_id || sub.submission_id || "Unknown";
        for (const row of sub.custom || []) {
          const bpq = (row.bpq || [])
            .map((x) => `${x.body_part}: ${x.label}`)
            .join(", ");
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${pid}</td>
            <td>${row.movement_id}</td>
            <td>${row.intended_command || ""}</td>
            <td>${row.wbs ?? ""}</td>
            <td>${bpq}</td>
          `;
          customByParticipantTbody.appendChild(tr);
        }
      }

      commentsTableBody.innerHTML = "";
      const comments = data.comments || [];
      if (comments.length === 0) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="3" class="hint">No comments submitted yet.</td>`;
        commentsTableBody.appendChild(tr);
      } else {
        for (const item of comments) {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${item.participant_id || item.submission_id || "Unknown"}</td>
            <td>${item.submission_id || ""}</td>
            <td>${item.comment || ""}</td>
          `;
          commentsTableBody.appendChild(tr);
        }
      }

      bpqSection.innerHTML = "";
      for (const mv of data.bpq_per_movement) {
        const wrapper = document.createElement("div");
        wrapper.className = "bpq-result-block";
        let html = `<h3>${mv.command}</h3>`;
        html += `<div class="table-wrap"><table><thead><tr>
          <th>Body Part</th><th>Good %</th><th>Partially Good %</th><th>Bad %</th><th>Not Relevant</th><th>Total</th>
        </tr></thead><tbody>`;
        for (const bp of mv.body_parts) {
          html += `<tr>
            <td>${bp.body_part}</td>
            <td>${bp.good_pct}</td>
            <td>${bp.partial_pct}</td>
            <td>${bp.bad_pct}</td>
            <td>${bp.not_relevant}</td>
            <td>${bp.total_ratings}</td>
          </tr>`;
        }
        html += "</tbody></table></div>";
        wrapper.innerHTML = html;
        bpqSection.appendChild(wrapper);
      }
    })
    .catch((err) => {
      summaryCards.innerHTML = card("Error", err.message);
    });
}

startEvaluatePage();
startResultsPage();
