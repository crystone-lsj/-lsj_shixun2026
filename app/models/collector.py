import httpx
import asyncio
from bs4 import BeautifulSoup
from app.models.lookout import LookoutSourceRepository, LookoutDataRepository


async def collect_from_source(source, params):
    url = source["url_template"]
    for key, value in params.items():
        url = url.replace("{" + key + "}", str(value))

    headers = source.get("headers", {})

    collected = []
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            html = resp.text

            soup = BeautifulSoup(html, "html.parser")

            title_sel = source.get("selector_title", "")
            items = soup.select(title_sel) if title_sel else []

            if not items:
                all_news = soup.select("div.result, div.news-item, div.news_box, div.c-container")
                if all_news:
                    items = all_news

            for item in items:
                title_tag = item.select_one("a") if isinstance(item, BeautifulSoup) else item
                if isinstance(item, BeautifulSoup):
                    a_tag = item.select_one("a")
                else:
                    a_tag = item.select_one("a")

                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                link = a_tag.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://www.baidu.com" + link

                summary = ""
                if source.get("selector_content"):
                    summary_el = item.select_one(source["selector_content"])
                    if summary_el:
                        summary = summary_el.get_text(strip=True)

                publish_time = ""
                if source.get("selector_time"):
                    time_el = item.select_one(source["selector_time"])
                    if time_el:
                        publish_time = time_el.get_text(strip=True)

                source_name = ""
                if source.get("selector_source"):
                    src_el = item.select_one(source["selector_source"])
                    if src_el:
                        source_name = src_el.get_text(strip=True)

                if title:
                    collected.append({
                        "source_id": source["id"],
                        "title": title,
                        "summary": summary,
                        "content": "",
                        "url": link,
                        "source_name": source_name,
                        "publish_time": publish_time
                    })
    except Exception:
        pass

    return collected


async def run_collection(source_ids, keywords, pages=1, count=10):
    all_results = []
    tasks = []

    sources = LookoutSourceRepository.get_all()
    source_map = {s["id"]: s for s in sources}

    for sid in source_ids:
        if sid not in source_map:
            continue
        source = source_map[sid]

        for keyword in keywords:
            for page in range(pages):
                params = {}
                for pf in source.get("param_fields", []):
                    field = pf["field"]
                    if field == "keyword":
                        params[field] = keyword
                    elif field == "pn":
                        params[field] = page * 10
                    else:
                        params[field] = pf.get("default", "")

                tasks.append(collect_from_source(source, params))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, list):
            all_results.extend(r)

    saved = LookoutDataRepository.batch_save(all_results)
    return {"total_collected": len(all_results), "saved": saved, "items": all_results}
