const API = "http://localhost:8080";

async function getToken() {
  try {
    const res = await fetch(`${API}/api/v1/login/access-token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "username=admin@example.com&password=changethis",
    });
    const data = await res.json();
    return data.access_token;
  } catch {
    return null;
  }
}

function status(msg, cls) {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.className = cls;
}

document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  document.getElementById("url").textContent = tab.url;
  document.getElementById("title").value = tab.title;

  const token = await getToken();

  document.getElementById("save").addEventListener("click", async () => {
    const btn = document.getElementById("save");
    const title = document.getElementById("title").value.trim();
    const content = document.getElementById("content").value.trim();
    const tags = document.getElementById("tags").value.trim();

    if (!title || !content) {
      status("Title and content are required.", "error");
      return;
    }

    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
      const res = await fetch(`${API}/api/v1/notes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          content,
          tags: tags ? tags.split(",").map((t) => t.trim()).filter(Boolean) : null,
        }),
      });

      if (res.ok) {
        status("Saved!", "success");
        setTimeout(() => window.close(), 800);
      } else {
        const err = await res.json();
        status(err.detail || "Failed to save", "error");
      }
    } catch (e) {
      status("Cannot reach Second Brain. Is it running?", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Save to Second Brain";
    }
  });
});
