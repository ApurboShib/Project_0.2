# 🚀 Legal Drafting Assistant - Startup Guide

## Quick Start (3 Steps)

### Step 1: Get Your API Key

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create account and get your `ANTHROPIC_API_KEY`
3. Copy the key to your clipboard

### Step 2: Edit `.env`

```bash
cd /Users/apurboshib/Desktop/Apurbo/Project_02
nano .env
```

Paste this (replace with your actual key):

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
LEGAL_AI_DATA_DIR=./data
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Run the App

```bash
./run.sh
```

**That's it!** When you see:

```
🚀 Starting Legal Drafting Assistant...
📍 Open http://localhost:8000 in your browser
```

Open your browser to `http://localhost:8000`

---

## Complete Setup Steps (If Manual)

### 1. Install Python (if needed)

```bash
# Check if you have Python 3.9+
python3 --version

# If not installed, use Homebrew on Mac:
brew install python3
```

### 2. Create Virtual Environment

```bash
cd /Users/apurboshib/Desktop/Apurbo/Project_02
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API key
```

### 5. Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open Browser

```
http://localhost:8000
```

---

## What Each File Does

| File               | Purpose                            |
| ------------------ | ---------------------------------- |
| `run.sh`           | **Use this!** One-command startup  |
| `run-api.sh`       | Production server (no auto-reload) |
| `requirements.txt` | Python dependencies                |
| `.env`             | Your API keys & config             |
| `.env.example`     | Template for .env                  |

---

## Testing Without API Key

You can still test the UI without an API key, but drafting won't work:

```bash
# Comment out the ANTHROPIC_API_KEY line in .env
# ANTHROPIC_API_KEY=sk-ant-...

./run.sh
```

The app will:

- ✓ Accept document uploads
- ✓ Extract text & structure
- ✓ Show retrieval results
- ✗ Skip draft generation (will show error)

---

## Sample Workflow

### Via Web UI

1. Download a sample: [sample_notice.txt](samples/sample_notice.txt)
2. Open `http://localhost:8000`
3. Upload the file
4. Select "Notice-Related Summary"
5. Click "Generate Draft"
6. See the draft with evidence citations
7. Edit and save to learn style rules

### Via API

```bash
# 1. Process document
DOC_ID=$(curl -X POST -F "file=@samples/sample_notice.txt" \
  http://localhost:8000/api/process | jq -r '.doc_id')

echo "Document ID: $DOC_ID"

# 2. Generate draft
DRAFT_ID=$(curl -X POST http://localhost:8000/api/draft \
  -H "Content-Type: application/json" \
  -d "{\"doc_ids\":[\"$DOC_ID\"],\"draft_type\":\"notice_summary\"}" | jq -r '.draft_id')

echo "Draft ID: $DRAFT_ID"

# 3. View the draft
curl http://localhost:8000/api/drafts | jq '.'
```

---

## Stopping the Server

Press `Ctrl+C` in your terminal.

---

## Common Issues

### "Port 8000 already in use"

```bash
# Use a different port
uvicorn app.main:app --port 8001
```

### "ANTHROPIC_API_KEY is not configured"

1. Check your `.env` file exists
2. Verify the key is set correctly
3. Restart the server after editing `.env`

### "Module not found"

```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Database locked"

```bash
# Remove the old database and restart
rm data/app.db
./run.sh
```

---

## Folder Structure Created

After running, you'll see:

```
data/
├── app.db                 # SQLite database with all documents & drafts
├── chroma/                # Vector embeddings
└── file_store/            # Raw document copies
.venv/                     # Virtual environment (ignore)
```

---

## Next Steps

✅ Check the full [README.md](README.md) for:

- Detailed API endpoints
- All draft type options
- How the learning loop works
- Troubleshooting guide

✅ Try the sample files in `samples/`

✅ Build your own legal document workflow!

---

## Support

If something breaks:

1. Check the error message
2. Look at [Troubleshooting](README.md#-troubleshooting)
3. Check logs in terminal
4. Restart: `./run.sh`

Happy drafting! 📝⚖️
