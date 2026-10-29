"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Braces, GitBranch, Info, Layers3 } from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";
import { useRole } from "../components/role";
import {
  LinkedQueue,
  LinkedStack,
  ParticipantLinkedList,
  type ParticipantRecord,
} from "../components/structures-demo";

type Demo = {
  linkedList: ParticipantRecord[];
  stackActions: string[];
  queueItems: string[];
  tree: { inorder: number[]; preorder: number[]; postorder: number[]; searchValue: number; searchFound: boolean };
  graph: { bfs: string[]; dfs: string[] };
};

const venueNames = [
  "Cricket Ground",
  "Basketball Court",
  "Volleyball Court",
  "Badminton Court",
  "Indoor Sports Complex",
  "Tennis Court",
  "Athletics Track",
];
const venueConnections: [string, string][] = [
  ["Indoor Sports Complex", "Cricket Ground"],
  ["Indoor Sports Complex", "Athletics Track"],
  ["Indoor Sports Complex", "Basketball Court"],
  ["Indoor Sports Complex", "Volleyball Court"],
  ["Indoor Sports Complex", "Badminton Court"],
  ["Indoor Sports Complex", "Tennis Court"],
  ["Cricket Ground", "Athletics Track"],
  ["Basketball Court", "Volleyball Court"],
  ["Volleyball Court", "Badminton Court"],
  ["Badminton Court", "Tennis Court"],
  ["Athletics Track", "Tennis Court"],
];

function findVenueRoutes(start: string, end: string) {
  const connections = new Map(venueNames.map((name) => [name, [] as string[]]));
  for (const [first, second] of venueConnections) {
    connections.get(first)?.push(second);
    connections.get(second)?.push(first);
  }
  const routes: string[][] = [];
  function visit(current: string, route: string[]) {
    if (current === end) { routes.push(route); return; }
    for (const next of connections.get(current) || []) {
      if (!route.includes(next)) visit(next, [...route, next]);
    }
  }
  visit(start, [start]);
  return routes.sort((first, second) => first.length - second.length);
}

export default function Structures() {
  const { role, loading: roleLoading } = useRole();
  const isAdmin = role === "admin";
  const linkedList = useRef(new ParticipantLinkedList());
  const actionStack = useRef(new LinkedStack<string>());
  const checkInQueue = useRef(new LinkedQueue<string>());
  const [demo, setDemo] = useState<Demo | null>(null);
  const [records, setRecords] = useState<ParticipantRecord[]>([]);
  const [participantId, setParticipantId] = useState("");
  const [participantName, setParticipantName] = useState("");
  const [expr, setExpr] = useState("1200 + 40 * 2");
  const [result, setResult] = useState("");
  const [stack, setStack] = useState<string[]>([]);
  const [queue, setQueue] = useState<string[]>([]);
  const [checkInName, setCheckInName] = useState("");
  const [message, setMessage] = useState("");
  const [venueStart, setVenueStart] = useState("Indoor Sports Complex");
  const [venueEnd, setVenueEnd] = useState("Cricket Ground");
  const venueRoutes = findVenueRoutes(venueStart, venueEnd);

  useEffect(() => {
    fetch("/api/demo", { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("The practice examples are unavailable.");
        return response.json();
      })
      .then((data: Demo) => {
        setDemo(data);
        linkedList.current.load(data.linkedList || []);
        setRecords(linkedList.current.traverse());
        actionStack.current = new LinkedStack<string>();
        for (const action of [...(data.stackActions || [])].reverse()) actionStack.current.push(action);
        setStack(actionStack.current.toArray());
        checkInQueue.current = new LinkedQueue<string>();
        for (const item of data.queueItems || []) checkInQueue.current.enqueue(item);
        setQueue(checkInQueue.current.toArray());
      })
      .catch((error: Error) => setMessage(error.message));
  }, []);

  function addParticipant() {
    const id = participantId.trim();
    const name = participantName.trim();
    if (!id || !name) return setMessage("Enter both a participant number and name.");
    if (linkedList.current.traverse().some((record) => record.student_id === id)) return setMessage("That participant number is already in this practice list.");
    linkedList.current.insertAtEnd({ student_id: id, name, game: "Practice entry" });
    setRecords(linkedList.current.traverse());
    setParticipantName("");
    setMessage("Added to the practice list. This does not create a tournament account.");
  }

  function removeParticipant() {
    const removed = linkedList.current.deleteByStudentId(participantId.trim());
    setRecords(linkedList.current.traverse());
    setMessage(removed ? "Removed " + removed.name + " from the practice list." : "No matching number was found.");
  }

  function showListOrder() {
    const ids = linkedList.current.traverse().map((record) => record.student_id);
    setMessage(ids.length ? "List order: " + ids.join(" → ") : "The practice list is empty.");
  }

  function pushAction() {
    actionStack.current.push("Score update " + (stack.length + 1));
    setStack(actionStack.current.toArray());
    setMessage("Added a recent activity item.");
  }

  function popAction() {
    const removed = actionStack.current.pop();
    setStack(actionStack.current.toArray());
    setMessage(removed ? "Removed the latest activity: " + removed : "There is no activity to undo.");
  }

  function addToLine() {
    const name = checkInName.trim();
    if (!name) return setMessage("Enter a player or team name first.");
    checkInQueue.current.enqueue(name);
    setQueue(checkInQueue.current.toArray());
    setCheckInName("");
    setMessage(name + " joined the check-in line.");
  }

  function serveNext() {
    const removed = checkInQueue.current.dequeue();
    setQueue(checkInQueue.current.toArray());
    setMessage(removed ? "Next in line was served: " + removed : "The check-in line is empty.");
  }

  async function calculate() {
    try {
      const response = await fetch("/api/expression", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ expression: expr }),
      });
      const data = await response.json();
      setResult(data.error || String(data.result));
    } catch {
      setResult("The calculator is unavailable.");
    }
  }

  return (
    <>
      <PageTitle
        eyebrow="GAME DAY TOOLS"
        title="Keep game day"
        accent="moving smoothly."
        description="Manage the game-day roster, player check-in, score desk, and event-space guide."
        action="Plan the tournament day"
        href="/algorithms"
      />

      <div className="tools-note" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--blue-soft)", borderColor: "var(--blue)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Info size={19} color="var(--blue)" />
          <span style={{ color: "var(--ink)" }}>Looking for player lineups, score calculator, championship brackets, and interactive game flow?</span>
        </div>
        <Link href="/lab" className="button primary-button" style={{ fontSize: 12 }}>
          Open Search & Find
        </Link>
      </div>

      <div className="phase-heading tools-section">
        <div><div className="eyebrow">ROSTER DESK</div><h2>Review game participants</h2><p>See submitted game choices and try managing a temporary game-day list.</p></div>
        <Tag>Participant list</Tag>
      </div>
      <Card className="tools-card">
        <SectionHeading title="Participant game choices" aside={<Tag tone="green">{records.length} entries</Tag>} />
        <div className="linked-track">
          {records.map((record, index) => (
            <div className="linked-unit" key={record.student_id + ":" + record.game}>
              <div className="linked-node"><small>{record.student_id}</small><b>{record.name}</b><span>{record.game}</span></div>
              {index < records.length - 1 && <i className="link-arrow">→</i>}
            </div>
          ))}
          {!records.length && <div className="empty-state">No game choices have been submitted yet. Add a temporary example below to try the list.</div>}
        </div>
        {roleLoading ? (
          <div className="tools-note inline">Checking your access…</div>
        ) : isAdmin ? (
          <>
            <div className="tools-note inline">Admin practice controls. Changes here are temporary; manage real student accounts from the Participants page.</div>
            <div className="structure-inputs">
              <input className="demo-input" value={participantId} onChange={(event) => setParticipantId(event.target.value)} placeholder="Player ID" aria-label="Player ID" />
              <input className="demo-input" value={participantName} onChange={(event) => setParticipantName(event.target.value)} placeholder="Participant name" aria-label="Participant name" />
            </div>
            <div className="structure-buttons">
              <button onClick={addParticipant}>Add to practice list</button>
              <button onClick={removeParticipant}>Remove from practice list</button>
            </div>
          </>
        ) : (
          <div className="tools-note inline">This roster is view-only for students. Only an administrator can add or remove participants.</div>
        )}
        <div className="structure-buttons">
          <button onClick={showListOrder}>Review roster order</button>
        </div>
      </Card>

      <div className="phase-heading tools-section">
        <div><div className="eyebrow">GAME-DAY OPERATIONS</div><h2>Score desk and check-in</h2><p>Keep a short activity log and call players in the order they arrived.</p></div>
        <Tag>Activity and check-in</Tag>
      </div>
      <div className="two-column tools-grid">
        <Card>
          <SectionHeading title="Score desk activity" aside={<Tag>Latest update</Tag>} />
          <p className="muted-copy">Practice logging score-desk updates and undoing the most recent one.</p>
          <div className="stack-card"><span className="top-label">LATEST UPDATE</span><b>{stack[0] || "No recent updates"}</b></div>
          <div className="structure-buttons"><button onClick={pushAction}>Log a score update</button><button onClick={popAction}>Undo latest update</button></div>
        </Card>
        <Card>
          <SectionHeading title="Player check-in line" aside={<Tag>Next player first</Tag>} />
          <p className="muted-copy">Add a player or team, then call the next entry to the check-in desk.</p>
          <div className="queue-card"><span className="top-label">UP NEXT</span><b>{queue[0] || "No players waiting"}</b></div>
          <div className="structure-inputs"><input className="demo-input" value={checkInName} onChange={(event) => setCheckInName(event.target.value)} placeholder="Player or team name" aria-label="Player or team name" /></div>
          <div className="structure-buttons"><button onClick={addToLine}>Join check-in line</button><button onClick={serveNext}>Call next player</button></div>
        </Card>
      </div>

      <div className="phase-heading tools-section">
        <div><div className="eyebrow">SCORE DESK</div><h2>Check points and score totals</h2><p>Calculate a points total and review scores from different angles.</p></div>
        <Tag>Score examples</Tag>
      </div>
      <div className="two-column tools-grid">
        <Card>
          <SectionHeading title="Points calculator" aside={<Braces size={18} />} />
          <p className="muted-copy">Work out a score or points adjustment using numbers, brackets, and basic arithmetic.</p>
          <div className="expression-tool">
            <input aria-label="Arithmetic expression" value={expr} onChange={(event) => setExpr(event.target.value)} />
            <button onClick={calculate}>Calculate</button>
          </div>
          {result && <div className="tools-result" role="status">Answer: <b>{result}</b></div>}
        </Card>
        <Card>
          <SectionHeading title="Scoreboard review" aside={<Tag>Current points</Tag>} />
          <p className="muted-copy">Review participant point values from low to high, or open the extra views for other score-review orders.</p>
          <div className="tools-score-order"><span>Low to high</span><b>{demo?.tree.inorder.join(" · ") || "Loading examples…"}</b></div>
          <details className="tools-details">
            <summary>See other score-review views</summary>
            <div className="traversal-row compact"><b>Start at each parent first</b><span>{demo?.tree.preorder.join(" · ") || "—"}</span></div>
            <div className="traversal-row compact"><b>Visit children before parent</b><span>{demo?.tree.postorder.join(" · ") || "—"}</span></div>
            <div className="tools-result">Example lookup: {demo ? (demo.tree.searchFound ? "Found " : "Did not find ") + demo.tree.searchValue : "Loading…"}</div>
          </details>
        </Card>
      </div>

      <div className="phase-heading tools-section">
        <div><div className="eyebrow">EVENT SPACES</div><h2>Plan movement around the venue</h2><p>Use the sample map to see how event areas connect and review possible routes.</p></div>
        <Tag>Sample map</Tag>
      </div>
      <Card className="tools-card">
        <div className="tools-note inline"><Info size={18} /><span>This is a sample venue layout for planning movement. Scheduled game locations are shown on the Tournaments & games page.</span></div>
        <div className="venue-demo-layout">
          <div className="graph-map" aria-label="Sample venue map" style={{ display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "center", alignItems: "center", minHeight: 180, padding: 16 }}>
            {venueNames.map((v) => {
              const isStart = venueStart === v;
              const isEnd = venueEnd === v;
              const onShortest = venueRoutes[0]?.includes(v);
              return (
                <span
                  key={v}
                  className={"graph-vertex " + (isStart ? "is-start " : "") + (isEnd ? "is-end" : "")}
                  style={{
                    position: "static",
                    cursor: "pointer",
                    boxShadow: onShortest ? "0 0 12px rgba(89, 111, 224, 0.4)" : undefined,
                    borderColor: isStart ? "var(--green)" : isEnd ? "var(--red)" : onShortest ? "var(--blue)" : undefined,
                  }}
                  onClick={() => {
                    if (venueStart === v) return;
                    setVenueEnd(v);
                  }}
                >
                  {v}
                </span>
              );
            })}
          </div>
          <div className="venue-map-legend"><span><i className="legend-start" /> Starting place</span><span><i className="legend-end" /> Destination</span></div>
          <div className="venue-route-controls">
            <label>Starting place
              <select value={venueStart} onChange={(event) => setVenueStart(event.target.value)}>
                {venueNames.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
            </label>
            <label>Destination
              <select value={venueEnd} onChange={(event) => setVenueEnd(event.target.value)}>
                {venueNames.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
            </label>
          </div>
          <div className="venue-routes" aria-live="polite">
            <div className="route-list-heading"><b>Routes between your places</b><span>{venueRoutes.length} {venueRoutes.length === 1 ? "route" : "routes"} found</span></div>
            {venueRoutes.map((route, index) => (
              <article className="route-card" key={route.join("-")}>
                <div><span className="route-label">{index === 0 ? "SHORTEST ROUTE" : "ALTERNATIVE ROUTE " + index}</span><small>{route.length - 1} {route.length - 1 === 1 ? "connection" : "connections"}</small></div>
                <b>{route.join(" -> ")}</b>
              </article>
            ))}
            {!venueRoutes.length && <div className="empty-state">There is no connected route between those places.</div>}
          </div>
        </div>
      </Card>

      {message && <div className="form-message tools-message" role="status">{message}</div>}
      <div className="phase-bridge"><Layers3 size={18} /><span>Manage live schedules and official standings from the tournament and leaderboard pages.</span><a href="/tournament">Open tournaments →</a></div>
    </>
  );
}
