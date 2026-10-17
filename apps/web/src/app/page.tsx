import { redirect } from "next/navigation";

/** Middleware sends users to /login or /dashboard; this is a fallback. */
export default function HomePage() {
  redirect("/login");
}
