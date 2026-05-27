# Local LLM Chat with Trend Micro AI Guard

A browser-based chat UI that connects to a local LLM (via LM Studio) with an optional Trend Micro AI Guard layer to scan and filter prompts before they reach the model.

---

## Lab Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Machine                         │
│                                                             │
│   Browser ──── http://localhost:3000 ───► Python Proxy      │
│      │                                    (server.py)       │
│      │                                        │             │
│      │  Direct mode                           │ AI Guard    │
│      │  ┌─────────────────────────────────┐   │ mode        │
│      │  │                                 │   │             │
│      └──┼──► LM Studio :8080              │   │             │
│         │    (google/gemma-4-e4b)         │   │             │
│         │         ▲                       │   │             │
│         │         │ (if Allow)            │   │             │
│         └─────────┼───────────────────────┘   │             │
│                   │                           │             │
└───────────────────┼───────────────────────────┼─────────────┘
                    │                           │
                    │                           ▼
                    │              Trend Vision One Cloud
                    │         api.xdr.trendmicro.com
                    │         /v3.0/aiSecurity/applyGuardrails
                    │
                    │         ┌─────────────┐
                    └─────────┤  action:    │
                              │  Allow ──►──┘ (forward to LM Studio)
                              │  Block ──►  Show blocked + reasons
                              └─────────────┘
```

### Request flow

| Mode | Flow |
|------|------|
| **Direct** | Browser → LM Studio → streaming response |
| **AI Guard** | Browser → Proxy → AI Guard API → Allow → LM Studio → streaming response |
| **AI Guard (blocked)** | Browser → Proxy → AI Guard API → Block → show reasons, stop |

---

## Prerequisites

| Component | What you need |
|-----------|--------------|
| **LM Studio** | Installed and running with a model loaded (any GGUF model) |
| **Python 3** | Built-in on macOS, no extra packages required |
| **Trend Vision One account** | With AI Guard / AI Scanner feature enabled |

---

## Step-by-Step Setup

### Step 1 — Install and configure LM Studio

1. Download and install [LM Studio](https://lmstudio.ai)
2. Load a model (e.g. `google/gemma-4-e4b`)
3. Go to **Developer** tab → **Local Server**
4. Click **Start Server**
5. Note the server URL shown (e.g. `http://192.168.1.51:8080`)
6. Go to **Server Settings** → enable **Enable CORS**

> The server must be reachable from your machine. If running on the same machine, use `http://localhost:1234` (LM Studio default port).

---

### Step 2 — Get Trend Vision One API Key

1. Log in to [Trend Vision One Console](https://portal.xdr.trendmicro.com)
2. Go to **Administration → API Keys**
3. Click **Add API Key**
4. Set a name and select a role that has **AI Scanner** permissions
5. Copy the generated key — you will need it in Step 5

> Your account region determines which API endpoint to use. Check your console URL:
> - `portal.xdr.trendmicro.com` → **US**
> - `portal.eu.xdr.trendmicro.com` → **EU**
> - `portal.sg.xdr.trendmicro.com` → **SG**
> - etc.

---

### Step 3 — Clone this repository

```bash
git clone https://github.com/nattavutm/tm-ai-guard.git
cd tm-ai-guard
```

---

### Step 4 — Start the proxy server

The proxy server is required to:
- Serve `chat.html` over HTTP (avoids browser `file://` restrictions)
- Forward AI Guard API calls server-side (bypasses browser CORS)

```bash
python3 server.py
```

Expected output:
```
  Local LLM Chat proxy running
  Open: http://localhost:3000
```

> Keep this terminal open while using the app.

---

### Step 5 — Open the chat UI

Open your browser and go to:

```
http://localhost:3000
```

> Do **not** open `chat.html` directly as a file (`file://...`). It must be served via the proxy.

---

### Step 6 — Configure the UI

**LM Studio URL** (top right):
- Enter your LM Studio server address (e.g. `http://192.168.1.51:8080`)
- A green dot confirms the connection is live

**Mode toggle:**

| Toggle | Behavior |
|--------|----------|
| **Direct** | Prompts go straight to LM Studio, no scanning |
| **AI Guard** | Prompts are scanned by AI Guard first |

**AI Guard config panel** (visible when AI Guard mode is active):

| Field | Value |
|-------|-------|
| Region | Match your Trend Vision One account region (US, EU, SG, etc.) |
| Application Name | Any identifier using only letters, numbers, `-`, `_` (e.g. `Bank-AI-Guard`) |
| API Key | The Bearer token from Step 2 |

---

## How It Works

### Direct mode
```
User types prompt
       │
       ▼
LM Studio /v1/chat/completions  (streaming)
       │
       ▼
Response shown in chat
```

### AI Guard mode
```
User types prompt
       │
       ▼
Python proxy → POST /v3.0/aiSecurity/applyGuardrails
       │
   ┌───▼────────┐
   │ action?    │
   └───┬────────┘
       │
    Allow ──► LM Studio /v1/chat/completions (streaming)
    Block ──► Show "Blocked" badge + reasons, stop
```

---

## Files

```
.
├── chat.html    # Single-page chat UI (HTML + CSS + JS, no build step)
├── server.py    # Python proxy server (stdlib only, no pip required)
└── README.md
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Red dot / "ไม่พบเซิร์ฟเวอร์" | LM Studio not running | Start LM Studio server |
| `Failed to fetch` (LM Studio) | CORS not enabled | LM Studio → Server Settings → Enable CORS |
| `AI Guard HTTP 401` | API key invalid or wrong region | Regenerate key or change region |
| `invalid TMV1-Application-Name` | App name has spaces or special chars | Use only letters, numbers, `-`, `_` |
| Port 3000 already in use | Previous server still running | `lsof -ti:3000 \| xargs kill -9` |

---

## Stopping the server

Press `Ctrl+C` in the terminal running `server.py`.
