import io
import json
import pathlib
from itertools import product
from multiprocessing import Pool
from typing import Callable

from tenacity import retry
import requests
import zstandard
from textblob import TextBlob
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

COMMENTS_URL = "https://files.pushshift.io/reddit/comments"
ARCHIVE_TEMPLATE = "RC_{year}-{month:02d}.zst"


@retry
def download_file(url: str, file_path: pathlib.Path):
    with requests.get(url, stream=True) as response, file_path.open("wb") as fp:
        response.raise_for_status()
        for chunk in response.iter_content():
            if chunk:
                fp.write(chunk)


def decompress_archive(
        archive_path: pathlib.Path,
        output_path: pathlib.Path,
        callback: Callable[[str, io.TextIOWrapper], None]
):
    with archive_path.open("rb") as fp, output_path.open("wt") as tp:
        dctx = zstandard.ZstdDecompressor(max_window_size=2147483648)
        with dctx.stream_reader(fp) as stream_reader:
            text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')
            for line in text_stream.readlines():
                callback(line, tp)


def process_line(line: str, output: io.TextIOWrapper):
    document = json.loads(line)
    blob = TextBlob(document["body"])
    print(
        document["id"],
        document["subreddit"],
        document["created_utc"],
        *blob.sentiment,
        sep="\t",
        file=output
    )


def process_archive(yearmonth: tuple[int, int]):
    year, month = yearmonth
    archive = ARCHIVE_TEMPLATE.format(year=year, month=month)
    version_path = pathlib.Path.cwd() / archive
    output_path = pathlib.Path.cwd() / f"{archive}.tsv"
    version_url = f"{COMMENTS_URL}/{archive}"

    if not version_path.exists():
        download_file(version_url, version_path)

    decompress_archive(version_path, output_path, process_line)


if __name__ == '__main__':
    years = [2006, 2007, 2008, 2009, 2010]
    months = list(range(1, 13))

    with Pool(processes=4) as pool:
        for year in tqdm(years):
            process_map(process_archive, product([year], months), total=12)
