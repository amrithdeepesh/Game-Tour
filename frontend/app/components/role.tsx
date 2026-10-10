"use client";
import {createContext,useContext} from "react";
export type UserRole="admin"|"student";
export type User={id:number;username:string;email:string;name:string;faction:string;role:UserRole};
export const RoleContext=createContext<{role:UserRole;user:User|null;loading:boolean;refresh:()=>Promise<void>;logout:()=>Promise<void>}>({role:"student",user:null,loading:true,refresh:async()=>{},logout:async()=>{}});
export function useRole(){return useContext(RoleContext)}
export const API="/api";
export async function api(path:string,options:RequestInit={}){
 let r:Response;
 try{r=await fetch(API+path,{...options,credentials:"include",headers:{"Content-Type":"application/json",...(options.headers||{})}})}
 catch{throw Error("Cannot reach the tournament API. Make sure the Python backend is running.")}
 const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||"Request failed.");return d
}
