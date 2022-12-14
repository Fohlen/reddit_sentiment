import argparse
from itertools import product

from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

from reddit_sentiment.annotate import process_archive
from reddit_sentiment.preprocess import BASE_DIR, ARCHIVE_REGEX


def glob_archive_year_month(pattern: str) -> set[tuple[int, int]]:
    groups = [ARCHIVE_REGEX.search(file.name).groups() for file in BASE_DIR.glob(pattern)]
    return set([(int(year), int(month)) for year, month in groups])


def main():
    parser = argparse.ArgumentParser(description='Run sentiment analysis on reddit comments corpus.')
    parser.add_argument('start_year', nargs='?', default=2005, type=int)
    parser.add_argument('end_year', nargs='?', default=2006, type=int)
    parser.add_argument('--multithreading', default=False, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    years = list(range(args.start_year, args.end_year + 1))
    months = list(range(1, 13))

    processing_archives = glob_archive_year_month("**/RC*.zst")
    processed_archives = glob_archive_year_month("**/RC*.tsv")

    print(f"Omitting {len(processed_archives)} archives")
    product_of_years_months = set(product(years, months))
    year_months_to_process = processing_archives.union(product_of_years_months.difference(processed_archives))

    if args.multithreading:
        process_map(process_archive, sorted(year_months_to_process))
    else:
        for ip in tqdm(sorted(year_months_to_process)):
            process_archive(ip)


if __name__ == '__main__':
    main()
