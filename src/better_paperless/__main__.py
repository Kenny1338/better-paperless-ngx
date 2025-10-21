"""Main entry point for Better Paperless."""

from .cli.commands import app


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()