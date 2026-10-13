"""Build the PopQA question -> canonical Wikipedia page title map.

RQ4's obscurity arm needs the SUBJECT'S ARTICLE, not whatever Wikipedia search
returns for the question text. Measured 2026-07-28, gold answer present in the
retrieved context:

    full-question search    8%
    entity-name search     22%
    s_wiki_title (this)    -- direct page fetch, no search step at all

PopQA ships `s_wiki_title` and `datasets.py::_popqa` kept only s_pop/o_pop/prop,
so the field has to be re-fetched and joined on question text rather than
regenerating the frozen corpus.

Checkpointed and retried, because the naive version died at row 8,900 on an HF
429 and lost all 8,900 -- the same "one failure kills the whole pass" shape that
retry fixed everywhere else in this project.

    python scripts/fetch_popqa_titles.py
"""
from __future__ import annotations

import sys
import time

import pandas as pd
import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from faultlines.config import path  # noqa: E402

API = "https://datasets-server.huggingface.co/rows"
PAGE = 100          # HF caps `length` at 100
RETRIES = 5
BACKOFF = 3.0
PAUSE = 0.35        # between successful pages, to stay under the limit


def page(offset: int) -> list[dict]:
    for attempt in range(RETRIES):
        try:
            r = requests.get(API, params={
                "dataset": "akariasai/PopQA", "config": "default",
                "split": "test", "offset": offset, "length": PAGE}, timeout=60)
            r.raise_for_status()
            return [x["row"] for x in r.json()["rows"]]
        except Exception as exc:                                # noqa: BLE001
            if attempt == RETRIES - 1:
                print(f"  !! offset {offset} failed: {str(exc)[:70]}", flush=True)
                return []
            time.sleep(BACKOFF * (2 ** attempt))
    return []


PARQUET_API = "https://huggingface.co/api/datasets/akariasai/PopQA/parquet/default/test"


def whole_split() -> pd.DataFrame | None:
    """The entire split in ONE request, via HF's parquet export.

    Preferred over paging /rows. The paged version needed ~143 requests and was
    throttled to death twice (died at row 8,900, then 4,300), which is a lot of
    machinery and failure surface for a 14k-row table that HF will hand over as
    a single file. Reach for the bulk endpoint before building a pager.
    """
    for attempt in range(RETRIES):
        try:
            urls = requests.get(PARQUET_API, timeout=60).json()
            return pd.concat([pd.read_parquet(u) for u in urls], ignore_index=True)
        except Exception as exc:                                # noqa: BLE001
            if attempt == RETRIES - 1:
                print(f"  parquet export unavailable ({str(exc)[:60]}), paging instead")
                return None
            time.sleep(BACKOFF * (2 ** attempt))
    return None


def main() -> int:
    dest = path("interim", "popqa_wiki_titles.parquet")

    bulk = whole_split()
    if bulk is not None:
        df = bulk[["question", "s_wiki_title", "subj"]].drop_duplicates("question")
        print(f"fetched the whole split in one request: {len(df):,} rows")
    else:
        rows: list[dict] = []
        if dest.exists():                                       # resume
            rows = pd.read_parquet(dest).to_dict("records")
            print(f"resuming with {len(rows):,} rows already fetched")
        offset = len(rows)
        while True:
            got = page(offset)
            if not got:
                break
            rows += [{"question": g["question"], "s_wiki_title": g["s_wiki_title"],
                      "subj": g["subj"]} for g in got]
            offset += len(got)
            if offset % 2000 == 0:
                pd.DataFrame(rows).to_parquet(dest)             # checkpoint
                print(f"  {offset:,}", flush=True)
            if len(got) < PAGE:
                break
            time.sleep(PAUSE)
        df = pd.DataFrame(rows).drop_duplicates("question")

    df.to_parquet(dest)
    print(f"-> {dest.name}  {len(df):,} question -> wiki_title pairs")

    # Coverage against the frozen corpus is the only number that matters here.
    rec = pd.read_parquet(path("processed", "records.parquet"))
    pop = rec[rec["dataset"] == "popqa"]
    matched = pop["question"].isin(set(df["question"])).mean()
    print(f"   covers {matched:.1%} of the {len(pop):,} PopQA questions in the corpus")
    return 0 if matched > 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
