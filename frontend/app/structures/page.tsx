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
    setStructureMessage("Inserted the participant at the tail of the linked list.");
  }

  function deleteParticipant() {
    const removed = linkedList.current.deleteByStudentId(participantId.trim());
    setRecords(linkedList.current.traverse());
    setStructureMessage(
      removed ? "Deleted " + removed.name + " from the linked list." : "No record has that participant ID.",
    );
  }

  function traverseParticipants() {
    const ids = linkedList.current.traverse().map((record) => record.student_id);
    setStructureMessage(ids.length ? "Traversal: " + ids.join(" → ") : "The participant list is empty.");
  }

  function pushAction() {
    actionStack.current.push("Score update ST00" + (stack.length + 1));
    setStack(actionStack.current.toArray());
    setStructureMessage("Pushed a score update onto the action stack.");
  }

  function popAction() {
    const removed = actionStack.current.pop();
    setStack(actionStack.current.toArray());
    setStructureMessage(removed ? "Popped: " + removed : "The action stack is empty.");
  }

  function enqueueMatch() {
    checkInQueue.current.enqueue("New match check-in");
    setQueue(checkInQueue.current.toArray());
    setStructureMessage("Enqueued a match at the back of the line.");
  }

  function dequeueMatch() {
    const removed = checkInQueue.current.dequeue();
    setQueue(checkInQueue.current.toArray());
    setStructureMessage(removed ? "Dequeued: " + removed : "The match queue is empty.");
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
        title="The system behind"
        accent="every match."
        description="See how participant records, score lookups, check-ins, and venue routes work."
        action="Open standings tools"
        href="/algorithms"
      />

      <div className="phase-heading">
        <div>
          <div className="eyebrow">PARTICIPANT RECORDS</div>
          <h2>Manage the roster as a linked list</h2>
        </div>
        <Tag>Insert · delete · traverse</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Participant list" aside={<Tag tone="green">HEAD → TAIL</Tag>} />
          <p className="muted-copy">
            The records begin with current game choices. Insert a practice record, remove by ID, or traverse the list in order.
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
              placeholder="Participant ID"
              aria-label="Participant ID"
            />
            <input
              className="demo-input"
              value={participantName}
              onChange={(event) => setParticipantName(event.target.value)}
              placeholder="Name for new record"
              aria-label="Name for new record"
            />
          </div>
          <div className="structure-buttons">
            <button onClick={insertParticipant}>Insert at tail</button>
            <button onClick={deleteParticipant}>Delete by ID</button>
            <button onClick={traverseParticipants}>Traverse list</button>
          </div>
          <div className="structure-meta">
            <span><GitBranch size={14} /> Singly linked records</span>
            <b>{records.length} nodes</b>
          </div>
        </Card>

        <Card>
          <SectionHeading title="Match operations" aside={<Tag tone="blue">LINKED NODES</Tag>} />
          <div className="mini-structure">
            <div>
              <div className="eyebrow">ACTION HISTORY · LIFO</div>
              <div className="stack-card">
                <span className="top-label">TOP</span>
                <b>{stack[0] || "Stack is empty"}</b>
              </div>
              <div className="structure-buttons">
                <button onClick={pushAction}>Push action</button>
                <button onClick={popAction}>Pop</button>
              </div>
            </div>
            <div>
              <div className="eyebrow">MATCH CHECK-IN · FIFO</div>
              <div className="queue-card">
                <span className="top-label">FRONT</span>
                <b>{queue[0] || "Queue is empty"}</b>
              </div>
              <div className="structure-buttons">
                <button onClick={enqueueMatch}>Enqueue match</button>
                <button onClick={dequeueMatch}>Dequeue</button>
              </div>
            </div>
          </div>
          {structureMessage && <div className="form-message">{structureMessage}</div>}
          <div className="expression-tool">
            <label><Braces size={15} /> Evaluate arithmetic with an operator stack</label>
            <input value={expr} onChange={(event) => setExpr(event.target.value)} />
            <button onClick={evaluate}>Evaluate</button>
            <b>{result}</b>
          </div>
        </Card>
      </div>

      <div className="phase-heading second-phase">
        <div>
          <div className="eyebrow">SCORE INDEX & VENUE ROUTES</div>
          <h2>Look up standings and navigate the arena</h2>
        </div>
        <Tag>Binary search tree · Graph</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Score search tree" aside={<Tag>Ordered score index</Tag>} />
          <p className="muted-copy">
            Scores are stored in a binary search tree. Inorder lists them in order; search follows the tree branches.
          </p>
          <div className="traversal-list">
            {[
              ["INORDER", demo?.tree.inorder],
              ["PREORDER", demo?.tree.preorder],
              ["POSTORDER", demo?.tree.postorder],
            ].map(([label, values]: any) => (
              <div className="traversal-row" key={label}>
                <b>{label}</b>
                <span>{(values || []).join("  /  ") || "Loading..."}</span>
              </div>
            ))}
          </div>
          <div className="traversal-row compact">
            <b>BST SEARCH</b>
            <span>
              {demo ? (demo.tree.searchFound ? "Found " : "Not found ") + demo.tree.searchValue : "Loading..."}
            </span>
          </div>
        </Card>
        <Card>
          <SectionHeading title="Venue connections" aside={<Tag tone="green">ADJACENCY LIST</Tag>} />
          <p className="muted-copy">
            Each arena location stores its connected venues. Breadth-first and depth-first traversals show routes through the graph.
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
          <div className="traversal-row compact"><b>BFS</b><span>{demo?.graph.bfs.join(" → ") || "Loading..."}</span></div>
          <div className="traversal-row compact"><b>DFS</b><span>{demo?.graph.dfs.join(" → ") || "Loading..."}</span></div>
        </Card>
      </div>
      <div className="phase-bridge">
        <Layers3 size={18} />
        <span>Search and scheduling tools use these same tournament records.</span>
        <a href="/algorithms">Explore standings tools →</a>
      </div>
    </>
  );
}
