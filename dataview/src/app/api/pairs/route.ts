import { NextResponse } from "next/server";
import { listAvailablePairs } from "@/lib/csv";

export async function GET() {
  try {
    const pairs = await listAvailablePairs();
    return NextResponse.json({ pairs });
  } catch {
    return NextResponse.json({ pairs: [] });
  }
}
