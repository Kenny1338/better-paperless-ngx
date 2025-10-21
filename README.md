# Better Paperless

<div align="center">

**Automated Paperless-ngx with LLM Integration**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Intelligent document processing for Paperless-ngx with LLM-powered automation for titles, tags, metadata, and more.

</div>

---

## 🎯 Features

- **🤖 Automatic Title Generation**: Intelligent, descriptive titles based on document content
- **🏷️ Smart Tagging**: Hybrid approach with rule-based and LLM-based tags
- **📊 Metadata Extraction**: Automatic detection of dates, senders, amounts, invoice numbers
- **📁 Categorization**: Intelligent assignment to document types
- **📝 Summaries**: Optionally generated document summaries
- **⚡ Batch Processing**: Efficient parallel processing of multiple documents
- **🔌 Multi-LLM Support**: OpenAI (GPT-5-mini), Anthropic (Claude 4.5 Sonnet), Ollama (local)
- **🐳 Docker-Ready**: Complete Docker setup with docker-compose
- **🎨 Rich CLI**: User-friendly command-line interface with progress indicators

## 📋 Table of Contents

- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- Paperless-ngx installation
- OpenAI API Key (or other LLM provider)

### With Poetry (Recommended)

```bash
# Clone repository
git clone https://github.com/Kenny1338/better-paperless-ngx.git
cd better-paperless-ngx

# Install dependencies
poetry install

# Initialize configuration
poetry run better-paperless init

# Adjust configuration
cp config/config.example.yaml config/config.yaml
nano config/config.yaml

# Set environment variables
cp .env.example .env
nano .env
```

### With Docker (Recommended for Unraid)

**Pull from GitHub Container Registry:**

```bash
docker pull ghcr.io/kenny1338/better-paperless-ngx:latest
```

**Run with Docker:**

```bash
docker run -d \
  --name better-paperless \
  -e PAPERLESS_API_URL=http://your-paperless:8000 \
  -e PAPERLESS_API_TOKEN=your_token_here \
  -e OPENAI_API_KEY=your_openai_key_here \
  -v /path/to/config:/app/config \
  -v /path/to/logs:/app/logs \
  ghcr.io/kenny1338/better-paperless-ngx:latest
```

**Or use Docker Compose:**

```bash
# Clone repository
git clone https://github.com/kenny1338/better-paperless-ngx.git
cd better-paperless-ngx

# Create .env file
cp .env.example .env
nano .env

# Adjust configuration
cp config/config.example.yaml config/config.yaml
nano config/config.yaml

# Start with Docker Compose
cd docker
docker-compose up -d
```

### With pip

```bash
# Clone repository
git clone https://github.com/Kenny1338/better-paperless-ngx.git
cd better-paperless-ngx

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install
pip install -e .
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project directory:

```env
# Paperless-ngx
PAPERLESS_API_URL=http://localhost:8000
PAPERLESS_API_TOKEN=your_paperless_api_token_here

# OpenAI (Primary)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Redis for Caching
REDIS_URL=redis://localhost:6379/0
```

### Configuration File

Main configuration in [`config/config.yaml`](config/config.yaml:1):

```yaml
paperless:
  url: "http://localhost:8000"
  api_token: "${PAPERLESS_API_TOKEN}"

llm:
  primary_provider: "openai"
  
processing:
  features:
    title_generation: true
    tagging: true
    metadata_extraction: true
    categorization: true
    summarization: false
```

See [`config/config.example.yaml`](config/config.example.yaml:1) for all options.

### Tagging Rules

Customize tagging rules in [`config/rules/tagging_rules.yaml`](config/rules/tagging_rules.yaml:1):

```yaml
rules:
  - name: "Invoice"
    patterns:
      - regex: '\b(invoice|rechnung)\b'
        case_insensitive: true
    tags: ["invoice", "financial"]
    priority: 10
```

## 💻 Usage

### CLI Commands

#### Process Single Document

```bash
better-paperless process 1234
```

#### Batch Processing

```bash
# All unprocessed documents
better-paperless batch --all

# With filter
better-paperless batch --filter "created__gte=30d"

# With concurrency limit
better-paperless batch --all --concurrency 3
```

#### Validate Configuration

```bash
better-paperless config validate
```

#### Show Configuration

```bash
better-paperless config show
```

#### Show Version

```bash
better-paperless version
```

### As Python Module

```python
import asyncio
from better_paperless.api import PaperlessClient
from better_paperless.llm import LLMFactory
from better_paperless.processors import DocumentProcessor
from better_paperless.core import Config

async def main():
    # Load configuration
    config = Config()
    
    # Initialize clients
    async with PaperlessClient(
        base_url=config.paperless.api_url,
        api_token=config.paperless.api_token
    ) as paperless:
        llm = LLMFactory.create_from_config(config)
        options = config.get_processing_options()
        
        # Create processor
        processor = DocumentProcessor(paperless, llm, options)
        
        # Process document
        result = await processor.process_document(1234)
        
        if result.success:
            print(f"Title: {result.title}")
            print(f"Tags: {result.tags}")
            print(f"Processing time: {result.processing_time:.2f}s")

asyncio.run(main())
```

## 🏗️ Architecture

### Components

```
better-paperless/
├── src/better_paperless/
│   ├── api/              # Paperless API Client
│   ├── llm/              # LLM Provider Abstraction
│   ├── processors/       # Document Processing Pipeline
│   ├── core/             # Core Utilities (Config, Logger, Cache)
│   └── cli/              # Command-Line Interface
├── config/               # Configuration Files
└── docker/               # Docker Setup
```

### Processing Pipeline

1. **Fetch Document** → Paperless API
2. **Extract Text** → OCR Content
3. **Generate Title** → LLM
4. **Extract Metadata** → LLM + Regex
5. **Generate Tags** → Hybrid (Rules + LLM)
6. **Categorize** → LLM
7. **Update Document** → Paperless API

### LLM Providers

- **OpenAI**: GPT-5-mini (recommended for cost-efficiency)
- **Anthropic**: Claude 4.5 Sonnet (recommended for quality)
- **Ollama**: Local models (llama2, llama3, etc.)

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/Kenny1338/better-paperless-ngx.git
cd better-paperless-ngx

# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

### Run Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=better_paperless

# Unit tests only
poetry run pytest tests/unit/
```

### Code Quality

```bash
# Formatting
poetry run black src/

# Import sorting
poetry run isort src/

# Linting
poetry run flake8 src/

# Type checking
poetry run mypy src/
```

## 📊 Example Workflows

### Workflow 1: Automatic Processing After Upload

1. Upload document to Paperless
2. Trigger Better Paperless via webhook/cron
3. Automatic processing:
   - Title: "Invoice - City Utilities - 2024-03-15 - $234.56"
   - Tags: invoice, utility, electricity
   - Correspondent: City Utilities
   - Date: 2024-03-15

### Workflow 2: Batch Processing Existing Documents

```bash
# Process all documents without titles
better-paperless batch --filter "title__isnull=true" --concurrency 5

# Output:
# ✓ 156 documents processed successfully
# ⚠ 3 errors
# 💰 Cost: $2.34
# ⏱ Average: 3.2s/document
```

## 🔧 Advanced Configuration

### Custom LLM Prompts

Customize prompts in [`src/better_paperless/llm/prompts.py`](src/better_paperless/llm/prompts.py:1):

```python
def title_generation(content: str, language: str = "en") -> str:
    return f"""Create a title for:
    {content[:1000]}
    
    Format: "Type - Info - Date"
    """
```

### Custom Tagging Rules

Add custom rules in [`config/rules/tagging_rules.yaml`](config/rules/tagging_rules.yaml:1):

```yaml
rules:
  - name: "My Rule"
    patterns:
      - regex: '\b(pattern)\b'
        case_insensitive: true
    tags: ["custom-tag"]
    priority: 10
```

## 🐳 Docker Deployment

### Unraid

**Docker Pull Command:**
```
ghcr.io/kenny1338/better-paperless-ngx:latest
```

**Unraid Template Settings:**
- **Repository**: `ghcr.io/kenny1338/better-paperless-ngx:latest`
- **Network Type**: Bridge
- **Port Mappings**: None required (unless using webhook mode)
- **Environment Variables**:
  - `PAPERLESS_API_URL` → Your Paperless-ngx URL (e.g., `http://192.168.1.100:8000`)
  - `PAPERLESS_API_TOKEN` → Your Paperless API token
  - `OPENAI_API_KEY` → Your OpenAI API key
- **Volume Mappings**:
  - `/app/config` → `/mnt/user/appdata/better-paperless/config`
  - `/app/logs` → `/mnt/user/appdata/better-paperless/logs`

### Standalone

```bash
cd docker
docker-compose up -d
```

### With Paperless-ngx

Add to your existing `docker-compose.yml`:

```yaml
services:
  better-paperless:
    image: ghcr.io/kenny1338/better-paperless-ngx:latest
    environment:
      PAPERLESS_API_URL: http://paperless:8000
      PAPERLESS_API_TOKEN: ${PAPERLESS_API_TOKEN}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    networks:
      - paperless-network
```

## 📈 Performance & Costs

### Typical Processing

- **Processing time**: 2-5 seconds per document
- **LLM costs** (GPT-5-mini):
  - Title: ~$0.001
  - Tags: ~$0.001
  - Metadata: ~$0.001
  - **Total**: ~$0.003 per document

- **LLM costs** (Claude 4.5 Sonnet):
  - Title: ~$0.015
  - Tags: ~$0.015
  - Metadata: ~$0.015
  - **Total**: ~$0.045 per document

### Optimization

- Use caching for repeated requests
- Batch processing with concurrency
- Fallback to rule-based methods
- Ollama for local, cost-free processing

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [`CONTRIBUTING.md`](CONTRIBUTING.md:1) for details.

## 📝 License

This project is licensed under the MIT License - see [`LICENSE`](LICENSE:1) for details.

## 🙏 Acknowledgments

- [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) - The best DMS
- [OpenAI](https://openai.com/) - GPT-4 API
- [Anthropic](https://anthropic.com/) - Claude API
- [Typer](https://typer.tiangolo.com/) - CLI Framework
- [Rich](https://rich.readthedocs.io/) - Terminal Formatting

## 📞 Support

- 💬 Discussions: [GitHub Discussions](https://github.com/Kenny1338/better-paperless-ngx/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/Kenny1338/better-paperless-ngx/issues)

## 🗺️ Roadmap

- [ ] Web UI for configuration
- [ ] Workflow automation
- [ ] Multi-tenancy support
- [ ] ML-based training
- [ ] Advanced OCR integration
- [ ] Custom LLM fine-tuning

---

<div align="center">

**Made with ❤️ for the Paperless Community**

[⭐ Star on GitHub](https://github.com/Kenny1338/better-paperless-ngx)

</div>