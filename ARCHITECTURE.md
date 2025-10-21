# Better Paperless - Architecture Plan
## Automated Paperless-ngx with LLM Integration

**Version:** 1.0  
**Date:** 2025-10-21  
**Status:** Architecture Design Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Structure](#project-structure)
3. [Module Descriptions](#module-descriptions)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Internal API Design](#internal-api-design)
6. [Configuration Schema](#configuration-schema)
7. [Example Workflows](#example-workflows)
8. [Dependencies](#dependencies)
9. [Deployment Strategy](#deployment-strategy)
10. [Security Considerations](#security-considerations)
11. [Future Enhancements](#future-enhancements)

---

## 1. Executive Summary

**Better Paperless** is a comprehensive Python automation system for Paperless-ngx that leverages Large Language Models (primarily OpenAI) to automate document management tasks including:

- Intelligent document titling
- Context-aware tagging
- Metadata extraction (dates, senders, recipients)
- Automatic categorization
- Document summarization
- Smart workflow automation

### Key Design Principles

1. **Modularity**: Clean separation of concerns with pluggable components
2. **Extensibility**: Support for multiple LLM providers through abstraction
3. **Reliability**: Comprehensive error handling, retry logic, and logging
4. **Configurability**: YAML-based configuration for flexible customization
5. **Scalability**: Efficient batch processing and queue management
6. **Maintainability**: Type hints, documentation, and clean code practices

---

## 2. Project Structure

```
better-paperless/
├── src/
│   ├── better_paperless/
│   │   ├── __init__.py
│   │   ├── __main__.py              # CLI entry point
│   │   │
│   │   ├── api/                      # Paperless API Layer
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # Paperless API client
│   │   │   ├── models.py            # Pydantic models for API responses
│   │   │   └── exceptions.py        # API-specific exceptions
│   │   │
│   │   ├── llm/                      # LLM Service Layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Abstract LLM provider interface
│   │   │   ├── openai_provider.py   # OpenAI implementation
│   │   │   ├── anthropic_provider.py # Anthropic implementation
│   │   │   ├── ollama_provider.py   # Ollama implementation
│   │   │   ├── factory.py           # LLM provider factory
│   │   │   └── prompts.py           # Prompt templates
│   │   │
│   │   ├── processors/               # Document Processing
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py # Main document processor
│   │   │   ├── title_generator.py   # Auto-titling logic
│   │   │   ├── tag_engine.py        # Tagging engine
│   │   │   ├── metadata_extractor.py # Metadata extraction
│   │   │   ├── categorizer.py       # Document categorization
│   │   │   └── summarizer.py        # Document summarization
│   │   │
│   │   ├── core/                     # Core Utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Configuration management
│   │   │   ├── logger.py            # Logging setup
│   │   │   ├── cache.py             # Caching layer
│   │   │   └── validators.py        # Input validation
│   │   │
│   │   ├── scheduler/                # Automation & Scheduling
│   │   │   ├── __init__.py
│   │   │   ├── watcher.py           # Document watcher
│   │   │   ├── batch_processor.py   # Batch processing
│   │   │   └── queue_manager.py     # Processing queue
│   │   │
│   │   ├── cli/                      # Command Line Interface
│   │   │   ├── __init__.py
│   │   │   ├── commands.py          # CLI commands
│   │   │   └── ui.py                # Rich UI components
│   │   │
│   │   └── utils/                    # Helper Utilities
│   │       ├── __init__.py
│   │       ├── retry.py             # Retry decorators
│   │       ├── text_processing.py   # Text utilities
│   │       └── metrics.py           # Metrics collection
│   │
├── config/                           # Configuration Files
│   ├── config.yaml                  # Main configuration
│   ├── config.example.yaml          # Example configuration
│   ├── prompts/                     # Prompt templates
│   │   ├── title_generation.yaml
│   │   ├── tagging.yaml
│   │   ├── metadata_extraction.yaml
│   │   └── summarization.yaml
│   └── rules/                       # Custom rules
│       └── tagging_rules.yaml
│
├── tests/                            # Test Suite
│   ├── unit/
│   │   ├── test_api_client.py
│   │   ├── test_llm_providers.py
│   │   ├── test_processors.py
│   │   └── test_config.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_paperless_api.py
│   └── fixtures/
│       └── sample_documents.py
│
├── docs/                             # Documentation
│   ├── getting-started.md
│   ├── configuration.md
│   ├── api-reference.md
│   ├── examples.md
│   └── troubleshooting.md
│
├── docker/                           # Docker Configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── scripts/                          # Utility Scripts
│   ├── setup.sh
│   ├── migrate_config.py
│   └── benchmark.py
│
├── .env.example                      # Environment variables template
├── .gitignore
├── pyproject.toml                    # Poetry configuration
├── README.md
├── LICENSE
└── ARCHITECTURE.md                   # This document
```

---

## 3. Module Descriptions

### 3.1 API Layer (`api/`)

#### `client.py` - Paperless API Client
**Responsibilities:**
- HTTP client for Paperless-ngx REST API
- Authentication handling
- Request/response serialization
- Rate limiting and retry logic
- Pagination support

**Key Classes:**
```python
class PaperlessClient:
    - get_documents(filters, limit, offset) -> List[Document]
    - get_document(document_id) -> Document
    - update_document(document_id, updates) -> Document
    - get_tags() -> List[Tag]
    - create_tag(name, color) -> Tag
    - get_correspondents() -> List[Correspondent]
    - get_document_types() -> List[DocumentType]
    - download_document(document_id) -> bytes
```

#### `models.py` - Data Models
**Responsibilities:**
- Pydantic models for type-safe API interactions
- Validation of API responses
- Serialization/deserialization

**Key Models:**
```python
Document, Tag, Correspondent, DocumentType, 
CustomField, SearchResult, BulkUpdateRequest
```

### 3.2 LLM Layer (`llm/`)

#### `base.py` - Abstract LLM Interface
**Responsibilities:**
- Define common interface for all LLM providers
- Token counting and cost estimation
- Response parsing and validation

**Key Classes:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_completion(prompt, temperature, max_tokens) -> str
    @abstractmethod
    async def generate_structured_output(prompt, schema) -> dict
    @abstractmethod
    def count_tokens(text) -> int
    @abstractmethod
    def estimate_cost(input_tokens, output_tokens) -> float
```

#### `openai_provider.py` - OpenAI Implementation
**Responsibilities:**
- OpenAI API integration (primary provider)
- GPT-4, GPT-3.5-turbo support
- Function calling for structured outputs
- Streaming support for long documents

#### `factory.py` - LLM Provider Factory
**Responsibilities:**
- Provider instantiation based on configuration
- Provider switching and fallback logic
- Connection pooling

### 3.3 Processors Layer (`processors/`)

#### `document_processor.py` - Main Orchestrator
**Responsibilities:**
- Coordinate all processing steps
- Execute processing pipeline
- Handle processing errors and retries
- Maintain processing state

**Processing Pipeline:**
1. Fetch document from Paperless
2. Extract text content
3. Generate title (if needed)
4. Extract metadata
5. Generate tags
6. Categorize document
7. Generate summary (if enabled)
8. Update document in Paperless

#### `title_generator.py` - Auto-Titling
**Responsibilities:**
- Generate concise, descriptive titles
- Consider document type and content
- Handle multi-language documents
- Avoid duplicate titles

**Example Output:**
```
"Electricity Bill - June 2024 - Provider Name"
"Employment Contract - John Doe - 2024-01-15"
"Bank Statement - Account 1234 - March 2024"
```

#### `tag_engine.py` - Intelligent Tagging
**Responsibilities:**
- Rule-based tagging (regex, keywords)
- LLM-based contextual tagging
- Hierarchical tag suggestions
- Confidence scoring

**Tagging Strategies:**
1. **Rule-based**: Fast, deterministic matching
2. **LLM-based**: Context-aware, semantic understanding
3. **Hybrid**: Combine both approaches

#### `metadata_extractor.py` - Metadata Extraction
**Responsibilities:**
- Extract dates (document date, due date, etc.)
- Identify senders/correspondents
- Extract amounts and currencies
- Identify document types
- Custom field extraction

#### `categorizer.py` - Document Categorization
**Responsibilities:**
- Classify documents into predefined categories
- Learn from existing categorization
- Handle ambiguous documents
- Multi-label classification support

#### `summarizer.py` - Document Summarization
**Responsibilities:**
- Generate concise summaries
- Extract key information
- Support different summary lengths
- Multi-language support

### 3.4 Core Layer (`core/`)

#### `config.py` - Configuration Management
**Responsibilities:**
- Load and validate YAML configuration
- Environment variable override support
- Configuration hot-reloading
- Schema validation

#### `logger.py` - Logging Setup
**Responsibilities:**
- Structured logging (JSON format)
- Log rotation and retention
- Log level management
- Contextual logging

#### `cache.py` - Caching Layer
**Responsibilities:**
- Cache LLM responses
- Cache Paperless API responses
- TTL-based expiration
- Cache invalidation

### 3.5 Scheduler Layer (`scheduler/`)

#### `watcher.py` - Document Watcher
**Responsibilities:**
- Monitor Paperless for new documents
- Webhook support for real-time processing
- Polling fallback mechanism
- Event filtering

#### `batch_processor.py` - Batch Processing
**Responsibilities:**
- Process multiple documents efficiently
- Parallel processing with concurrency control
- Progress tracking
- Batch error handling

#### `queue_manager.py` - Processing Queue
**Responsibilities:**
- Queue documents for processing
- Priority-based processing
- Retry failed documents
- Dead letter queue for permanent failures

### 3.6 CLI Layer (`cli/`)

#### `commands.py` - CLI Commands
**Responsibilities:**
- Command definitions using Click/Typer
- Argument parsing and validation
- Interactive prompts

**Commands:**
```bash
better-paperless process [document_id]    # Process single document
better-paperless batch [--all | --filter] # Batch process documents
better-paperless watch                    # Start document watcher
better-paperless config validate          # Validate configuration
better-paperless config show              # Display configuration
better-paperless tags sync                # Sync tags with Paperless
better-paperless stats                    # Show processing statistics
```

---

## 4. Data Flow Architecture

### 4.1 High-Level Data Flow

```
┌─────────────────┐
│  Paperless-ngx  │
│   (Documents)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│           Document Watcher / Batch Processor         │
│  - Monitors new documents                            │
│  - Fetches documents from queue                      │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Paperless API Client                    │
│  - Fetch document metadata                           │
│  - Download document content (OCR text)              │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│           Document Processor (Orchestrator)          │
│  - Coordinates processing pipeline                   │
│  - Manages state and error handling                  │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Processing Pipeline                     │
│                                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │  1. Title Generation                         │   │
│  │     - Extract key information                │   │
│  │     - Generate descriptive title             │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  2. Metadata Extraction                      │   │
│  │     - Extract dates                          │   │
│  │     - Identify correspondent                 │   │
│  │     - Extract custom fields                  │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  3. Tag Generation                           │   │
│  │     - Apply rule-based tags                  │   │
│  │     - Generate LLM-based tags                │   │
│  │     - Merge and deduplicate                  │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  4. Categorization                           │   │
│  │     - Classify document type                 │   │
│  │     - Assign to category                     │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  5. Summarization (Optional)                 │   │
│  │     - Generate summary                       │   │
│  │     - Store in custom field                  │   │
│  └──────────────────┬───────────────────────────┘   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   LLM Provider         │
         │   (OpenAI/Anthropic)   │
         │   - Process prompts    │
         │   - Return results     │
         └───────────┬────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Response Parser     │
         │   - Validate output   │
         │   - Extract data      │
         └───────────┬────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Paperless API Client │
         │  - Update document    │
         │  - Create tags        │
         │  - Set metadata       │
         └───────────┬────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Paperless-ngx       │
         │   (Updated Document)  │
         └───────────────────────┘
```

### 4.2 Processing Flow Details

#### Single Document Processing Flow

1. **Document Retrieval**
   - Fetch document metadata from Paperless API
   - Download OCR text content
   - Validate document structure

2. **Pre-processing**
   - Text cleaning and normalization
   - Language detection
   - Document type preliminary classification

3. **LLM Processing**
   - Construct context-aware prompts
   - Send requests to LLM provider
   - Handle rate limiting and retries
   - Parse and validate responses

4. **Post-processing**
   - Validate generated data
   - Apply business rules
   - Merge with existing metadata
   - Prepare update payload

5. **Update Document**
   - Create missing tags/correspondents
   - Update document metadata
   - Verify update success
   - Log processing results

### 4.3 Error Handling Flow

```
Processing Error Detected
         │
         ▼
Is error retriable?
    │        │
   Yes       No
    │        │
    │        ▼
    │    Log to dead letter queue
    │    Send notification
    │    Mark as failed
    │
    ▼
Retry with exponential backoff
    │
    ▼
Max retries reached?
    │        │
    No      Yes
    │        │
    │        ▼
    │    Move to dead letter queue
    │    Send alert
    │
    ▼
Continue processing
```

---

## 5. Internal API Design

### 5.1 Core Interfaces

#### Document Processor Interface

```python
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """Result of document processing"""
    document_id: int
    success: bool
    title: Optional[str] = None
    tags: List[str] = None
    correspondent: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    summary: Optional[str] = None
    errors: List[str] = None
    processing_time: float = 0.0
    llm_tokens_used: int = 0
    llm_cost: float = 0.0

class DocumentProcessor:
    """Main document processor orchestrating all processing steps"""
    
    async def process_document(
        self,
        document_id: int,
        options: ProcessingOptions
    ) -> ProcessingResult:
        """
        Process a single document
        
        Args:
            document_id: Paperless document ID
            options: Processing configuration options
            
        Returns:
            ProcessingResult with all extracted information
        """
        pass
    
    async def process_batch(
        self,
        document_ids: List[int],
        options: ProcessingOptions,
        max_concurrency: int = 5
    ) -> List[ProcessingResult]:
        """
        Process multiple documents in parallel
        
        Args:
            document_ids: List of document IDs to process
            options: Processing configuration options
            max_concurrency: Maximum parallel processing tasks
            
        Returns:
            List of ProcessingResults
        """
        pass
```

#### LLM Provider Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class LLMResponse(BaseModel):
    """Standardized LLM response"""
    content: str
    tokens_used: int
    cost: float
    model: str
    finish_reason: str

class StructuredOutput(BaseModel):
    """Structured output from LLM"""
    data: Dict[str, Any]
    confidence: float
    tokens_used: int
    cost: float

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.3,
        **kwargs
    ) -> StructuredOutput:
        """Generate structured output matching schema"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost for token usage"""
        pass
```

#### Paperless API Client Interface

```python
from typing import Optional, List, Dict, Any
from datetime import datetime

class PaperlessClient:
    """Client for Paperless-ngx API"""
    
    async def get_document(self, document_id: int) -> Document:
        """Fetch document by ID"""
        pass
    
    async def get_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """Fetch documents with optional filters"""
        pass
    
    async def update_document(
        self,
        document_id: int,
        title: Optional[str] = None,
        tags: Optional[List[int]] = None,
        correspondent: Optional[int] = None,
        document_type: Optional[int] = None,
        created_date: Optional[datetime] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Update document metadata"""
        pass
    
    async def get_or_create_tag(
        self,
        name: str,
        color: str = "#3498db"
    ) -> Tag:
        """Get existing tag or create new one"""
        pass
    
    async def get_or_create_correspondent(
        self, name: str
    ) -> Correspondent:
        """Get existing correspondent or create new one"""
        pass
    
    async def download_document_content(
        self, document_id: int
    ) -> str:
        """Download OCR text content"""
        pass
```

### 5.2 Processing Options

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ProcessingOptions:
    """Configuration for document processing"""
    
    # Feature flags
    enable_title_generation: bool = True
    enable_tagging: bool = True
    enable_metadata_extraction: bool = True
    enable_categorization: bool = True
    enable_summarization: bool = False
    
    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2000
    
    # Tagging settings
    use_rule_based_tagging: bool = True
    use_llm_tagging: bool = True
    tag_confidence_threshold: float = 0.7
    max_tags_per_document: int = 10
    
    # Processing settings
    skip_if_title_exists: bool = True
    skip_if_tags_exist: bool = False
    overwrite_existing: bool = False
    
    # Summary settings
    summary_max_length: int = 500
    summary_style: str = "concise"  # concise, detailed, bullet_points
    
    # Error handling
    retry_attempts: int = 3
    retry_delay: float = 1.0
    continue_on_error: bool = True
```

---

## 6. Configuration Schema

### 6.1 Main Configuration File (`config.yaml`)

```yaml
# Paperless-ngx Configuration
paperless:
  url: "http://localhost:8000"
  api_token: "${PAPERLESS_API_TOKEN}"  # From environment variable
  verify_ssl: true
  timeout: 30
  max_retries: 3
  
# LLM Provider Configuration
llm:
  primary_provider: "openai"
  fallback_provider: "ollama"  # Optional fallback
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4-turbo-preview"
    temperature: 0.3
    max_tokens: 2000
    organization: ""  # Optional
    
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet-20240229"
    temperature: 0.3
    max_tokens: 2000
    
  ollama:
    base_url: "http://localhost:11434"
    model: "llama2"
    temperature: 0.3
    max_tokens: 2000

# Processing Configuration
processing:
  # Feature toggles
  features:
    title_generation: true
    tagging: true
    metadata_extraction: true
    categorization: true
    summarization: false
    
  # Processing rules
  rules:
    skip_if_title_exists: true
    skip_if_tagged: false
    overwrite_existing_metadata: false
    
  # Batch processing
  batch:
    enabled: true
    batch_size: 10
    max_concurrent_processes: 5
    process_on_startup: false
    
  # Document filtering
  filters:
    exclude_tags: ["processed", "manual"]
    include_document_types: []  # Empty means all types
    min_document_age_hours: 0  # Process immediately
    
# Tagging Configuration
tagging:
  rule_based:
    enabled: true
    rules_file: "config/rules/tagging_rules.yaml"
    
  llm_based:
    enabled: true
    confidence_threshold: 0.7
    max_tags_per_document: 10
    use_existing_tags_as_context: true
    
  tag_creation:
    auto_create_tags: true
    tag_color_scheme: "categorical"  # categorical, random, fixed
    default_color: "#3498db"

# Metadata Extraction Configuration
metadata:
  date_extraction:
    enabled: true
    prefer_document_date_over_content: false
    date_formats: ["DD.MM.YYYY", "YYYY-MM-DD", "MM/DD/YYYY"]
    
  correspondent_extraction:
    enabled: true
    auto_create_correspondents: true
    use_existing_correspondents: true
    confidence_threshold: 0.8
    
  custom_fields:
    invoice_number:
      enabled: true
      field_type: "text"
      extract_pattern: "\\b(Invoice|Rechnung)[\\s#:-]*(\\d+)\\b"
      
    amount:
      enabled: true
      field_type: "monetary"
      extract_pattern: "\\b(\\d+[.,]\\d{2})\\s*€\\b"

# Summarization Configuration
summarization:
  enabled: false
  max_length: 500
  style: "concise"  # concise, detailed, bullet_points
  languages: ["de", "en"]
  store_in_custom_field: "summary"

# Watcher Configuration
watcher:
  enabled: false
  mode: "webhook"  # webhook or polling
  
  polling:
    interval_seconds: 60
    check_for_new_documents: true
    
  webhook:
    enabled: true
    host: "0.0.0.0"
    port: 8080
    path: "/webhook/paperless"
    secret: "${WEBHOOK_SECRET}"

# Caching Configuration
cache:
  enabled: true
  backend: "memory"  # memory, redis
  ttl_seconds: 3600
  
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: "${REDIS_PASSWORD}"

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "json"  # json, text
  output: "file"  # file, console, both
  
  file:
    path: "logs/better-paperless.log"
    max_size_mb: 100
    backup_count: 5
    rotation: "daily"  # daily, size
    
  structured_logging:
    enabled: true
    include_context: true

# Monitoring & Metrics
monitoring:
  enabled: true
  metrics_port: 9090
  
  prometheus:
    enabled: true
    
  statistics:
    track_processing_time: true
    track_llm_costs: true
    track_success_rate: true

# Notification Configuration
notifications:
  enabled: false
  
  email:
    enabled: false
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    from_address: "noreply@example.com"
    to_addresses: ["admin@example.com"]
    
  webhook:
    enabled: false
    url: "https://hooks.example.com/better-paperless"
    on_error: true
    on_success: false
```

### 6.2 Tagging Rules File (`config/rules/tagging_rules.yaml`)

```yaml
# Rule-based Tagging Configuration
# Rules are evaluated in order and all matching rules apply

rules:
  # Financial documents
  - name: "Invoice Detection"
    patterns:
      - regex: "\\b(invoice|rechnung|factura)\\b"
        case_insensitive: true
    tags: ["invoice", "financial"]
    priority: 10
    
  - name: "Bank Statement"
    patterns:
      - regex: "\\b(bank statement|kontoauszug)\\b"
        case_insensitive: true
    tags: ["bank-statement", "financial"]
    priority: 10
    
  - name: "Receipt"
    patterns:
      - regex: "\\b(receipt|quittung|bon)\\b"
        case_insensitive: true
    tags: ["receipt", "financial"]
    priority: 10
    
  # Utilities
  - name: "Electricity Bill"
    patterns:
      - regex: "\\b(electricity|strom|energie)\\b"
        case_insensitive: true
      - regex: "\\b(bill|rechnung)\\b"
        case_insensitive: true
    tags: ["utility", "electricity"]
    priority: 8
    
  - name: "Water Bill"
    patterns:
      - regex: "\\b(water|wasser)\\b"
        case_insensitive: true
      - regex: "\\b(bill|rechnung)\\b"
        case_insensitive: true
    tags: ["utility", "water"]
    priority: 8
    
  # Insurance
  - name: "Insurance Documents"
    patterns:
      - regex: "\\b(insurance|versicherung)\\b"
        case_insensitive: true
    tags: ["insurance"]
    priority: 9
    
  # Healthcare
  - name: "Medical Documents"
    patterns:
      - regex: "\\b(medical|doctor|arzt|kranken)\\b"
        case_insensitive: true
    tags: ["healthcare"]
    priority: 9
    
  # Contracts
  - name: "Contracts"
    patterns:
      - regex: "\\b(contract|vertrag|agreement)\\b"
        case_insensitive: true
    tags: ["contract"]
    priority: 10
    
  # Tax documents
  - name: "Tax Documents"
    patterns:
      - regex: "\\b(tax|steuer|finanzamt)\\b"
        case_insensitive: true
    tags: ["tax", "important"]
    priority: 10
    
# Tag aliases - map similar tags to standard tags
tag_aliases:
  "bill": "invoice"
  "rechnung": "invoice"
  "factura": "invoice"
  "statement": "bank-statement"

# Tag hierarchy - parent-child relationships
tag_hierarchy:
  financial:
    - invoice
    - receipt
    - bank-statement
    - tax
  utility:
    - electricity
    - water
    - gas
    - internet
  personal:
    - healthcare
    - insurance
    - contract
```

### 6.3 Prompt Templates (`config/prompts/title_generation.yaml`)

```yaml
# Title Generation Prompts

default_prompt: |
  You are a document management assistant. Generate a concise, descriptive title for the following document.
  
  The title should:
  - Be clear and specific
  - Include key information (date, sender, type)
  - Be under 100 characters
  - Follow this pattern when applicable: "Type - Key Info - Date"
  
  Document content:
  {content}
  
  Existing tags: {tags}
  Document type: {document_type}
  
  Generate only the title, nothing else.

invoice_prompt: |
  Generate a title for this invoice document. Use this format:
  "Invoice - [Company/Sender] - [Date] - [Amount if available]"
  
  Document content:
  {content}
  
  Title:

contract_prompt: |
  Generate a title for this contract document. Use this format:
  "Contract - [Party] - [Contract Type] - [Start Date]"
  
  Document content:
  {content}
  
  Title:

statement_prompt: |
  Generate a title for this statement document. Use this format:
  "Statement - [Institution] - [Period] - [Account]"
  
  Document content:
  {content}
  
  Title:

# Language-specific prompts
language_prompts:
  de: |
    Du bist ein Dokumentenverwaltungsassistent. Erstelle einen prägnanten, beschreibenden Titel für das folgende Dokument.
    
    Der Titel sollte:
    - Klar und spezifisch sein
    - Wichtige Informationen enthalten (Datum, Absender, Typ)
    - Unter 100 Zeichen lang sein
    
    Dokumentinhalt:
    {content}
    
    Titel:
```

---

## 7. Example Workflows

### 7.1 Workflow 1: Single Document Processing

**Scenario:** Process a newly uploaded invoice

```bash
# Step 1: Upload document to Paperless (manual or automatic)
# Document ID: 1234

# Step 2: Process the document
better-paperless process 1234

# Internal Flow:
# 1. Fetch document from Paperless API
# 2. Download OCR text content
# 3. Generate title: "Invoice - Acme Corp - 2024-03-15 - €1,234.56"
# 4. Extract metadata:
#    - Date: 2024-03-15
#    - Correspondent: Acme Corp
#    - Amount: €1,234.56
# 5. Generate tags: [invoice, financial, acme-corp]
# 6. Categorize: Document Type = "Invoice"
# 7. Update document in Paperless
# 8. Output result:

# OUTPUT:
# ✓ Document 1234 processed successfully
#   Title: Invoice - Acme Corp - 2024-03-15 - €1,234.56
#   Tags: invoice, financial, acme-corp
#   Correspondent: Acme Corp
#   Document Type: Invoice
#   Created Date: 2024-03-15
#   LLM Tokens: 1,234 ($0.015)
#   Processing Time: 3.2s
```

### 7.2 Workflow 2: Batch Processing Existing Documents

**Scenario:** Process all unprocessed documents from last month

```bash
# Process documents without titles from the last 30 days
better-paperless batch \
  --filter "created__gte=30d" \
  --filter "title__isnull=true" \
  --concurrency 5

# Internal Flow:
# 1. Query Paperless for matching documents
# 2. Queue documents for processing
# 3. Process in parallel (5 at a time)
# 4. Track progress and errors
# 5. Generate summary report

# OUTPUT:
# Processing 47 documents...
# [████████████████████░░░░] 85% (40/47)
# 
# Results:
#   ✓ Successful: 40
#   ⚠ Failed: 5
#   ⏱ Total Time: 2m 34s
#   💰 Total Cost: $1.23
#   
# Failed Documents:
#   - Document 1250: LLM timeout
#   - Document 1251: Invalid OCR text
#   - Document 1255: API error
#   - Document 1260: Missing content
#   - Document 1265: Rate limit exceeded
#
# Retry failed documents? [Y/n]: Y
# Retrying 5 documents...
# ✓ All documents processed successfully
```

### 7.3 Workflow 3: Watch Mode for Continuous Processing

**Scenario:** Automatically process new documents as they arrive

```bash
# Start watcher in webhook mode
better-paperless watch --mode webhook --port 8080

# Internal Flow:
# 1. Start HTTP server listening on port 8080
# 2. Wait for webhook from Paperless
# 3. On webhook received:
#    a. Extract document ID
#    b. Verify webhook signature
#    c. Queue document for processing
#    d. Process document asynchronously
#    e. Send response to Paperless
# 4. Continue listening

# OUTPUT:
# ✓ Watcher started successfully
#   Mode: webhook
#   Host: 0.0.0.0:8080
#   Endpoint: /webhook/paperless
#   
# Waiting for documents...
# 
# [2024-03-15 10:23:45] Received webhook for document 1234
# [2024-03-15 10:23:45] Processing document 1234...
# [2024-03-15 10:23:48] ✓ Document 1234 processed
# 
# [2024-03-15 10:25:12] Received webhook for document 1235
# [2024-03-15 10:25:12] Processing document 1235...
# [2024-03-15 10:25:15] ✓ Document 1235 processed
```

### 7.4 Workflow 4: Tag Synchronization

**Scenario:** Sync existing tags and create missing ones

```bash
# Analyze existing documents and sync tags
better-paperless tags sync --analyze

# Internal Flow:
# 1. Fetch all documents from Paperless
# 2. Analyze tag patterns
# 3. Identify common tags that should exist
# 4. Create missing tags
# 5. Update tag hierarchy

# OUTPUT:
# Analyzing 1,234 documents...
# 
# Found tags in use: 45
# Suggested new tags: 12
#   - utility-internet (used implicitly in 23 documents)
#   - healthcare-prescription (used implicitly in 15 documents)
#   - tax-2024 (referenced in 18 documents)
#   ...
#
# Create suggested tags? [Y/n]: Y
# ✓ Created 12 new tags
# ✓ Updated tag hierarchy
# ✓ Sync complete
```

### 7.5 Workflow 5: Custom Processing with Overrides

**Scenario:** Reprocess documents with custom settings

```bash
# Reprocess invoices with summarization enabled
better-paperless batch \
  --filter "tags__name=invoice" \
  --enable-summarization \
  --summary-style detailed \
  --llm-model gpt-4-turbo-preview \
  --overwrite-existing

# Internal Flow:
# 1. Query for documents tagged with "invoice"
# 2. Override default processing options
# 3. Process each document with summarization
# 4. Store summaries in custom field
# 5. Generate report

# OUTPUT:
# Processing 156 invoices...
# Configuration:
#   LLM Model: gpt-4-turbo-preview
#   Summarization: Enabled (detailed)
#   Overwrite: Yes
#
# [████████████████████████] 100% (156/156)
#
# Results:
#   ✓ Processed: 156
#   ✓ Summaries Generated: 156
#   💰 Total Cost: $4.23
#   ⏱ Average Time: 4.2s per document
```

---

## 8. Dependencies

### 8.1 Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"

# HTTP & API
httpx = "^0.27.0"              # Async HTTP client
aiohttp = "^3.9.0"             # Alternative async HTTP
requests = "^2.31.0"           # Sync HTTP fallback

# LLM Providers
openai = "^1.12.0"             # OpenAI API
anthropic = "^0.18.0"          # Anthropic API
ollama = "^0.1.6"              # Ollama local models

# Data Validation & Serialization
pydantic = "^2.6.0"            # Data validation
pydantic-settings = "^2.2.0"   # Settings management

# CLI
typer = "^0.9.0"               # CLI framework
rich = "^13.7.0"               # Rich terminal output
click = "^8.1.7"               # CLI utilities

# Configuration
pyyaml = "^6.0.1"              # YAML parsing
python-dotenv = "^1.0.1"       # Environment variables

# Async & Concurrency
asyncio = "^3.4.3"             # Async programming
aiofiles = "^23.2.1"           # Async file operations

# Text Processing
regex = "^2023.12.25"          # Advanced regex
langdetect = "^1.0.9"          # Language detection
python-dateutil = "^2.8.2"     # Date parsing

# Caching
redis = "^5.0.1"               # Redis client
aiocache = "^0.12.2"           # Async caching

# Logging & Monitoring
structlog = "^24.1.0"          # Structured logging
prometheus-client = "^0.19.0"  # Prometheus metrics

# Task Scheduling
apscheduler = "^3.10.4"        # Job scheduling
watchdog = "^4.0.0"            # File system monitoring

# Utilities
tenacity = "^8.2.3"            # Retry logic
backoff = "^2.2.1"             # Exponential backoff
```

### 8.2 Development Dependencies

```toml
[tool.poetry.group.dev.dependencies]
# Testing
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
pytest-httpx = "^0.29.0"

# Code Quality
black = "^24.1.0"              # Code formatting
isort = "^5.13.0"              # Import sorting
flake8 = "^7.0.0"              # Linting
mypy = "^1.8.0"                # Type checking
pylint = "^3.0.0"              # Additional linting

# Documentation
mkdocs = "^1.5.0"              # Documentation
mkdocs-material = "^9.5.0"     # Material theme
mkdocstrings = "^0.24.0"       # API docs

# Development Tools
ipython = "^8.21.0"            # Enhanced REPL
pre-commit = "^3.6.0"          # Git hooks
```

### 8.3 Optional Dependencies

```toml
[tool.poetry.extras]
all = ["redis", "prometheus-client", "sentry-sdk"]
monitoring = ["prometheus-client", "sentry-sdk"]
distributed = ["redis", "celery"]
```

---

## 9. Deployment Strategy

### 9.1 Docker Deployment (Recommended)

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY config/ ./config/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Create non-root user
RUN useradd -m -u 1000 paperless && \
    chown -R paperless:paperless /app

USER paperless

# Expose ports
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "-m", "better_paperless", "watch"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  better-paperless:
    build: .
    container_name: better-paperless
    restart: unless-stopped
    
    environment:
      # Paperless Configuration
      PAPERLESS_API_URL: http://paperless:8000
      PAPERLESS_API_TOKEN: ${PAPERLESS_API_TOKEN}
      
      # LLM Configuration
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      
      # Redis Configuration
      REDIS_URL: redis://redis:6379/0
      
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./data:/app/data
      
    ports:
      - "8080:8080"
      - "9090:9090"  # Prometheus metrics
      
    depends_on:
      - redis
      - paperless
      
    networks:
      - paperless-network
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: better-paperless-redis
    restart: unless-stopped
    
    volumes:
      - redis-data:/data
      
    networks:
      - paperless-network
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 3s
      retries: 3

  # Existing Paperless-ngx service
  paperless:
    image: ghcr.io/paperless-ngx/paperless-ngx:latest
    # ... existing paperless configuration ...
    
    networks:
      - paperless-network

volumes:
  redis-data:

networks:
  paperless-network:
    driver: bridge
```

### 9.2 Poetry Local Development

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone repository
git clone https://github.com/yourusername/better-paperless.git
cd better-paperless

# Install dependencies
poetry install

# Copy example configuration
cp config/config.example.yaml config/config.yaml
cp .env.example .env

# Edit configuration and environment variables
nano config/config.yaml
nano .env

# Run in development mode
poetry run better-paperless watch

# Run tests
poetry run pytest

# Format code
poetry run black src/
poetry run isort src/
```

### 9.3 Systemd Service (Linux)

```ini
# /etc/systemd/system/better-paperless.service

[Unit]
Description=Better Paperless - Automated Document Processing
After=network.target paperless.service

[Service]
Type=simple
User=paperless
Group=paperless
WorkingDirectory=/opt/better-paperless
Environment="PATH=/opt/better-paperless/.venv/bin"
ExecStart=/opt/better-paperless/.venv/bin/python -m better_paperless watch
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=better-paperless

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/better-paperless/logs /opt/better-paperless/data

[Install]
WantedBy=multi-user.target
```

### 9.4 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: better-paperless
  namespace: paperless
spec:
  replicas: 2
  selector:
    matchLabels:
      app: better-paperless
  template:
    metadata:
      labels:
        app: better-paperless
    spec:
      containers:
      - name: better-paperless
        image: better-paperless:latest
        ports:
        - containerPort: 8080
        - containerPort: 9090
        env:
        - name: PAPERLESS_API_URL
          value: "http://paperless-service:8000"
        - name: PAPERLESS_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: paperless-secrets
              key: api-token
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-api-key
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: better-paperless-config
      - name: logs
        persistentVolumeClaim:
          claimName: better-paperless-logs
```

---

## 10. Security Considerations

### 10.1 API Key Management

- Store API keys in environment variables, never in code
- Use secret management systems (Vault, AWS Secrets Manager)
- Rotate keys regularly
- Implement key expiration monitoring

### 10.2 Data Protection

- Encrypt sensitive data at rest
- Use TLS for all API communications
- Implement proper access controls
- Regular security audits of dependencies

### 10.3 Paperless Integration Security

- Validate webhook signatures
- Implement rate limiting
- Use read-only API tokens where possible
- Audit all document modifications

### 10.4 LLM Security

- Never send actual document content to LLM without user consent
- Implement content filtering
- Monitor for prompt injection attempts
- Log all LLM interactions for audit

---

## 11. Future Enhancements

### Phase 2 Features

1. **Machine Learning**
   - Train custom models for document classification
   - Learn from user corrections
   - Improve tagging accuracy over time

2. **Advanced OCR**
   - Integrate with external OCR services
   - Handle handwritten documents
   - Multi-column layout detection

3. **Workflow Automation**
   - Custom workflow definitions
   - Conditional processing rules
   - Integration with external systems

4. **Web UI**
   - Dashboard for monitoring
   - Configuration management interface
   - Processing history and analytics

5. **Multi-tenancy**
   - Support multiple Paperless instances
   - User-specific configurations
   - Shared tag libraries

### Phase 3 Features

1. **AI-Powered Features**
   - Question-answering over documents
   - Document relationship detection
   - Duplicate detection
   - Smart search suggestions

2. **Enterprise Features**
   - LDAP/SSO integration
   - Advanced audit logging
   - Compliance reporting
   - SLA monitoring

3. **Performance Optimization**
   - Distributed processing
   - GPU acceleration for OCR
   - Advanced caching strategies
   - Database optimization

---

## Appendix A: API Endpoints Reference

### Paperless-ngx API Endpoints Used

```
GET    /api/documents/                    # List documents
GET    /api/documents/{id}/               # Get document
PATCH  /api/documents/{id}/               # Update document
GET    /api/documents/{id}/download/      # Download document
GET    /api/tags/                         # List tags
POST   /api/tags/                         # Create tag
GET    /api/correspondents/               # List correspondents
POST   /api/correspondents/               # Create correspondent
GET    /api/document_types/               # List document types
POST   /api/document_types/               # Create document type
```

### Better Paperless Internal Endpoints

```
POST   /webhook/paperless                 # Webhook receiver
GET    /health                            # Health check
GET    /ready                             # Readiness check
GET    /metrics                           # Prometheus metrics
GET    /api/v1/status                     # Processing status
POST   /api/v1/process/{document_id}      # Process document
GET    /api/v1/stats                      # Statistics
```

---

## Appendix B: Error Codes

```
E001: Paperless API connection error
E002: Invalid API token
E003: Document not found
E004: LLM API error
E005: Rate limit exceeded
E006: Invalid configuration
E007: Processing timeout
E008: Insufficient permissions
E009: Invalid document format
E010: Cache error
```

---

## Conclusion

This architecture provides a solid foundation for building a comprehensive document automation system for Paperless-ngx. The modular design allows for incremental implementation and easy extension. The focus on reliability, security, and maintainability ensures long-term success of the project.

**Next Steps:**
1. Review and approve this architecture plan
2. Set up development environment
3. Implement core modules iteratively
4. Test with sample documents
5. Deploy and monitor