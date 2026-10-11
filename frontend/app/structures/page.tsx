"use client";

import { useEffect, useRef, useState } from "react";
import { Braces, GitBranch, Layers3 } from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";
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
  tree: {
    inorder: number[];
    preorder: number[];
    postorder: number[];
    searchValue: number;
    searchFound: boolean;
  };
  graph: { bfs: string[]; dfs: string[] };
};

export default function Structures() {
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
  const [structureMessage, setStructureMessage] = useState("");

  useEffect(() => {
    fetch("/api/demo", { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("The operations demo is unavailable.");
        return response.json();
      })
      .then((data: Demo) => {
        setDemo(data);
        linkedList.current.load(data.linkedList || []);
        setRecords(linkedList.current.traverse());
        actionStack.current = new LinkedStack<string>();
        for (const action of [...(data.stackActions || [])].reverse()) {
          actionStack.current.push(action);
        }
        setStack(actionStack.current.toArray());
        checkInQueue.current = new LinkedQueue<string>();
        for (const match of data.queueItems || []) checkInQueue.current.enqueue(match);
        setQueue(checkInQueue.current.toArray());
      })
      .catch((error: Error) => setStructureMessage(error.message));
  }, []);

  function insertParticipant() {
    const id = participantId.trim();
    const name = participantName.trim();
    if (!id || !name) {
      setStructureMessage("Enter a participant ID and name before inserting.");
      return;
    }
    if (linkedList.current.traverse().some((record) => record.student_id === id)) {
      setStructureMessage("That participant ID is already in the list.");
      return;
    }
    linkedList.current.insertAtEnd({ student_id: id, name, game: "Practice record" });
    setRecords(linkedList.current.traverse());
    setParticipantName("");
    setStructureMessage("Participant added to the list.");
  }

  function deleteParticipant() {
    const removed = linkedList.current.deleteByStudentId(participantId.trim());
    setRecords(linkedList.current.traverse());
    setStructureMessage(
      removed ? "Removed " + removed.name + " from the list." : "No participant has that number.",
    );
  }

  function traverseParticipants() {
    const ids = linkedList.current.traverse().map((record) => record.student_id);
    setStructureMessage(ids.length ? "Traversal: " + ids.join(" → ") : "The participant list is empty.");
  }

  function pushAction() {
    actionStack.current.push("Score update ST00" + (stack.length + 1));
    setStack(actionStack.current.toArray());
    setStructureMessage("Added a score update to recent actions.");
  }

  function popAction() {
    const removed = actionStack.current.pop();
    setStack(actionStack.current.toArray());
    setStructureMessage(removed ? "Removed latest action: " + removed : "There are no recent actions.");
  }

  function enqueueMatch() {
    checkInQueue.current.enqueue("New match check-in");
    setQueue(checkInQueue.current.toArray());
    setStructureMessage("Added the match to the end of the check-in line.");
  }

  function dequeueMatch() {
    const removed = checkInQueue.current.dequeue();
    setQueue(checkInQueue.current.toArray());
    setStructureMessage(removed ? "Next in line: " + removed : "The check-in line is empty.");
  }

  async function evaluate() {
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
      setResult("The expression service is unavailable.");
    }
  }

  return (
    <>
      <PageTitle
        eyebrow="TOURNAMENT OPERATIONS"
        title="Everything behind"
        accent="every game."
        description="Try the simple tools that keep game day organized."
        action="Open leaderboard tools"
        href="/algorithms"
      />

      <div className="phase-heading">
        <div>
          <div className="eyebrow">PARTICIPANT RECORDS</div>
          <h2>Manage the participant list</h2>
        </div>
        <Tag>Add · remove · view</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Participant list" aside={<Tag tone="green">HEAD → TAIL</Tag>} />
          <p className="muted-copy">
            Try adding a sample participant, removing one, or viewing the list in order.
          </p>
          <div className="linked-track">
            {records.map((record, index) => (
              <div className="linked-unit" key={record.student_id}>
                <div className="linked-node">
                  <small>{record.student_id}</small>
                  <b>{record.name}</b>
                  <span>{record.game}</span>
                </div>
                {index < records.length - 1 && <i className="link-arrow">→</i>}
              </div>
            ))}
            {!records.length && <div className="empty-state">No participant records yet.</div>}
          </div>
          <div className="structure-inputs">
            <input
              className="demo-input"
              value={participantId}
              onChange={(event) => setParticipantId(event.target.value)}
              placeholder="Participant number"
              aria-label="Participant number"
            />
            <input
              className="demo-input"
              value={participantName}
              onChange={(event) => setParticipantName(event.target.value)}
              placeholder="Participant name"
              aria-label="Name for new record"
            />
          </div>
          <div className="structure-buttons">
            <button onClick={insertParticipant}>Add participant</button>
            <button onClick={deleteParticipant}>Remove participant</button>
            <button onClick={traverseParticipants}>Show participants</button>
          </div>
          <div className="structure-meta">
            <span><GitBranch size={14} /> Participant records</span>
            <b>{records.length} participants</b>
          </div>
        </Card>

        <Card>
          <SectionHeading title="Game day flow" aside={<Tag tone="blue">GAME DAY</Tag>} />
          <div className="mini-structure">
            <div>
              <div className="eyebrow">RECENT ACTIONS</div>
              <div className="stack-card">
                <span className="top-label">LATEST</span>
                <b>{stack[0] || "No recent actions"}</b>
              </div>
              <div className="structure-buttons">
                <button onClick={pushAction}>Add recent action</button>
                <button onClick={popAction}>Undo latest</button>
              </div>
            </div>
            <div>
              <div className="eyebrow">CHECK-IN LINE</div>
              <div className="queue-card">
                <span className="top-label">NEXT</span>
                <b>{queue[0] || "No one waiting"}</b>
              </div>
              <div className="structure-buttons">
                <button onClick={enqueueMatch}>Add to line</button>
                <button onClick={dequeueMatch}>Next in line</button>
              </div>
            </div>
          </div>
          {structureMessage && <div className="form-message">{structureMessage}</div>}
          <div className="expression-tool">
            <label><Braces size={15} /> Quick score calculator</label>
            <input value={expr} onChange={(event) => setExpr(event.target.value)} />
            <button onClick={evaluate}>Calculate</button>
            <b>{result}</b>
          </div>
        </Card>
      </div>

      <div className="phase-heading second-phase">
        <div>
          <div className="eyebrow">SCORES & GAME DAY</div>
          <h2>Explore scores and game day</h2>
        </div>
        <Tag>Scores · Venue map</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Score summary" aside={<Tag>Sorted scores</Tag>} />
          <p className="muted-copy">
            These views show the same scores in three useful orders, with a quick check for a score.
          </p>
          <div className="traversal-list">
            {[
              ["LOW TO HIGH", demo?.tree.inorder],
              ["FIRST SCORE FIRST", demo?.tree.preorder],
              ["RELATED SCORES FIRST", demo?.tree.postorder],
            ].map(([label, values]: any) => (
              <div className="traversal-row" key={label}>
                <b>{label}</b>
                <span>{(values || []).join("  /  ") || "Loading..."}</span>
              </div>
            ))}
          </div>
          <div className="traversal-row compact">
            <b>SCORE CHECK</b>
            <span>
              {demo ? (demo.tree.searchFound ? "Found " : "Not found ") + demo.tree.searchValue : "Loading..."}
            </span>
          </div>
        </Card>
        <Card>
          <SectionHeading title="Places around the venue" aside={<Tag tone="green">VENUE GUIDE</Tag>} />
          <p className="muted-copy">
            See which event spaces are connected and two ways to explore the venue.
          </p>
          <div className="graph-map">
            <div className="graph-edge edge-one" />
            <div className="graph-edge edge-two" />
            <div className="graph-edge edge-three" />
            <div className="graph-edge edge-four" />
            <div className="graph-edge edge-five" />
            <span className="graph-vertex v-hub">Arena</span>
            <span className="graph-vertex v-chess">Chess Hall</span>
            <span className="graph-vertex v-court">Court A</span>
            <span className="graph-vertex v-table">Table Tennis</span>
          </div>
          <div className="traversal-row compact"><b>ROUTE A</b><span>{demo?.graph.bfs.join(" → ") || "Loading..."}</span></div>
          <div className="traversal-row compact"><b>ROUTE B</b><span>{demo?.graph.dfs.join(" → ") || "Loading..."}</span></div>
        </Card>
      </div>
      <div className="phase-bridge">
        <Layers3 size={18} />
        <span>Leaderboard and schedule tools use the same tournament details.</span>
        <a href="/algorithms">Explore leaderboard tools →</a>
      </div>
    </>
  );
}
