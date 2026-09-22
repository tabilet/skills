/* Tabilet Explorer client. All project text is rendered through textContent. */
(function () {
  "use strict";
  const state = { view: "overview", timelineNext: null, timelinePrevious: null, timelineFilters: {}, todoOffsets: {}, generation: null, activity: null, poll: null, returnFocus: null, detailParameter: null };
  const todoGroups = ["resume", "ready", "waiting", "blocked", "needs_review"];
  const $ = (id) => document.getElementById(id);
  const list = (value) => Array.isArray(value) ? value : [];
  const obj = (value) => value && typeof value === "object" ? value : {};
  const string = (value) => String(value == null ? "" : value);
  function text(value) { return document.createTextNode(string(value)); }
  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = string(value);
      else if (value !== false && value != null) node.setAttribute(key, value === true ? "" : value);
    });
    list(children).forEach((child) => node.append(child instanceof Node ? child : text(child)));
    return node;
  }
  function button(label, handler, attrs) { const node = el("button", Object.assign({ type: "button" }, attrs), [label]); node.addEventListener("click", handler); return node; }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function badge(value, extra) { return el("span", { class: `badge ${extra || ""}` }, [value || "unknown"]); }
  function showNotice(message) { $("notice").hidden = !message; $("notice").textContent = message || ""; }
  function showDiagnostics(items) {
    const values = list(items).map(string).filter(Boolean); const node = $("diagnostics"); clear(node); node.hidden = values.length === 0;
    if (values.length) node.append(el("strong", {}, ["Diagnostics: "]), text(values.join("; ")));
  }
  async function api(path, options) {
    const response = await fetch(path, Object.assign({ headers: { Accept: "application/json" } }, options || {}));
    let body = {}; try { body = await response.json(); } catch (_) { body = { error: "The server returned an invalid response." }; }
    if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
    showDiagnostics(body.diagnostics || (body.index && body.index.diagnostics)); return body;
  }
  function updateUrl(values, replace) {
    const url = new URL(location.href);
    Object.entries(values).forEach(([key, value]) => { if (value) url.searchParams.set(key, value); else url.searchParams.delete(key); });
    history[replace ? "replaceState" : "pushState"]({}, "", url);
  }
  function detailUrl(kind, value, extras) {
    const values = { run: null, document: null, line: null, search: null, search_offset: null,
      event_offset: null, message_offset: null, child_offset: null };
    values[kind] = value;
    return Object.assign(values, extras || {});
  }
  function activityChanged(beforeGeneration, beforeActivity, generation, activity) { return generation !== beforeGeneration || activity !== beforeActivity; }
  function source(ref) {
    const value = obj(ref); const path = value.path || value.source_path;
    if (!path) return el("span", { class: "source" }, ["source unavailable"]);
    const label = `${path}${value.line ? `:${value.line}` : ""}`;
    return button(label, () => openDocument(path, value.line), { class: "source source-button", "aria-label": `Open ${label}` });
  }
  function setView(view, replace) {
    state.view = ["overview", "timeline", "todo"].includes(view) ? view : "overview";
    document.querySelectorAll("[data-view-panel]").forEach((panel) => { panel.hidden = panel.dataset.viewPanel !== state.view; });
    document.querySelectorAll("[data-view]").forEach((link) => { if (link.dataset.view === state.view) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current"); });
    updateUrl({ view: state.view }, replace);
    if (state.view === "overview") loadOverview();
    if (state.view === "timeline") loadTimeline(new URL(location.href).searchParams.get("cursor"));
    if (state.view === "todo") loadTodo();
  }
  function openAttention(item) {
    if (item.view === "timeline") {
      if (item.outcome) { state.timelineFilters.outcome = item.outcome; $("timeline-outcome").value = item.outcome; }
      updateUrl({ view: "timeline", outcome: item.outcome || null, cursor: null }, false);
      setView("timeline", true);
    } else {
      updateUrl({ view: "todo" }, false);
      setView("todo", true);
    }
  }
  function renderOverview(data) {
    const body = obj(data); const root = $("overview-content"); clear(root);
    $("overview-freshness").textContent = body.index && body.index.refreshed_at ? `Indexed ${body.index.refreshed_at}` : "Index status unavailable";
    if (body.summary) root.append(el("p", { class: "card", text: body.summary }));
    if (list(body.attention).length) {
      root.append(el("h3", {}, ["Needs attention"])); const attention = el("ul", { class: "attention-list" });
      list(body.attention).forEach((item) => { const row = el("li", { class: "attention-item" }, [el("strong", { text: item.title || item.kind || "Attention" }), el("p", { text: item.message || item.reason || "" })]); if (item.source) row.append(source(item.source)); else if (item.view) row.append(button(item.view === "timeline" ? "Open timeline" : "Open To-do", () => openAttention(item))); attention.append(row); }); root.append(attention);
    }
    const sections = [["Active milestones and tasks", body.active_milestones, "milestone"], ["History", body.history, "history"], ["Archives", body.archives, "archive"], ["Evolution", body.evolution, "evolution"]];
    sections.forEach(([title, records, kind]) => {
      const wrap = el("section", { class: "overview-section" }, [el("h3", {}, [title])]); const items = list(records);
      if (!items.length) wrap.append(el("p", { class: "muted" }, ["No indexed records available."]));
      else {
        const grouped = {};
        items.forEach((item) => { const group = kind === "history" ? item.group : kind === "archive" ? `Lane ${item.lane}` : kind === "evolution" ? `Version ${item.version}` : ""; (grouped[group] ||= []).push(item); });
        Object.entries(grouped).forEach(([group, groupItems]) => {
          if (group) wrap.append(el("h4", { class: "group-title", text: group }));
          const grid = el("div", { class: "card-grid" });
          groupItems.forEach((item) => {
          const card = el("article", { class: "card" }, [el("h3", { text: item.title || item.milestone_id || item.path || "Untitled" })]);
          card.append(el("p", { class: item.summary ? "" : "muted", text: item.summary || "No maintained summary is available." }));
          if (item.acceptance) card.append(el("p", {}, [el("strong", {}, ["Acceptance: "]), item.acceptance]));
          if (kind === "milestone") {
            const stats = el("div", { class: "stats" }); const counts = obj(item.counts);
            ["pending", "in_progress", "blocked", "completed", "cancelled", "historical"].forEach((key) => { if (counts[key] != null) stats.append(badge(`${key.replace("_", " ")}: ${counts[key]}`, `state-${key}`)); }); card.append(stats);
            if (list(item.tasks).length) { const tasks = el("ul", { class: "compact-list" }); list(item.tasks).forEach((task) => tasks.append(el("li", {}, [badge(task.state), " ", task.label, " ", source(task.source)]))); card.append(tasks); }
            if (item.tasks_truncated) card.append(el("p", { class: "muted", text: "Additional current tasks are available through To-do." }));
          }
          if (item.outcome) card.append(badge(item.outcome, `outcome-${item.outcome}`)); if (item.lane) card.append(badge(`lane ${item.lane}`)); if (list(item.pair_missing).length) card.append(el("p", { class: "diagnostic", text: `Missing counterpart: ${item.pair_missing.join(", ")}` })); if (item.source) card.append(source(item.source)); grid.append(card);
          }); wrap.append(grid);
        });
      } root.append(wrap);
    });
  }
  async function loadOverview() { try { renderOverview(await api("/api/overview")); } catch (error) { const root = $("overview-content"); clear(root); root.append(el("p", { class: "diagnostic", text: error.message })); } }
  function timelineEntry(item, child) {
    const entry = el("li", { class: child ? "timeline-entry timeline-child" : "timeline-entry" }); const exact = item.started_at || item.recorded_at || item.occurred_at; const when = exact ? new Date(exact).toLocaleString() : "Time unavailable";
    entry.append(el("time", { datetime: exact || "", title: exact || "", text: when })); const content = el("div"); content.append(el("h3", {}, [item.operation || "Recorded operation"])); content.append(el("p", { text: item.request_summary || "Request text was not captured." })); content.append(el("p", { class: "meta", text: item.result_summary || item.result || (item.unfinished ? "Unfinished run" : "No result summary recorded.") })); content.append(badge(`Capture: ${item.capture_fidelity || "incomplete"}`, "capture")); entry.append(content); entry.append(button("Open", () => openRun(item.run_id), { "aria-label": `Open ${item.operation || "run"} details` }));
    if (list(item.children).length) { const children = el("ol", { class: "timeline-children", "aria-label": "Goal child operations" }); list(item.children).forEach((record) => children.append(timelineEntry(record, true))); entry.append(children); }
    if (item.children_more) entry.append(el("p", { class: "muted", text: `${Math.max(0, Number(item.child_count || 0) - list(item.children).length)} additional child operations are available in run details.` }));
    return entry;
  }
  function timelineQuery(cursor) { const query = new URLSearchParams(); Object.entries(state.timelineFilters).forEach(([key, value]) => { if (value) query.set(key, value); }); const search = new URL(location.href).searchParams.get("search"); if (search) query.set("search", search); if (cursor) query.set("cursor", cursor); return query; }
  async function loadTimeline(cursor) {
    try { const body = obj(await api(`/api/timeline?${timelineQuery(cursor)}`)); state.timelineNext = body.next_cursor || null; state.timelinePrevious = body.previous_cursor || null; const root = $("timeline-content"); clear(root); const entries = list(body.entries || body.runs || body.results); if (!entries.length) root.append(el("p", { class: "muted" }, ["No recorded workflow entries match these filters."])); else { const records = el("ol", { class: "timeline-list" }); entries.forEach((item) => records.append(timelineEntry(item, false))); root.append(records); } renderTimelinePagination(); }
    catch (error) { const root = $("timeline-content"); clear(root); root.append(el("p", { class: "diagnostic", text: error.message })); }
  }
  function goTimeline(cursor) { updateUrl({ cursor }, false); loadTimeline(cursor); }
  function renderTimelinePagination() { const root = $("timeline-pagination"); clear(root); if (state.timelinePrevious) root.append(button("Previous", () => goTimeline(state.timelinePrevious))); if (state.timelineNext) root.append(button("Next", () => goTimeline(state.timelineNext))); }
  async function openSearch(query, push, offset) {
    const pageOffset = Math.max(0, Number(offset || 0));
    if (push !== false) updateUrl(detailUrl("search", query, { search_offset: pageOffset || null }), false);
    state.detailParameter = "search";
    try { const body = await api(`/api/search?q=${encodeURIComponent(query)}&limit=50&offset=${pageOffset}`); const root = el("div"); if (!list(body.results).length) root.append(el("p", { class: "muted" }, ["No indexed source matches."])); else { const records = el("ul", { class: "search-results" }); list(body.results).forEach((result) => records.append(el("li", { class: "search-result" }, [source({ path: result.path, line: result.line }), el("p", { class: "snippet", text: result.snippet || "" })]))); root.append(records); } const controls = pager("Search results", { limit: body.limit, offset: body.offset, more: body.more }, (value) => openSearch(query, true, value)); if (controls) root.append(controls); openPanel(`Search: ${query}`, root); }
    catch (error) { openPanel("Search unavailable", el("p", { class: "diagnostic", text: error.message })); }
  }
  function relationshipList(title, records) {
    if (!list(records).length) return null; const root = el("div", { class: "relationships" }, [el("strong", {}, [`${title}: `])]);
    list(records).forEach((record, index) => { if (index) root.append(text(", ")); const label = record.label || `${record.milestone_id ? `${record.milestone_id}/` : ""}${record.task_key || "unresolved"}`; if (record.source) root.append(button(label, () => openDocument(record.source.path), { class: "source-button" })); else root.append(text(label)); if (record.state) root.append(text(` (${record.state})`)); }); return root;
  }
  function todoItem(item, group, canAct) {
    const row = el("li", { class: "todo-item" }); const main = el("div", { class: "task-main" }); main.append(el("h4", { text: item.label || item.task_label || (item.milestone_id ? `Milestone ${item.milestone_id}` : "Workflow review") })); main.append(el("p", { class: "meta", text: item.reason || item.notes || "" })); if (item.milestone_id) main.append(el("span", { class: "source", text: `Milestone ${item.milestone_id} ` })); if (item.source) main.append(source(item.source)); const prerequisites = relationshipList("Prerequisites", item.prerequisites); if (prerequisites) main.append(prerequisites); const dependents = relationshipList("Dependents", item.dependents); if (dependents) main.append(dependents); row.append(main);
    if (canAct) { const action = group === "blocked" ? "investigate" : group === "needs_review" ? "review" : group === "waiting" ? "clarify" : "continue"; const label = group === "blocked" ? "Investigate" : group === "needs_review" ? "Review" : group === "waiting" ? "Clarify" : "Continue"; row.append(el("div", { class: "task-actions" }, [button(label, () => prepareFollowUp(action, item), { "aria-label": `${action} ${item.label || item.milestone_id || "workflow"}` })])); }
    return row;
  }
  function renderTodo(data) {
    const body = obj(data); const validated = body.validated !== false; const recommendations = body.recommendations_available !== false; const totals = obj(body.totals); const pages = obj(body.pagination); const anyTasks = todoGroups.some((key) => Number(totals[key] == null ? list(body[key]).length : totals[key]) > 0); $("todo-validation").textContent = validated && recommendations ? "Validated recommendations" : validated && !anyTasks ? "No actionable or review work" : "Evidence available; recommendations withheld"; const root = $("todo-content"); clear(root); if (body.validation_reason) root.append(el("p", { class: "diagnostic", text: body.validation_reason })); if (!recommendations && anyTasks) root.append(el("p", { class: "muted" }, ["Current evidence remains available below. Resolve review or freshness requirements before continuing execution."])); const groups = [["Resume", "resume"], ["Ready", "ready"], ["Waiting", "waiting"], ["Blocked", "blocked"], ["Needs review", "needs_review"]]; groups.forEach(([title, key]) => { const records = list(body[key]); const page = obj(pages[key]); const total = totals[key] == null ? records.length : Number(totals[key]); const section = el("section", { class: "todo-group" }, [el("h3", {}, [title, badge(String(total))])]); if (!records.length) section.append(el("p", { class: "muted" }, ["None"])); else { const ordered = el(key === "ready" ? "ol" : "ul", { class: "todo-list", start: key === "ready" ? Number(page.offset || 0) + 1 : null }); records.forEach((item) => { const canAct = validated && (key === "needs_review" ? Boolean(item.milestone_id || item.source) : ["blocked", "waiting"].includes(key) ? Number(totals.needs_review || 0) === 0 : recommendations); ordered.append(todoItem(item, key, canAct)); }); section.append(ordered); } if (page.offset > 0 || page.more) { const controls = el("div", { class: "pagination", "aria-label": `${title} pagination` }); if (page.offset > 0) controls.append(button("Previous", () => loadTodo(key, Math.max(0, page.offset - page.limit), true))); if (page.more) controls.append(button("Next", () => loadTodo(key, page.offset + page.limit, true))); section.append(controls); } root.append(section); });
  }
  async function loadTodo(group, offset, push) { try { if (group) { state.todoOffsets[group] = Math.max(0, offset || 0); if (push) updateUrl({ [`${group}_offset`]: state.todoOffsets[group] || null }, false); } const query = new URLSearchParams({ limit: "50" }); Object.entries(state.todoOffsets).forEach(([key, value]) => { if (value) query.set(`${key}_offset`, String(value)); }); renderTodo(await api(`/api/todo?${query}`)); } catch (error) { const root = $("todo-content"); clear(root); root.append(el("p", { class: "diagnostic", text: error.message })); } }
  function detailSection(title, children) { return el("section", { class: "detail-section" }, [el("h3", {}, [title]), ...children]); }
  function openPanel(title, content) { const opening = $("detail-panel").hidden; if (opening) state.returnFocus = document.activeElement; $("detail-title").textContent = title; const root = $("detail-content"); clear(root); root.append(content); $("detail-panel").hidden = false; $("backdrop").hidden = false; $("close-detail").focus(); }
  function eventDetails(event) { if (event && typeof event.details_json === "string") { try { return obj(JSON.parse(event.details_json)); } catch (_) { return { raw: event.details_json }; } } return obj(event && event.details); }
  function sourcePreview(value, line) { const content = string(value); if (!line) return el("pre", { class: "source-document" }, [content]); const lines = content.split("\n"); const target = Number(line); if (!Number.isInteger(target) || target < 1 || target > lines.length) return el("div", {}, [el("p", { class: "diagnostic", text: `Referenced line ${line} is outside the current ${lines.length}-line document.` })]); const start = Math.max(1, target - 5); const end = Math.min(lines.length, target + 5); const width = String(end).length; const excerpt = lines.slice(start - 1, end).map((entry, index) => { const number = start + index; return `${number === target ? ">" : " "} ${String(number).padStart(width, " ")} | ${entry}`; }).join("\n"); return el("pre", { class: "source-document", "data-line": target }, [excerpt]); }
  async function openDocument(path, line, push) { state.detailParameter = "document"; if (push !== false) updateUrl(detailUrl("document", path, { line: line || null }), false); try { const body = await api(`/api/document?path=${encodeURIComponent(path)}&live=1`); openPanel(`Source: ${path}${line ? `:${line}` : ""}`, sourcePreview(body.text || "", line)); } catch (error) { openPanel("Source unavailable", el("p", { class: "diagnostic", text: error.message })); } }
  function pager(label, page, handler) { const value = obj(page); const root = el("div", { class: "pagination", "aria-label": `${label} pagination` }); if (value.offset > 0) root.append(button("Previous", () => handler(Math.max(0, value.offset - value.limit)))); if (value.more) root.append(button("Next", () => handler(value.offset + value.limit))); return root.children.length ? root : null; }
  function messageRow(message) { return el("article", { class: "recorded-message" }, [el("strong", { text: message.role || "message" }), " ", badge(message.fidelity || "incomplete"), el("pre", { text: message.text || "" })]); }
  async function openRun(runId, push, offsets) {
    if (!runId) return;
    state.detailParameter = "run";
    if (push !== false) updateUrl(detailUrl("run", runId, {
      event_offset: offsets && offsets.event_offset || null,
      message_offset: offsets && offsets.message_offset || null,
      child_offset: offsets && offsets.child_offset || null
    }), false);
    const pageOffsets = Object.assign({ event_offset: 0, message_offset: 0, child_offset: 0 }, offsets || {});
    try {
      const body = await api(`/api/runs/${encodeURIComponent(runId)}?${new URLSearchParams(pageOffsets)}`);
      const run = obj(body.run); const request = obj(body.request_message); const output = obj(body.output_message); const pagination = obj(body.pagination); const root = el("div");
      root.append(detailSection("Recorded then — request", [el("p", { text: request.text || "Request text was not captured." }), badge(request.fidelity || "incomplete")]));
      root.append(detailSection("Recorded then — output", [el("pre", { text: output.text || "No selected output was recorded." }), badge(output.fidelity || "incomplete")]));
      const conversation = list(body.messages).filter((message) => message.message_id !== request.message_id && message.message_id !== output.message_id);
      const messageControls = pager("Messages", pagination.messages, (value) => openRun(runId, true, { ...pageOffsets, message_offset: value }));
      if (conversation.length || messageControls) {
        const section = detailSection("Recorded clarifications and approvals", conversation.map(messageRow));
        if (messageControls) section.append(messageControls); root.append(section);
      }
      const eventControls = pager("Events", pagination.events, (value) => openRun(runId, true, { ...pageOffsets, event_offset: value }));
      if (list(body.events).length || eventControls) {
        const section = detailSection("Recorded then — observed activity", list(body.events).map((event) => {
          const details = eventDetails(event); const explorer = obj(event.explorer); const summary = event.summary || explorer.summary || details.summary || details.raw || JSON.stringify(details);
          const row = el("article", { class: "recorded-event" }, [el("strong", { text: explorer.phase || event.event_type || "event" }), " — ", summary]);
          list(explorer.message_refs).forEach((reference) => row.append(el("p", { class: "meta", text: `Message reference: ${reference.purpose} (${reference.message_id})` })));
          list(explorer.artifact_refs).forEach((artifact) => { const transition = artifact.old_state || artifact.new_state ? ` ${artifact.old_state || "?"} → ${artifact.new_state || "?"}` : ""; const evidence = el("p", { class: "meta" }, [`${artifact.relationship || "referenced"} ${artifact.namespace || "artifact"} ${artifact.identifier || ""}${transition} `]); if (artifact.path) evidence.append(source(artifact)); row.append(evidence); });
          if (event.status_path) row.append(source({ path: event.status_path })); return row;
        }));
        if (eventControls) section.append(eventControls); root.append(section);
      }
      if (list(body.snapshot_observations).length) root.append(detailSection("Recorded snapshot observations", list(body.snapshot_observations).map((record) => el("p", { text: `${record.observation_state || "observed"}: ${record.source_path || "unknown source"}${record.diagnostic ? ` — ${record.diagnostic}` : ""}` }))));
      const childControls = pager("Child operations", pagination.children, (value) => openRun(runId, true, { ...pageOffsets, child_offset: value }));
      if (list(body.children).length || childControls) {
        const section = detailSection("Child operations", list(body.children).map((child) => el("p", {}, [button(`${child.operation || "run"} — ${child.result || "unfinished"}`, () => openRun(child.run_id), { "aria-label": `Open child run ${child.run_id}` })])));
        if (childControls) section.append(childControls); root.append(section);
      }
      const current = list(body.current_state).map((item) => { if (!item.resolved) return el("p", { class: "diagnostic", text: `${item.kind} ${item.identifier}: ${item.reason || "current location unresolved"}` }); const record = obj(item.record); return el("p", {}, [`${item.kind} ${item.identifier}${record.state ? ` — ${record.state}` : ""} `, record.path ? source({ path: record.path, line: record.line }) : ""]); });
      root.append(detailSection("Current state", current.length ? current : [el("p", { class: "muted", text: "No referenced current milestone or task could be resolved." })])); openPanel(run.operation || "Run details", root);
    } catch (error) { openPanel("Run details unavailable", el("p", { class: "diagnostic", text: error.message })); }
  }
  async function prepareFollowUp(action, item) {
    try { showNotice("Validating the current source state…"); const body = await api("/api/follow-up", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ action, milestone_id: item.milestone_id, task_id: item.explicit_id, task_label: item.label || item.task_label, source: item.source }) }); showNotice(""); const root = el("div", {}, [el("p", { class: "muted", text: body.validation_note || "Prepared from validated current source state. Copying does not execute work." })]); const prompt = el("pre", { class: "prompt", tabindex: "0" }, [body.prompt || "No prompt was prepared."]); root.append(prompt); root.append(el("div", { class: "prompt-actions" }, [button("Copy prompt", async () => { try { await navigator.clipboard.writeText(body.prompt || ""); showNotice("Prompt copied."); } catch (_) { prompt.focus(); showNotice("Clipboard access is unavailable. Select the prompt text and copy it manually."); } }), button("Select prompt", () => { const range = document.createRange(); range.selectNodeContents(prompt); const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range); prompt.focus(); })])); openPanel(`${action.replace("_", " ")} follow-up`, root); }
    catch (error) { showNotice(""); openPanel("Follow-up unavailable", el("p", { class: "diagnostic", text: error.message })); }
  }
  async function refresh() { try { showNotice("Refreshing the derived index…"); const body = await api("/api/refresh", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: "{}" }); showNotice(body.message || "Project refreshed."); await loadCurrent(); } catch (error) { showNotice(`Refresh failed: ${error.message}`); } }
  async function loadCurrent() {
    try { const body = await api("/api/health"); const project = obj(body.project || body); state.generation = body.index && body.index.generation || null; state.activity = body.activity || null; $("project-name").textContent = project.name || project.project_name || "Tabilet project"; $("project-context").textContent = [project.branch, project.git_head, body.index && body.index.refreshed_at ? `Indexed ${body.index.refreshed_at}` : "Index not refreshed"].filter(Boolean).join(" · "); $("refresh-project").textContent = body.setup_required ? "Create index" : "Refresh project"; }
    catch (error) { $("project-name").textContent = "Tabilet Explorer"; showDiagnostics([error.message]); }
    if (state.view === "overview") await loadOverview(); else if (state.view === "timeline") await loadTimeline(new URL(location.href).searchParams.get("cursor")); else await loadTodo();
  }
  function closePanel(updateHistory) { $("detail-panel").hidden = true; $("backdrop").hidden = true; if (updateHistory !== false && state.detailParameter) updateUrl(detailUrl(state.detailParameter, null), true); state.detailParameter = null; if (state.returnFocus && typeof state.returnFocus.focus === "function") state.returnFocus.focus(); }
  function restoreUrlState() {
    const params = new URLSearchParams(location.search); state.timelineFilters = { operation: params.get("operation") || "", outcome: params.get("outcome") || "", milestone: params.get("milestone") || "", since: params.get("since") || "", until: params.get("until") || "", order: params.get("order") || "newest" }; todoGroups.forEach((key) => { state.todoOffsets[key] = Math.max(0, Number(params.get(`${key}_offset`)) || 0); }); $("timeline-operation").value = state.timelineFilters.operation; $("timeline-outcome").value = state.timelineFilters.outcome; $("timeline-milestone").value = state.timelineFilters.milestone; $("timeline-since").value = state.timelineFilters.since; $("timeline-until").value = state.timelineFilters.until; $("timeline-order").value = state.timelineFilters.order; $("global-search").value = params.get("search") || ""; setView(params.get("view") || "overview", true); if (params.get("run")) openRun(params.get("run"), false, { event_offset: Number(params.get("event_offset")) || 0, message_offset: Number(params.get("message_offset")) || 0, child_offset: Number(params.get("child_offset")) || 0 }); else if (params.get("document")) openDocument(params.get("document"), Number(params.get("line")) || null, false); else if (params.get("search")) openSearch(params.get("search"), false, Number(params.get("search_offset")) || 0); else closePanel(false);
  }
  function setup() {
    restoreUrlState(); document.querySelectorAll("[data-view]").forEach((link) => link.addEventListener("click", (event) => { event.preventDefault(); setView(link.dataset.view, false); })); window.addEventListener("popstate", restoreUrlState); document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !$("detail-panel").hidden) { event.preventDefault(); closePanel(true); } }); $("close-detail").addEventListener("click", () => closePanel(true)); $("backdrop").addEventListener("click", () => closePanel(true)); $("refresh-project").addEventListener("click", refresh); $("timeline-operation").addEventListener("change", () => { state.timelineFilters.operation = $("timeline-operation").value; updateUrl({ operation: state.timelineFilters.operation, cursor: null }, true); loadTimeline(); }); $("timeline-outcome").addEventListener("change", () => { state.timelineFilters.outcome = $("timeline-outcome").value; updateUrl({ outcome: state.timelineFilters.outcome, cursor: null }, true); loadTimeline(); }); $("timeline-milestone").addEventListener("change", () => { state.timelineFilters.milestone = $("timeline-milestone").value.trim(); updateUrl({ milestone: state.timelineFilters.milestone, cursor: null }, true); loadTimeline(); }); for (const name of ["since", "until"]) { $(`timeline-${name}`).addEventListener("change", () => { state.timelineFilters[name] = $(`timeline-${name}`).value.trim(); updateUrl({ [name]: state.timelineFilters[name], cursor: null }, true); loadTimeline(); }); } $("timeline-order").addEventListener("change", () => { state.timelineFilters.order = $("timeline-order").value; updateUrl({ order: state.timelineFilters.order === "newest" ? null : state.timelineFilters.order, cursor: null }, true); loadTimeline(); }); $("global-search").addEventListener("keydown", (event) => { if (event.key === "Enter" && event.currentTarget.value.trim()) { event.preventDefault(); openSearch(event.currentTarget.value.trim()); } }); loadCurrent();
    const poll = async () => { if (document.hidden) return; try { const body = await api("/api/health"); const generation = body.index && body.index.generation || null; const activity = body.activity || null; if (activityChanged(state.generation, state.activity, generation, activity)) await loadCurrent(); state.generation = generation; state.activity = activity; } catch (_) {} };
    state.poll = window.setInterval(poll, 5000); document.addEventListener("visibilitychange", () => { if (!document.hidden) loadCurrent(); });
  }
  window.TabiletExplorerTest = { activityChanged, renderTodo, timelineEntry, restoreUrlState, updateUrl, detailUrl, sourcePreview, closePanel, openPanel, prepareFollowUp };
  document.addEventListener("DOMContentLoaded", setup);
}());
