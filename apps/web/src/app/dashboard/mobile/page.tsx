"use client";

import Link from "next/link";
import { Bell, Check, Images, LayoutDashboard, Library, PlusCircle, RotateCcw, Sparkles, X } from "lucide-react";
import "@/app/app-shell.css";

export default function MobileApprovePage() {
  return (
    <div className="mobile-shell">
      <main className="mobile-shell__main">
        <header style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <p className="muted" style={{ fontSize: "0.875rem", fontWeight: 500, margin: 0 }}>
                Tuesday, 14 May
              </p>
              <h1 className="display-title" style={{ fontSize: "1.5rem", marginTop: "0.25rem" }}>
                Today&apos;s content
              </h1>
            </div>
            <Bell size={18} />
          </div>
          <p className="muted" style={{ fontSize: "0.875rem", marginTop: "0.35rem" }}>
            2 of 3 ready for approval
          </p>
        </header>

        <article className="card" style={{ marginBottom: "1.5rem" }}>
          <div className="content-thumb" style={{ aspectRatio: "4/3" }}>
            <img
              src="https://images.unsplash.com/photo-1623875286835-cebe5e49e224?w=400&q=80"
              alt="New Summer Collection"
            />
            <div style={{ position: "absolute", top: 16, left: 16, display: "flex", gap: "0.5rem" }}>
              <span className="badge" style={{ background: "rgba(255,255,255,0.9)" }}>
                Product
              </span>
              <span className="badge" style={{ background: "rgba(255,255,255,0.9)" }}>
                Strong brand match
              </span>
            </div>
          </div>
          <div className="card-pad">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <h2 className="display-title" style={{ fontSize: "1.25rem" }}>
                New Summer Collection
              </h2>
              <span className="muted" style={{ fontSize: "0.75rem", fontWeight: 500 }}>
                1 of 3
              </span>
            </div>
            <p className="muted" style={{ fontSize: "0.875rem", lineHeight: 1.5 }}>
              Meet the pieces made for slow, sunny days.
            </p>
            <div className="muted" style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.75rem", margin: "1rem 0" }}>
              <Images size={14} /> 3 references used
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem" }}>
              <button type="button" className="btn btn-outline" style={{ flexDirection: "column", height: 56, borderRadius: 12, gap: 4 }}>
                <X size={18} />
                <span style={{ fontSize: "0.7rem" }}>Reject</span>
              </button>
              <button type="button" className="btn btn-outline" style={{ flexDirection: "column", height: 56, borderRadius: 12, gap: 4 }}>
                <RotateCcw size={18} />
                <span style={{ fontSize: "0.7rem" }}>Regenerate</span>
              </button>
              <button type="button" className="btn btn-primary" style={{ flexDirection: "column", height: 56, borderRadius: 12, gap: 4 }}>
                <Check size={18} />
                <span style={{ fontSize: "0.7rem" }}>Approve</span>
              </button>
            </div>
          </div>
        </article>

        <div style={{ textAlign: "center" }}>
          <p className="muted" style={{ fontSize: "0.75rem" }}>
            Swipe right to approve · swipe left to reject
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", margin: "1rem 0" }} aria-label="Progress">
            <div style={{ width: 64, height: 6, borderRadius: 999, background: "var(--accent)" }} />
            <div style={{ width: 64, height: 6, borderRadius: 999, background: "rgba(27,36,55,0.1)" }} />
            <div style={{ width: 64, height: 6, borderRadius: 999, background: "rgba(27,36,55,0.1)" }} />
          </div>
          <button type="button" className="btn btn-ghost">
            Review later
          </button>
        </div>
      </main>

      <nav className="mobile-nav" aria-label="Main">
        <Link href="/dashboard">
          <LayoutDashboard size={18} />
          Home
        </Link>
        <Link href="/dashboard/mobile" className="active">
          <Sparkles size={18} />
          Content
        </Link>
        <Link href="/dashboard/create">
          <PlusCircle size={18} />
          Create
        </Link>
        <Link href="/dashboard/library">
          <Library size={18} />
          Library
        </Link>
      </nav>
    </div>
  );
}
