"use client";
import { useEffect, useState } from "react";
import { Activity, CheckCircle2, Clock3, Flag, Trophy } from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";
export default function ActivityPage(){
 const [data,setData]=useState<any>(null),[error,setError]=useState("");
 useEffect(()=>{fetch("http://localhost:8000/api/dashboard").then(r=>r.json()).then(setData).catch(()=>setError("Start the Python API to see current tournament activity."))},[]);
 const rows=data?.matches||[];
 return <><PageTitle eyebrow="TOURNAMENT PULSE" title="Activity" accent="from every arena." description="A live view of fixtures and the data structure events driving the tournament." action="Open match schedule" href="/tournament"/>{error&&<div className="notice">{error}</div>}
 <div className="stat-grid compact-stats"><Card className="stat-card"><span className="stat-icon blue"><Activity size={18}/></span><span className="stat-label">Tracked fixtures</span><b className="stat-value">{rows.length}</b><small className="stat-caption">Current schedule</small></Card><Card className="stat-card"><span className="stat-icon green"><CheckCircle2 size={18}/></span><span className="stat-label">API status</span><b className="stat-value">{data?"Online":"Loading"}</b><small className="stat-caption">Local Python service</small></Card><Card className="stat-card"><span className="stat-icon gold"><Flag size={18}/></span><span className="stat-label">Active rounds</span><b className="stat-value">{data?.stats?.matchesToday||0}</b><small className="stat-caption">Across all arenas</small></Card></div>
 <Card><SectionHeading label="LATEST TOURNAMENT EVENTS" title="Match timeline" aside={<Tag tone="green">LIVE FEED</Tag>}/><div className="timeline-list">{rows.map((m:any,i:number)=><article className="timeline-event" key={m.name}><div className="timeline-marker">{i===0?<Trophy size={15}/>:<Clock3 size={15}/>}</div><div className="timeline-body"><div className="timeline-meta"><span>{String(m.start).padStart(2,"0")}:00 - {String(m.end).padStart(2,"0")}:00</span><Tag tone={i===0?"green":"blue"}>{i===0?"In progress":"Scheduled"}</Tag></div><h3>{m.name}</h3><p>{["Aarav Sharma vs. Rohan Das","Mira Patel vs. Nisha Kapoor","Kabir Nair vs. Dev Shah","Ananya Rao vs. Meera Iyer"][i%4]}</p><small>Venue: {["Arena Chess Hall","Court A","Table Tennis Hall","Arena Chess Hall"][i%4]}</small></div></article>)}</div>{!rows.length&&<div className="empty-state">No activity available.</div>}</Card>
 </>;
}
