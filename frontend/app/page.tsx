"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {ArrowRight,CheckCircle2,ClipboardList,Gamepad2,Medal,Trophy,Users} from "lucide-react";
import {Card,PageTitle,Tag} from "./components/ui";
import {useRole} from "./components/role";

type Game={game_id:string;name:string;category:string;venue:string};
type Player={student_id:string;name:string;game:string;points:number;wins:number};

export default function Overview(){
 const {role}=useRole();
 const [games,setGames]=useState<Game[]>([]);
 const [leaders,setLeaders]=useState<Player[]>([]);
 const [stats,setStats]=useState<Record<string,number>>({});
 const [selected,setSelected]=useState("");
 const [error,setError]=useState("");
 const [loading,setLoading]=useState(true);

 useEffect(()=>{
  let active=true;
  fetch("http://localhost:8000/api/dashboard")
   .then(async r=>{const d=await r.json();if(!r.ok)throw Error(d.error||"Could not load dashboard.");return d})
   .then(d=>{if(!active)return;setGames(d.games||[]);setStats(d.stats||{});setSelected(d.games?.[0]?.name||"");setLoading(false)})
   .catch(e=>{if(!active)return;setError(e instanceof Error?e.message:"Could not connect to tournament data.");setLoading(false)});
  return()=>{active=false};
 },[]);

 useEffect(()=>{
  if(!selected)return;
  let active=true;
  fetch("http://localhost:8000/api/leaderboard?game="+encodeURIComponent(selected))
   .then(async r=>{const d=await r.json();if(!r.ok)throw Error(d.error||"Could not load standings.");return d})
   .then(d=>{if(active)setLeaders(d.players||[])})
   .catch(e=>{if(active)setError(e instanceof Error?e.message:"Could not load standings.")});
  return()=>{active=false};
 },[selected]);

 const tasks=role==="admin"
  ? [
    {icon:Gamepad2,title:"Set up games and scores",detail:"Publish games and record match results.",href:"/tournament",action:"Manage games"},
    {icon:ClipboardList,title:"Review student entries",detail:"Approve participation requests.",href:"/participants",action:"Review requests"},
  ]
  : [
    {icon:ClipboardList,title:"Join a tournament game",detail:"Choose a game and submit your details.",href:"/participants",action:"Add participation"},
    {icon:Medal,title:"Check the standings",detail:"See the top scorers in each game.",href:"/leaderboard",action:"Open leaderboard"},
  ];

 return <div className="simple-dashboard">
  <PageTitle eyebrow={role==="admin"?"ADMIN DASHBOARD":"STUDENT DASHBOARD"} title="Tournament overview" description={role==="admin"?"A clear view of games, entries, and results.":"Find a game, submit your entry, and follow the standings."}/>
  {error&&<div className="dashboard-error" role="alert"><b>Data is not available</b><span>{error}</span><small>Check the MySQL setup and restart the Python API.</small></div>}
  <div className="dashboard-metrics">
   <Card className="dashboard-metric"><span className="metric-icon blue"><Trophy size={20}/></span><span className="metric-label">Games</span><b>{loading?"—":games.length}</b><small>Open for participation</small></Card>
   <Card className="dashboard-metric"><span className="metric-icon green"><Users size={20}/></span><span className="metric-label">Active participants</span><b>{loading?"—":stats.players||0}</b><small>Approved and ready to play</small></Card>
   <Card className="dashboard-metric"><span className="metric-icon gold">{role==="admin"?<ClipboardList size={20}/>:<CheckCircle2 size={20}/>}</span><span className="metric-label">{role==="admin"?"Requests to review":"Results posted"}</span><b>{loading?"—":role==="admin"?(stats.pending||0):(stats.results||0)}</b><small>{role==="admin"?"Student entries waiting":"Match scores recorded"}</small></Card>
  </div>
  <div className="dashboard-columns">
   <Card className="dashboard-panel"><div className="dashboard-panel-heading"><div><span className="eyebrow">QUICK ACTIONS</span><h2>{role==="admin"?"What needs doing?":"Your next steps"}</h2></div><Tag tone={role==="admin"?"violet":"green"}>{role==="admin"?"ADMIN":"STUDENT"}</Tag></div>
    <div className="dashboard-task-list">{tasks.map(({icon:Icon,title,detail,href,action})=><Link className="dashboard-task" href={href} key={title}><span className="task-icon"><Icon size={19}/></span><span className="task-copy"><b>{title}</b><small>{detail}</small></span><span className="task-action">{action}<ArrowRight size={15}/></span></Link>)}</div>
    <div className="dashboard-footer-link"><Link href="/structures">Explore the DS and algorithm phases <ArrowRight size={14}/></Link></div>
   </Card>
   <Card className="dashboard-panel dashboard-leaders"><div className="dashboard-panel-heading"><div><span className="eyebrow">LIVE STANDINGS</span><h2>Top scorers</h2></div><Link href="/leaderboard" className="plain-arrow" aria-label="View full leaderboard"><ArrowRight size={18}/></Link></div>
    <label className="dashboard-game-select">Game<select value={selected} onChange={e=>setSelected(e.target.value)} disabled={!games.length}>{games.map(g=><option key={g.game_id} value={g.name}>{g.name}</option>)}</select></label>
    <div className="dashboard-rank-list">{leaders.slice(0,3).map((player,index)=><div className="dashboard-rank" key={player.student_id}><span className={"dashboard-rank-number rank-color-"+index}>{index+1}</span><span className="dashboard-rank-name"><b>{player.name}</b><small>{player.wins} wins</small></span><strong>{player.points.toLocaleString()} <small>pts</small></strong></div>)}
     {!loading&&!leaders.length&&<div className="dashboard-empty">Standings will appear when this game has active participants.</div>}
    </div>
    <Link href="/leaderboard" className="dashboard-full-link">View full leaderboard <ArrowRight size={15}/></Link>
   </Card>
  </div>
 </div>;
}
