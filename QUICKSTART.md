# 🚀 Quick Start Guide - Better Paperless

## Installation Complete! ✅

The project is installed and ready to use.

## Next Steps

### 1. Initialize Configuration

```bash
python -m poetry run better-paperless init
```

### 2. Set Up Environment Variables

```bash
# Create .env file
copy .env.example .env

# Edit and add API keys
notepad .env
```

**Required API Keys:**
- `PAPERLESS_API_TOKEN` - From your Paperless-ngx installation
- `OPENAI_API_KEY` - From https://platform.openai.com/api-keys

### 3. Adjust Configuration

```bash
# Copy example configuration
copy config\config.example.yaml config\config.yaml

# Customize
notepad config\config.yaml
```

**Important Settings:**
```yaml
paperless:
  url: "http://localhost:8000"  # Your Paperless URL
  
llm:
  primary_provider: "openai"
  openai:
    model: "gpt-5-mini"  # Recommended for cost-efficiency
```

### 4. Test Configuration

```bash
python -m poetry run better-paperless config validate
```

### 5. Process First Document

```bash
# Replace 123 with a real document ID from Paperless
python -m poetry run better-paperless process 123
```

**Example Output:**
```
Processing document 123...
✓ Processing successful!

╭─────────────────────────────────────────╮
│      Processing Results                 │
├──────────────────┬──────────────────────┤
│ Title            │ Invoice - Acme...    │
│ Tags             │ invoice, financial   │
│ Processing Time  │ 3.2s                 │
│ LLM Tokens       │ 1234                 │
│ LLM Cost         │ $0.015               │
╰──────────────────┴──────────────────────╯
```

### 6. Batch Processing (Optional)

```bash
# Process all documents without titles
python -m poetry run better-paperless batch --filter "title__isnull=true" --limit 10

# Process all documents (caution with large quantities!)
python -m poetry run better-paperless batch --all --limit 50 --concurrency 3
```

## 🎨 Available Commands

```bash
# Show help
python -m poetry run better-paperless --help

# Single document
python -m poetry run better-paperless process <ID>

# Batch processing
python -m poetry run better-paperless batch [OPTIONS]

# Configuration
python -m poetry run better-paperless config validate
python -m poetry run better-paperless config show

# Version
python -m poetry run better-paperless version

# Initialization
python -m poetry run better-paperless init
```

## 🔧 Troubleshooting

### Problem: "No API token configured"
**Solution:** Set `PAPERLESS_API_TOKEN` in the `.env` file

### Problem: "OpenAI API key not found"
**Solution:** Set `OPENAI_API_KEY` in the `.env` file

### Problem: "Connection refused"
**Solution:** Check that Paperless is running and the URL is correct

### Problem: "Document not found"
**Solution:** Use a valid document ID from Paperless

## 💡 Tips

### Use Different Models
```yaml
# In config.yaml:
llm:
  openai:
    model: "gpt-5-mini"  # Best cost-efficiency (recommended)
  # or
  anthropic:
    model: "claude-4.5-sonnet"  # Best quality
```

### Only Generate Titles
```yaml
processing:
  features:
    title_generation: true
    tagging: false
    metadata_extraction: false
```

### Optimize Performance
```yaml
processing:
  batch:
    max_concurrent_processes: 10  # More parallelism
cache:
  enabled: true
  backend: "redis"  # Faster than memory
```

## 📚 Additional Resources

- **Full Documentation**: [`README.md`](README.md:1)
- **Architecture Details**: [`ARCHITECTURE.md`](ARCHITECTURE.md:1)
- **Example Configuration**: [`config/config.example.yaml`](config/config.example.yaml:1)
- **Tagging Rules**: [`config/rules/tagging_rules.yaml`](config/rules/tagging_rules.yaml:1)

## 🐳 Docker Alternative

If you prefer Docker:

```bash
# Set up .env
copy .env.example .env

# Adjust config
copy config\config.example.yaml config\config.yaml

# Start
cd docker
docker-compose up -d

# View logs
docker-compose logs -f better-paperless
```

---

**Good luck with Better Paperless! 🎉**

Questions? [GitHub Issues](https://github.com/Kenny1338/better-paperless-ngx/issues)