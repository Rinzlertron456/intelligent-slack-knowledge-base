export default async function handler(_request, response) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    response.status(500).json({ status: "error", detail: "BACKEND_URL is not configured" });
    return;
  }

  try {
    const upstream = await fetch(new URL("/healthz", backendUrl), {
      headers: { accept: "application/json" },
    });
    const payload = await upstream.json();
    response.status(upstream.status).json(payload);
  } catch (error) {
    response.status(502).json({ status: "error", detail: "Cloud Run backend is unreachable" });
  }
}
