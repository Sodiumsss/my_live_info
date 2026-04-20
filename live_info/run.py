from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from live_info.config import Config
from live_info.crawlers.maoyan import MaoyanCrawler
from live_info.db.client import make_client
from live_info.db.repositories import Repository
from live_info.diff import diff_events, merge_raw_shows
from live_info.llm.alias_resolver import AliasResolver
from live_info.llm.client import LLMClient
from live_info.llm.verifier import LLMVerifier
from live_info.models import Event
from live_info.notifiers.dispatcher import dispatch
from live_info.notifiers.email import EmailNotifier, SMTPConfig
from live_info.notifiers.feishu import FeishuNotifier


log = logging.getLogger("live_info")


async def run(dry_run: bool = False) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    cfg = Config.from_env()
    if dry_run:
        log.info("DRY RUN: no DB writes, no notifications.")

    sb = make_client(cfg.supabase_url, cfg.supabase_service_key)
    repo = Repository(sb)

    artists = await repo.get_subscribed_artists()
    log.info("subscribed artists: %d", len(artists))
    if not artists:
        _write_summary("no subscribed artists. noop.")
        return 0

    total_events: list[Event] = []
    failures: list[str] = []

    async with (
        LLMClient(cfg.llm_base_url, cfg.llm_api_key, cfg.llm_model) as llm,
        MaoyanCrawler() as crawler,
        FeishuNotifier() as feishu,
    ):
        alias = AliasResolver(repo=repo, llm=llm)
        verifier = LLMVerifier(llm=llm)

        for artist in artists:
            try:
                my_shows = await crawler.search(artist.canonical_name)
                llm_shows = await verifier.verify(artist.canonical_name)

                # alias normalization for any raw_artist_name that differs
                # (cheap: skip — crawler & verifier already queried by canonical)

                new_concerts = merge_raw_shows(artist.id, my_shows, llm_shows)
                old_concerts = await repo.get_concerts_for_artist(artist.id)

                # upsert new ones (DB assigns id) — need ids to diff reliably
                if not dry_run:
                    enriched = []
                    for c in new_concerts:
                        saved = await repo.upsert_concert(c)
                        enriched.append(saved)
                    new_concerts = enriched

                events = diff_events(old=old_concerts, new=new_concerts)
                for e in events:
                    e.artist_name = artist.canonical_name
                total_events.extend(events)

                if not dry_run:
                    for e in events:
                        await repo.insert_snapshot(e.concert)

                log.info("%s: maoyan=%d llm=%d events=%d",
                         artist.canonical_name, len(my_shows), len(llm_shows), len(events))
            except Exception as e:
                log.exception("artist failed: %s", artist.canonical_name)
                failures.append(artist.canonical_name)

        if total_events and not dry_run:
            users = {u.id: u for u in await repo.get_users()}
            subscribers: dict[str, list[str]] = {}
            for artist in artists:
                subscribers[artist.id] = await repo.get_subscriber_user_ids(artist.id)

            email = None
            if cfg.smtp_host:
                email = EmailNotifier(SMTPConfig(
                    host=cfg.smtp_host, port=cfg.smtp_port,
                    user=cfg.smtp_user, password=cfg.smtp_pass,
                    sender=cfg.smtp_from or "",
                ))

            delivery = await dispatch(total_events, users, subscribers, feishu=feishu, email=email)
            log.info("delivery: %s", delivery)

    _write_summary(
        f"artists={len(artists)} events={len(total_events)} failures={len(failures)} "
        f"failed_artists={failures}"
    )
    # 失败率 > 30% 视为整体失败
    if artists and len(failures) / len(artists) > 0.3:
        return 1
    return 0


def _write_summary(text: str) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        print("[SUMMARY]", text)
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"### live_info run\n\n```\n{text}\n```\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    return asyncio.run(run(dry_run=args.dry_run or os.getenv("DRY_RUN", "").lower() in ("1", "true")))


if __name__ == "__main__":
    sys.exit(main())
