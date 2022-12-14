import argparse
import pathlib

from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, DoubleType, StringType, LongType
from pyspark.sql.functions import col, dayofyear, year, mean, count


def load_dataset(session: SparkSession, dataset_path: str) -> DataFrame:
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("subreddit", StringType(), True),
        StructField("created_utc", LongType(), True),
        StructField("polarity", DoubleType(), True),
        StructField("subjectivity", DoubleType(), True)
    ])

    df = session.read.option("delimiter", "\t").csv(dataset_path, schema=schema)
    return df.withColumn("created_utc", col("created_utc").cast("Timestamp"))


def main():
    parser = argparse.ArgumentParser(description='Process datasets.')
    parser.add_argument('dataset_path', nargs='?', default=pathlib.Path.cwd() / "dataset", type=pathlib.Path)
    parser.add_argument('result_path', nargs='?', default=pathlib.Path.cwd() / "dataset" / "result", type=pathlib.Path)
    args = parser.parse_args()
    spark = SparkSession.builder.getOrCreate()

    timed_df = load_dataset(spark, str(args.dataset_path))
    result_df = timed_df.groupby(
        year("created_utc").alias("year"),
        dayofyear("created_utc").alias("day"),
        "subreddit"
    ).agg(
        mean("polarity").alias("avg_polarity"),
        mean("subjectivity").alias("avg_subjectivity"),
        count("*").alias("count")
    ).orderBy(
        "year",
        "day"
    )

    result_df\
        .coalesce(1)\
        .write \
        .option("header", True) \
        .csv(str(args.result_path))


if __name__ == "__main__":
    main()
