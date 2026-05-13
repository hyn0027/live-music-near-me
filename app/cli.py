import argparse
import logging
import os
from dotenv import load_dotenv
from .core import run_job


def initialize_environment() -> None:
    load_dotenv(override=True)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configuration for the project")

    parser.add_argument(
        "--path",
        type=str,
        default=".asset/bandsintown.html",
        help="Path to the input file",
    )
    parser.add_argument(
        "--log_file",
        type=str,
        default="app.log",
        help="Path to the log file",
    )
    parser.add_argument(
        "--overwrite_log_file",
        action="store_true",
        help="Whether to overwrite the log file on each run (default: False)",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--OPENAI_API_KEY",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (can also be set via environment variable OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--even_db_path",
        type=str,
        default=".asset/event_db.json",
        help="Path to the event database file",
    )
    parser.add_argument(
        "--area",
        type=str,
        default="Austin, TX",
        help="Area for which to fetch live music events (e.g., 'Pittsburgh, PA')",
    )

    parser.add_argument(
        "--generate_page_path",
        type=str,
        default=".asset/generated_page.html",
        help="Path to the generated HTML page",
    )

    return parser


def configure_logging(args) -> None:
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    log_file_mode = "w" if args.overwrite_log_file else "a"
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(args.log_file, mode=log_file_mode),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    initialize_environment()
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args)
    logging.info("Starting the application with the following configuration:")
    logging.info(f"args: {args}")
    run_job(args)


if __name__ == "__main__":
    main()
