import argparse
from .html_operation import read_and_parse_html, extract_live_music_data
from .event_operation import get_bands_details_async
from .generate_html import generate_html
from .models import event_db
import logging
import asyncio

logger = logging.getLogger(__name__)


def run_job(args: argparse.Namespace) -> None:
    event_db.load_from_file(args.even_db_path)
    event_db.clean_events()
    events = []
    for path in args.path:
        logger.info(f"Processing input file: {path}")
        soup = read_and_parse_html(path)
        logger.info("HTML file has been read and parsed successfully.")
        events.extend(extract_live_music_data(soup))
        logger.info("Live music data has been extracted successfully.")
    
    events = asyncio.run(
        get_bands_details_async(
            events, args.OPENAI_API_KEY, args.even_db_path, args.area
        )
    )
    logger.info(
        "Band details have been retrieved and event database has been updated successfully."
    )
    event_db.remove_prior_events()
    event_db.save_to_file(args.even_db_path)
    logger.info("Past events have been removed from the database.")
    generate_html(events, args.generate_page_path, args.area)
    logger.info("Generated HTML page has been saved successfully.")
