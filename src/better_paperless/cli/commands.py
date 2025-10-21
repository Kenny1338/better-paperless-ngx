"""CLI commands for Better Paperless."""

import asyncio
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

# Disable Rich features on Windows to avoid encoding issues
console = Console(force_terminal=True, legacy_windows=False) if sys.platform != "win32" else Console(no_color=True, legacy_windows=True)

from ..api.client import PaperlessClient
from ..core.config import Config
from ..core.logger import setup_logging
from ..llm.factory import LLMFactory
from ..processors.agentic_processor import AgenticDocumentProcessor
from ..processors.document_processor import DocumentProcessor

app = typer.Typer(
    name="better-paperless",
    help="Automated Paperless-ngx with LLM Integration",
    add_completion=False,
    rich_markup_mode=None,  # Disable Rich markup to avoid compatibility issues
    pretty_exceptions_enable=False,  # Disable Rich exceptions
)



def get_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration."""
    return Config(config_path)


@app.command()
def process(
    document_id: int = typer.Argument(..., help="Document ID to process"),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """Process a single document."""
    asyncio.run(_process_document(document_id, config_path))


async def _process_document(document_id: int, config_path: Optional[Path]) -> None:
    """Async process document."""
    # Load configuration
    config = get_config(config_path)
    setup_logging(level=config.get("logging.level", "INFO"))

    console.print(f"[bold blue]Processing document {document_id}...[/bold blue]")

    try:
        # Initialize clients
        async with PaperlessClient(
            base_url=config.paperless.api_url,
            api_token=config.paperless.api_token,
            verify_ssl=config.paperless.verify_ssl,
        ) as paperless:
            llm = LLMFactory.create_from_config(config)
            options = config.get_processing_options()

            processor = DocumentProcessor(paperless, llm, options)

            # Process document
            print("Processing document...")
            result = await processor.process_document(document_id)

            # Display results
            if result.success:
                console.print("[bold green]OK Processing successful![/bold green]")

                table = Table(title="Processing Results")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")

                if result.title:
                    table.add_row("Title", result.title)
                if result.tags:
                    table.add_row("Tags", ", ".join(result.tags))
                if result.correspondent:
                    table.add_row("Correspondent", result.correspondent)
                if result.metadata:
                    for key, value in result.metadata.items():
                        table.add_row(key.replace("_", " ").title(), str(value))

                table.add_row("Processing Time", f"{result.processing_time:.2f}s")
                table.add_row("LLM Tokens", str(result.llm_tokens_used))
                table.add_row("LLM Cost", f"${result.llm_cost:.4f}")

                console.print(table)
            else:
                console.print("[bold red]X Processing failed[/bold red]")
                for error in result.errors:
                    console.print(f"[red]  • {error}[/red]")

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def batch(
    filter_query: Optional[str] = typer.Option(
        None, "--filter", "-f", help="Filter query for documents"
    ),
    all_documents: bool = typer.Option(False, "--all", help="Process all documents"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum documents to process"),
    concurrency: int = typer.Option(5, "--concurrency", help="Number of concurrent processes"),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """Process multiple documents in batch."""
    asyncio.run(_process_batch(filter_query, all_documents, limit, concurrency, config_path))


async def _process_batch(
    filter_query: Optional[str],
    all_documents: bool,
    limit: int,
    concurrency: int,
    config_path: Optional[Path],
) -> None:
    """Async batch processing."""
    config = get_config(config_path)
    setup_logging(level=config.get("logging.level", "INFO"))

    console.print("[bold blue]Starting batch processing...[/bold blue]")

    try:
        async with PaperlessClient(
            base_url=config.paperless.api_url,
            api_token=config.paperless.api_token,
            verify_ssl=config.paperless.verify_ssl,
        ) as paperless:
            # Get documents to process
            filters = {}
            if filter_query:
                # Parse filter query (simplified)
                filters = {"title__isnull": "true"}

            docs_response = await paperless.get_documents(filters=filters, limit=limit)
            document_ids = [doc.id for doc in docs_response.results]

            if not document_ids:
                console.print("[yellow]No documents to process[/yellow]")
                return

            console.print(f"Found {len(document_ids)} documents to process")

            # Initialize processor
            llm = LLMFactory.create_from_config(config)
            options = config.get_processing_options()
            processor = DocumentProcessor(paperless, llm, options)

            # Process in batch
            print(f"Processing {len(document_ids)} documents...")
            results = await processor.process_batch(document_ids, concurrency)

            # Show summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            total_cost = sum(r.llm_cost for r in results)
            avg_time = sum(r.processing_time for r in results) / len(results)

            summary = Table(title="Batch Processing Summary")
            summary.add_column("Metric", style="cyan")
            summary.add_column("Value", style="white")

            summary.add_row("Total Processed", str(len(results)))
            summary.add_row("Successful", f"[green]{successful}[/green]")
            summary.add_row("Failed", f"[red]{failed}[/red]" if failed > 0 else "0")
            summary.add_row("Total Cost", f"${total_cost:.4f}")
            summary.add_row("Avg Time/Doc", f"{avg_time:.2f}s")

            console.print(summary)

            # Show failed documents
            if failed > 0:
                console.print("\n[bold red]Failed Documents:[/bold red]")
                for result in results:
                    if not result.success:
                        console.print(
                            f"  • Document {result.document_id}: {', '.join(result.errors)}"
                        )

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def config(
    action: str = typer.Argument(..., help="Action: validate, show"),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """Manage configuration."""
    if action == "validate":
        _validate_config(config_path)
    elif action == "show":
        _show_config(config_path)
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)


def _validate_config(config_path: Optional[Path]) -> None:
    """Validate configuration."""
    try:
        config = get_config(config_path)
        console.print("[green]OK Configuration is valid[/green]")

        # Show key settings
        table = Table(title="Configuration Summary")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Paperless URL", config.paperless.api_url)
        table.add_row("LLM Provider", config.llm_provider)
        table.add_row("Cache Enabled", str(config.cache_enabled))

        console.print(table)

    except Exception as e:
        console.print(f"[red]X Configuration is invalid: {str(e)}[/red]")
        raise typer.Exit(1)


def _show_config(config_path: Optional[Path]) -> None:
    """Show configuration."""
    import yaml

    config = get_config(config_path)
    console.print("[bold]Current Configuration:[/bold]")
    console.print(yaml.dump(config._config, default_flow_style=False))


@app.command()
def version() -> None:
    """Show version information."""
    from .. import __version__

    console.print(f"Better Paperless v{__version__}")


@app.command()
def agentic(
    document_id: Optional[int] = typer.Argument(None, help="Document ID (if None, processes all)"),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """Process documents using AGENTIC mode - LLM decides everything autonomously."""
    asyncio.run(_agentic_process(document_id, config_path))


async def _agentic_process(document_id: Optional[int], config_path: Optional[Path]) -> None:
    """Agentic processing mode."""
    config = get_config(config_path)
    setup_logging(level=config.get("logging.level", "INFO"))

    console.print("[bold blue]Agentic Processing Mode - LLM decides everything![/bold blue]")

    try:
        async with PaperlessClient(
            base_url=config.paperless.api_url,
            api_token=config.paperless.api_token,
            verify_ssl=config.paperless.verify_ssl,
        ) as paperless:
            llm = LLMFactory.create_from_config(config)
            processor = AgenticDocumentProcessor(paperless, llm)

            if document_id:
                # Process single document
                console.print(f"Processing document {document_id}...")
                result = await processor.process_document(document_id)

                if result.success:
                    console.print("[green]OK Processing successful![/green]")
                    table = Table(title="Agentic Processing Results")
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="white")

                    if result.title:
                        table.add_row("Title", result.title)
                    if result.tags:
                        table.add_row("Tags", ", ".join(result.tags))
                    if result.correspondent:
                        table.add_row("Correspondent", result.correspondent)

                    table.add_row("Processing Time", f"{result.processing_time:.2f}s")
                    table.add_row("LLM Tokens", str(result.llm_tokens_used))
                    table.add_row("LLM Cost", f"${result.llm_cost:.4f}")

                    console.print(table)

                    # Show LLM reasoning/explanation
                    if result.metadata.get("reasoning"):
                        console.print("\n[bold cyan]LLM Analysis Report:[/bold cyan]")
                        console.print(f"[white]{result.metadata['reasoning']}[/white]")

                    # Show custom fields if extracted
                    if result.metadata.get("custom_fields"):
                        console.print("\n[bold cyan]Extracted Data:[/bold cyan]")
                        for key, value in result.metadata["custom_fields"].items():
                            console.print(f"  {key}: {value}")
                else:
                    console.print("[red]X Processing failed[/red]")
                    for error in result.errors:
                        console.print(f"  - {error}")
            else:
                # Process all documents
                docs_response = await paperless.get_documents(limit=100)
                document_ids = [doc.id for doc in docs_response.results]

                if not document_ids:
                    console.print("[yellow]No documents found[/yellow]")
                    return

                console.print(f"Found {len(document_ids)} documents to process")
                console.print("Processing with agentic mode...")

                successful = 0
                failed = 0
                total_cost = 0.0

                for doc_id in document_ids:
                    result = await processor.process_document(doc_id)
                    if result.success:
                        successful += 1
                        total_cost += result.llm_cost
                        print(f"  OK Document {doc_id}")
                    else:
                        failed += 1
                        print(f"  X Document {doc_id}: {', '.join(result.errors)}")

                # Summary
                summary = Table(title="Agentic Batch Summary")
                summary.add_column("Metric", style="cyan")
                summary.add_column("Value", style="white")

                summary.add_row("Total", str(len(document_ids)))
                summary.add_row("Successful", f"{successful}")
                summary.add_row("Failed", f"{failed}")
                summary.add_row("Total Cost", f"${total_cost:.4f}")

                console.print(summary)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def test_connection(
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """Test connection to Paperless-ngx."""
    asyncio.run(_test_connection(config_path))


async def _test_connection(config_path: Optional[Path]) -> None:
    """Test Paperless connection."""
    try:
        config = get_config(config_path)
        
        console.print("[bold blue]Testing Paperless connection...[/bold blue]")
        console.print(f"URL: {config.paperless.api_url}")
        console.print(f"Token: {'*' * 20}{config.paperless.api_token[-4:] if len(config.paperless.api_token) > 4 else '****'}")
        
        async with PaperlessClient(
            base_url=config.paperless.api_url,
            api_token=config.paperless.api_token,
            verify_ssl=config.paperless.verify_ssl,
            timeout=10,
        ) as paperless:
            # Try to fetch documents
            docs = await paperless.get_documents(limit=1)
            console.print(f"[green]OK Connection successful![/green]")
            console.print(f"[green]  Found {docs.count} total documents[/green]")
            
    except Exception as e:
        console.print(f"[red]X Connection failed: {str(e)}[/red]")
        console.print("\n[yellow]Troubleshooting tips:[/yellow]")
        console.print("  1. Check if Paperless is running")
        console.print("  2. Verify the PAPERLESS_API_URL in .env")
        console.print("  3. Verify the PAPERLESS_API_TOKEN is correct")
        console.print("  4. Check firewall/network settings")
        raise typer.Exit(1)


@app.command()
def init(
    path: Path = typer.Option(
        Path("config"), "--path", "-p", help="Configuration directory path"
    ),
) -> None:
    """Initialize configuration files."""
    console.print(f"[bold blue]Initializing configuration in {path}...[/bold blue]")

    path.mkdir(parents=True, exist_ok=True)

    # Create example config
    config_file = path / "config.example.yaml"
    if not config_file.exists():
        config = Config()
        config.save(config_file)
        console.print(f"[green]OK Created {config_file}[/green]")
    else:
        console.print(f"[yellow]  {config_file} already exists[/yellow]")

    console.print("\n[bold green]Configuration initialized successfully![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Copy config.example.yaml to config.yaml")
    console.print("  2. Edit config.yaml with your settings")
    console.print("  3. Set up environment variables (see .env.example)")


@app.command()
def listen(
    interval_hours: int = typer.Option(
        12, "--interval", "-i", help="Check interval in hours"
    ),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """Start listener mode - automatically process new documents every N hours."""
    asyncio.run(_listener_mode(interval_hours, config_path))


async def _listener_mode(interval_hours: int, config_path: Optional[Path]) -> None:
    """Run listener mode with periodic checks and manual sync option."""
    config = get_config(config_path)
    setup_logging(level=config.get("logging.level", "INFO"))

    console.print("[bold blue]═══════════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]   LISTENER MODE - Automatic Document Processing[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════════[/bold blue]")
    console.print(f"\n[cyan]Check interval:[/cyan] Every {interval_hours} hours")
    console.print("[cyan]Manual sync:[/cyan] Press 's' to sync now")
    console.print("[cyan]Stop:[/cyan] Press 'q' to quit\n")

    # Track last check time and processed documents
    last_check_time = None
    processed_doc_ids = set()
    manual_sync_requested = False
    should_quit = False
    next_check_shown = False  # Track if we've shown the next check message

    # Keyboard input handler
    def keyboard_listener():
        """Listen for keyboard input in a separate thread."""
        nonlocal manual_sync_requested, should_quit
        
        try:
            while not should_quit:
                if sys.platform == "win32":
                    # Windows
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                        if key == 's':
                            manual_sync_requested = True
                        elif key == 'q':
                            should_quit = True
                else:
                    # Unix/Linux/Mac
                    import select
                    import tty
                    import termios
                    
                    old_settings = termios.tcgetattr(sys.stdin)
                    try:
                        tty.setcbreak(sys.stdin.fileno())
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1).lower()
                            if key == 's':
                                manual_sync_requested = True
                            elif key == 'q':
                                should_quit = True
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
                time.sleep(0.1)  # Prevent busy loop
        except Exception as e:
            console.print(f"[yellow]Keyboard listener error: {e}[/yellow]")

    # Start keyboard listener in background thread
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()

    try:
        async with PaperlessClient(
            base_url=config.paperless.api_url,
            api_token=config.paperless.api_token,
            verify_ssl=config.paperless.verify_ssl,
        ) as paperless:
            llm = LLMFactory.create_from_config(config)
            processor = AgenticDocumentProcessor(paperless, llm)

            while not should_quit:
                current_time = datetime.now()
                
                # Check if it's time to sync (first run, interval elapsed, or manual request)
                should_sync = (
                    last_check_time is None  # First run
                    or (current_time - last_check_time) >= timedelta(hours=interval_hours)
                    or manual_sync_requested
                )

                if should_sync:
                    if manual_sync_requested:
                        console.print("\n[bold yellow]→ Manual sync requested![/bold yellow]")
                        manual_sync_requested = False
                    
                    console.print(f"\n[bold cyan]→ Checking for new documents... ({current_time.strftime('%Y-%m-%d %H:%M:%S')})[/bold cyan]")
                    
                    try:
                        # Get all documents
                        docs_response = await paperless.get_documents(limit=1000)
                        all_doc_ids = {doc.id for doc in docs_response.results}
                        
                        # Find new documents (not processed yet)
                        new_doc_ids = all_doc_ids - processed_doc_ids
                        
                        if new_doc_ids:
                            console.print(f"[green]✓ Found {len(new_doc_ids)} new document(s)[/green]")
                            
                            # Process each new document
                            successful = 0
                            failed = 0
                            total_cost = 0.0
                            
                            for doc_id in sorted(new_doc_ids):
                                console.print(f"\n[cyan]Processing document {doc_id}...[/cyan]")
                                result = await processor.process_document(doc_id)
                                
                                if result.success:
                                    successful += 1
                                    total_cost += result.llm_cost
                                    processed_doc_ids.add(doc_id)
                                    
                                    console.print(f"[green]  ✓ Document {doc_id} processed successfully[/green]")
                                    if result.title:
                                        console.print(f"[white]    Title: {result.title}[/white]")
                                    if result.tags:
                                        console.print(f"[white]    Tags: {', '.join(result.tags)}[/white]")
                                    if result.correspondent:
                                        console.print(f"[white]    Correspondent: {result.correspondent}[/white]")
                                else:
                                    failed += 1
                                    console.print(f"[red]  ✗ Document {doc_id} failed: {', '.join(result.errors)}[/red]")
                            
                            # Show summary
                            console.print(f"\n[bold]Summary:[/bold]")
                            console.print(f"  Processed: {successful} successful, {failed} failed")
                            console.print(f"  Total cost: ${total_cost:.4f}")
                        else:
                            console.print("[yellow]No new documents found[/yellow]")
                        
                        last_check_time = current_time
                        
                    except Exception as e:
                        console.print(f"[red]✗ Error during sync: {str(e)}[/red]")
                    
                    # Show next check time once after sync
                    next_check = last_check_time + timedelta(hours=interval_hours)
                    time_until_next = (next_check - datetime.now()).total_seconds()
                    
                    if time_until_next > 0:
                        hours = int(time_until_next // 3600)
                        minutes = int((time_until_next % 3600) // 60)
                        console.print(f"\n[dim]Next check in {hours}h {minutes}m (Press 's' to sync now, 'q' to quit)[/dim]")
                    next_check_shown = True
                
                # Sleep in longer intervals to reduce CPU usage
                # Check every 30 seconds for keyboard input
                await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Listener stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error in listener mode: {str(e)}[/red]")
        raise typer.Exit(1)
    finally:
        should_quit = True
        console.print("\n[bold blue]Listener mode stopped[/bold blue]")


if __name__ == "__main__":
    app()