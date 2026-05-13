# Live Music Near Me

A small tool that turns Bandsintown event listings into a readable, filterable local music guide.

> **Note:** Parts of this project were vibe-coded. Please review the code carefully for security issues before using it with sensitive data, API keys, or untrusted HTML.

## What it does

Bandsintown lists a lot of live music events, but it can be hard to quickly understand what an unfamiliar artist or band sounds like. Looking up every artist manually takes time.

This application uses an LLM with web access to look up artist information, including genre, background, and general style. It then combines that information with Bandsintown event data and generates a readable, filterable HTML page.

> **Note:** Artist genres and descriptions are generated from online sources and may be inaccurate or incomplete. Please double-check important details before making plans.

## Installation

```bash
pip install ./
```

## Usage

1. Go to Bandsintown’s date and genre page￼<https://www.bandsintown.com/choose-dates/genre/all-genres>.
2. Choose the date you want to search.
3. Scroll down the page and click View All until all events are loaded.
4. Right-click the page, choose Inspect, and copy the full HTML.
5. Save the copied HTML here:

    ```plain text
    .asset/bandsintown.html
    ```

6. Create an OpenAI API key and add it to a `.env` file. See `.env.example` for the expected format.
    Running this tool may incur API costs. Keep your API key private and do not commit it to a public repository.
7. Run the tool:

    ```bash
    music-finder --area <your area, e.g. Austin, TX>
    ```

8. Open the generated result:

    ```plain text
    .asset/generated_page.html
    ```

## Command-line options

To see all available options, run:

```bash
music-finder -h
```

## Example

music-finder --area "Austin, TX"

This reads event data from `.asset/bandsintown.html` and generates a filterable HTML guide at `.asset/generated_page.html`.
