import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight } from "lucide-react";
export function PageTitle({eyebrow,title,accent,description,action,href}:{eyebrow:string;title:string;accent?:string;description:string;action?:string;href?:string}) {
 return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title} {accent&&<em>{accent}</em>}</h1><p>{description}</p></div>{action&&href&&<Link className="button primary-button" href={href}>{action}<ArrowRight size={15}/></Link>}</div>;
}
export function Card({children,className=""}:{children:ReactNode;className?:string}) { return <section className={"card "+className}>{children}</section>; }
export function SectionHeading({label,title,aside}:{label?:string;title:string;aside?:ReactNode}) { return <div className="section-heading"><div>{label&&<div className="eyebrow">{label}</div>}<h2>{title}</h2></div>{aside}</div>; }
export function Tag({children,tone="blue"}:{children:ReactNode;tone?:string}) { return <span className={"tag "+tone}>{children}</span>; }
