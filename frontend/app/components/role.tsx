"use client";
import { createContext, useContext } from "react";
export type UserRole = "admin" | "student";
export const RoleContext = createContext<{role:UserRole;setRole:(role:UserRole)=>void}>({role:"student",setRole:()=>{}});
export function useRole(){return useContext(RoleContext)}
