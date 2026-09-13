# Live Music Near Me

A small tool that turns Bandsintown event listings into a readable, filterable local music guide.

## What it does

Bandsintown lists a lot of live music events, but it can be hard to quickly understand what an unfamiliar artist or band sounds like. Looking up every artist manually takes time.

This application uses an LLM with web access to look up artist information, including genre, background, and general style. It then combines that information with Bandsintown event data and generates a readable, filterable HTML page.

The generated page also lets visitors search events by keyword, save events in
their browser, filter to their shortlist, and export saved events as JSON.
Visitors can also choose an automatic layout or display one to four events per
row; that preference is saved in their browser.
Because the site is static,
saved events are specific to the current browser and GitHub Pages domain; they
do not automatically sync between devices.

> **Note:** Artist genres and descriptions are generated from online sources and may be inaccurate or incomplete. Please double-check important details before making plans.

## Installation

```bash
pip install -e ./
```

## Usage

1. Go to Bandsintown’s date and genre page￼<https://www.bandsintown.com/choose-dates/genre/all-genres>.
2. Choose the date you want to search.
3. Scroll down the page and click View All until all events are loaded.
4. Right-click the page, choose Inspect, and copy the full HTML.
5. Save the copied HTML to a file.
6. Create an OpenAI API key and add it to a `.env` file. See `.env.example` for the expected format.
    Running this tool may incur API costs. Keep your API key private and do not commit it to a public repository. To control your cost per run, use `--max-api-calls <number>`. You can review token usage report at `.asset/usage_report.json` after each run.
7. Run the tool:

    ```bash
    music-finder --path <path to your saved HTML> --area <your area, e.g. Pittsburgh, PA> --max-api-calls <number of max API call>
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

Use a different OpenAI model with:

```bash
music-finder --model <model name, such as gpt-5.6-luna>
```

Each run writes detailed token usage to `.asset/usage_report.json`, including
cached input, cache-write input, reasoning, visible output, totals, web-search
calls, and averages per enriched and parsed event. Use `--usage-report-path` to
choose another location.

## Example

```bash
music-finder --overwrite_log_file --path ".asset/bandsintown.html" --max-api-calls 1000
```

This reads event data from `.asset/bandsintown.html` and generates a filterable HTML guide at `.asset/generated_page.html`.
