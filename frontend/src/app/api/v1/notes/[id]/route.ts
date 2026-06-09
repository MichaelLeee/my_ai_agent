import { NextRequest, NextResponse } from "next/server";
import { backendFetch, BackendApiError } from "@/lib/server-api";

async function getToken(req: NextRequest) {
  const token = req.cookies.get("access_token")?.value;
  if (!token) return null;
  return token;
}

export async function GET(
  request: NextRequest, { params }: { params: Promise<{ id: string }> },
) {
  try {
    const token = await getToken(request);
    if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    const { id } = await params;
    const data = await backendFetch(`/api/v1/notes/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}

export async function PATCH(
  request: NextRequest, { params }: { params: Promise<{ id: string }> },
) {
  try {
    const token = await getToken(request);
    if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    const { id } = await params;
    const body = await request.json();
    const data = await backendFetch(`/api/v1/notes/${id}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest, { params }: { params: Promise<{ id: string }> },
) {
  try {
    const token = await getToken(request);
    if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    const { id } = await params;
    await backendFetch(`/api/v1/notes/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}
