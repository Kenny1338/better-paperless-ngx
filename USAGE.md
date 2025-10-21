# Better Paperless - Complete Usage Guide

## 🎯 What Better Paperless Does AUTOMATICALLY

Better Paperless reads **EVERY document completely with OCR** and analyzes it with GPT-4 to:

### 1. Generate Intelligent Titles
**Example:**
- Input: OCR text of a broadcast fee invoice
- Output: "Payment Request Broadcasting Fee - Contribution Number 293 963 730 - 15.10.2025"

### 2. Create Dynamic Tags (100% LLM, NO Rules!)
**Example for Broadcasting Fee:**
- `ard`, `contribution-number`, `contribution-service`, `bank-transfer`
- `deutschlandradio`, `due-date`, `broadcasting-fee`
- `sepa-direct-debit`, `late-fee`, `payment-request`
- `payment-receipt`, `zdf`

**Example for Tax Document:**
- `tax-office`, `tax-return`, `elster`, `filing-deadline`
- `late-fee`, `delay-surcharge`, `enforcement`

**Example for Energy Payment Reminder:**
- `enbw`, `reminder`, `electromobility`, `legal-proceedings`
- `debt-collection`, `receivables-management`, `outstanding-amount`

### 3. Automatically Recognize Vendors/Correspondents
**Automatically created:**
- "ARD ZDF Deutschlandradio Beitragsservice"
- "Tax Office Mannheim-Neckarstadt"
- "EnBW Energie Baden-Württemberg AG"
- "ENSTROGA AG"

### 4. Extract All Metadata
- **Document Date**: When it was created
- **Amount**: e.g., €55.08
- **Currency**: EUR, USD, etc.
- **Invoice Number**: e.g., "293 963 730"
- **Due Date**: Payment deadline

## 🔄 Smart Processing - No Duplicates!

The system automatically sets a **"bp-processed"** tag after processing.

### First Run:
```bash
python -m poetry run better-paperless batch
# Processed: 4 documents
# Time: ~40 seconds
# Cost: ~$0.06
```

### Second Run:
```bash
python -m poetry run better-paperless batch
# Skipped: 4 documents (already processed!)
# Time: 0.14 seconds
# Cost: $0.00
```

**Log Output:**
```json
{
  "document_id": 1,
  "reason": "Has 'bp-processed' tag",
  "event": "document_already_processed"
}
```

## 📋 Commands

### Process Single Document
```bash
python -m poetry run better-paperless process <ID>

# Example:
python -m poetry run better-paperless process 5
```

### Batch Process All Documents
```bash
python -m poetry run better-paperless batch
```

### Only New Documents (without bp-processed tag)
```bash
# Automatic - the system skips already processed documents!
python -m poetry run better-paperless batch
```

### Reprocess Documents (Force)
```yaml
# In config/config.yaml temporarily change:
processing:
  rules:
    skip_if_processed_tag: false  # Ignore bp-processed tag
```

Then:
```bash
python -m poetry run better-paperless batch
```

### Test Connection
```bash
python -m poetry run better-paperless test-connection
```

### Validate Configuration
```bash
python -m poetry run better-paperless config validate
```

## ⚙️ Current Configuration

### Fully Automatic & Dynamic
```yaml
processing:
  features:
    title_generation: true      # ✓ LLM generates titles
    tagging: true               # ✓ LLM creates tags
    metadata_extraction: true   # ✓ LLM extracts metadata
    
  rules:
    skip_if_title_exists: false       # Overwrites old titles
    overwrite_existing_metadata: true # Overwrites old data
    processed_tag: "bp-processed"     # Marker tag
    skip_if_processed_tag: true       # No duplicate processing!

tagging:
  rule_based:
    enabled: false  # ✗ NO hardcoded rules!
  llm_based:
    enabled: true   # ✓ ONLY LLM decides!
    max_tags_per_document: 15
```

## 💡 What the System Understands

Better Paperless reads the **complete OCR text** and understands:

- **Document Type**: Invoice, reminder, contract, tax document
- **Sender**: Companies, authorities, service providers
- **Context**: Payment request, reminder, filing deadline
- **Important Data**: Amounts, numbers, dates
- **Language**: German, English, etc.

## 📊 Example Output

### Document 1: Broadcasting Fee
```
✓ Successfully processed
├─ Title: "Payment Request Broadcasting Fee - Contribution Number 293 963 730 - 15.10.2025"
├─ Correspondent: ARD ZDF Deutschlandradio Beitragsservice
├─ Date: 2025-09-23
├─ Amount: €55.08
├─ Invoice No: 293 963 730
├─ Due: 2025-10-15
└─ Tags (13):
    ard, contribution-number, contribution-service, bank-transfer,
    deutschlandradio, online-service, broadcasting-fee,
    sepa-direct-debit, payment-receipt, zdf, bp-processed
```

### Document 2: Tax Document
```
✓ Successfully processed
├─ Title: "Reminder to File Tax Return - Tax Office Mannheim-Neckarstadt - 09.10.2025"
├─ Correspondent: Tax Office Mannheim-Neckarstadt
├─ Date: 2025-10-09
├─ Invoice No: 8653*0010791
├─ Due: 2025-11-10
└─ Tags (15):
    tax-office, tax-return, elster, filing-deadline,
    enforcement, late-fee, reminder, bp-processed
```

### Document 3: EnBW Reminder
```
✓ Successfully processed
├─ Title: "Reminder - EnBW mobility+ Outstanding Amount - October 21, 2025"
├─ Correspondent: EnBW Energie Baden-Württemberg AG
├─ Date: 2025-10-21
├─ Amount: €163.60
├─ Invoice No: DE-NBW-C10524599-X
├─ Due: 2025-10-28
└─ Tags (16):
    enbw, reminder, electromobility, legal-proceedings,
    debt-collection, receivables-management, outstanding-amount, bp-processed
```

### Document 4: Gas Payment Reminder
```
✓ Successfully processed
├─ Title: "Payment Reminder - ENSTROGA AG - October 2025 - 21.10.2025"
├─ Correspondent: ENSTROGA AG
├─ Date: 2025-10-21
├─ Amount: €77.14
├─ Invoice No: 3F53J3045
├─ Due: 2025-10-28
└─ Tags (16):
    energy-supplier, gas-supply-contract, payment-reminder,
    sepa-direct-debit, outstanding-claim, bp-processed
```

## 🚀 Automation

### Option 1: Manual Trigger
```bash
# After uploading new documents
python -m poetry run better-paperless batch
```

### Option 2: Automatic with Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Every morning at 8 AM
0 8 * * * cd /path/to/better-paperless && python -m poetry run better-paperless batch
```

### Option 3: Windows Task Scheduler
1. Open Task Scheduler
2. Create new task
3. Program: `C:\Python312\python.exe`
4. Arguments: `-m poetry run better-paperless batch`
5. Working Directory: `C:\Users\...\better-paperless`
6. Trigger: Daily at 8:00

### Option 4: Docker with Cron
```dockerfile
# In docker/Dockerfile
CMD ["python", "-m", "better_paperless", "batch", "--concurrency", "5"]
```

Then with docker-compose as cron job:
```yaml
services:
  better-paperless-cron:
    build: .
    command: ["sh", "-c", "while true; do python -m better_paperless batch && sleep 3600; done"]
```

## 💰 Costs

**Per Document (GPT-4 Turbo):**
- Title: ~$0.008
- Metadata: ~$0.008  
- Tags: ~$0.010
- **Total: ~$0.025 per document**

**Batch of 100 Documents:**
- Cost: ~$2.50
- Time: ~15-20 minutes (with concurrency 5)

**Cheaper with GPT-3.5:**
```yaml
# In config.yaml:
llm:
  openai:
    model: "gpt-3.5-turbo"  # ~10x cheaper!
```

Then: ~$0.003 per document!

## 🔧 Customizing Configuration

### More Tags per Document
```yaml
tagging:
  llm_based:
    max_tags_per_document: 20  # Default: 15
```

### Higher Concurrency (faster)
```yaml
processing:
  batch:
    max_concurrent_processes: 10  # Default: 5
```

### Enable Summarization
```yaml
processing:
  features:
    summarization: true

summarization:
  enabled: true
  max_length: 500
  style: "concise"  # or "detailed", "bullet_points"
```

## 🎯 Best Practices

1. **First Use**: Test with a single document
   ```bash
   python -m poetry run better-paperless process 1
   ```

2. **Small Batches**: Start with a few documents
   ```bash
   python -m poetry run better-paperless batch --limit 10
   ```

3. **Monitor Costs**: Check output after each batch

4. **Use bp-processed**: Let the system avoid duplicates

5. **Backup**: Make a Paperless backup before large batch runs

## ❓ FAQ

**Q: Are documents processed twice?**
A: No! The `bp-processed` tag prevents this.

**Q: Can I change the processed tag?**
A: Yes, in `config.yaml`: `processed_tag: "my-tag"`

**Q: What happens if a document fails?**
A: It's skipped, no `bp-processed` tag is set, will retry on next batch.

**Q: Does it really use OCR?**
A: Yes! Paperless does OCR, Better Paperless reads the complete OCR text.

**Q: Can I only process new documents?**
A: Yes! The system automatically skips documents with `bp-processed` tag.

## 🎉 Done!

Your system is now fully automated. New documents will be:
1. Scanned by Paperless (OCR)
2. Analyzed by Better Paperless (LLM)
3. Automatically tagged with title, tags, vendor, metadata
4. Marked with `bp-processed` (no duplicates)

**Good luck! 🚀**