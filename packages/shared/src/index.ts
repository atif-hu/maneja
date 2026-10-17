export type ImageStatus =
  | "generating"
  | "pending_review"
  | "approved"
  | "rejected"
  | "archived";

export type RunStatus = "pending" | "running" | "completed" | "failed";

export type MemberRole = "owner" | "admin" | "viewer";
