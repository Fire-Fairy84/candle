import { type NextRequest, NextResponse } from "next/server";

const BASE_URL = process.env.CANDLE_API_BASE_URL!;
const API_KEY = process.env.CANDLE_API_KEY!;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const url = new URL(request.url);
  const upstream = `${BASE_URL}/api/v1/${path.join("/")}${url.search}`;

  const res = await fetch(upstream, {
    headers: { "X-API-Key": API_KEY },
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
