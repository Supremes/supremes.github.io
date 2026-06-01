#!/usr/bin/env python3
"""xueqiu article analyzer - LLM summary for liuyijuushi"""
import os, re, sys, json, glob, time, subprocess
from datetime import datetime
from openai import OpenAI

XUEQIU_USER_ID = "9391624441"
XUEQIU_USER_NAME = "liuyijuushi"
KB_CONTENT_DIR = os.path.expanduser("~/knowledge-base/content/invest/liuyijuushi")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://token-plan-sgp.xiaomimimo.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "mimo-v2.5-pro")

def get_llm_client():
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE)

def fetch_article_content(article_id):
    try:
        url = f"https://xueqiu.com/{XUEQIU_USER_ID}/{article_id}"
        subprocess.run(["bb-browser", "goto", url, "--tab", "e022"], capture_output=True, timeout=15)
        time.sleep(2)
        result = subprocess.run(["bb-browser", "eval", """
            const t=document.querySelector("h1")?.textContent?.trim()||document.title;
            const e=document.querySelector(".article__bd__detail")||document.querySelector(".status-content");
            const c=e?.innerText?.trim()?.substring(0,6000)||"";
            const d=document.querySelector(".article__bd__from,[class*=time]")?.textContent?.trim()||"";
            JSON.stringify({title:t,date:d,content:c});
        """, "--tab", "e022"], capture_output=True, text=True, timeout=15)
        return json.loads(result.stdout.strip())
    except Exception as e:
        print(f"fetch failed {article_id}: {e}")
        return None

PROMPT = """Analyze this Xueqiu article and extract core arguments.

Title: {title}
Date: {date}
Content:
{content}

Output JSON:
{{"core_arguments":["arg1: ...","arg2: ...","arg3: ..."],"key_insights":"key investment insight","investment_principle":"principle","market_view":"market view","tags":["tag1","tag2"]}}"""

def analyze(title, date, content):
    client = get_llm_client()
    try:
        resp = client.chat.completions.create(model=LLM_MODEL, messages=[
            {"role":"system","content":"You are a professional investment analyst."},
            {"role":"user","content":PROMPT.format(title=title,date=date,content=content[:4000])}
        ], temperature=0.3, max_tokens=1500)
        txt = resp.choices[0].message.content
        m = re.search(r"\{[\s\S]*\}", txt)
        return json.loads(m.group()) if m else {"core_arguments":[txt],"key_insights":txt}
    except Exception as e:
        print(f"LLM failed: {e}")
        return None

def update_kb(art, ana):
    safe = re.sub(r"[^\w]","-",art["title"])[:40].strip("-")
    fn = f"{art['date']}-{safe}"
    fp = os.path.join(KB_CONTENT_DIR, f"{fn}.md")
    args = "\n".join([f"- {a}" for a in ana.get("core_arguments",[])])
    tags = ", ".join(ana.get("tags",["invest","index-fund"]))
    md = f"""---
title: "{art['title']}"
date: "{art['date']}"
tags: "{tags}"
summary: "{ana.get('key_insights','')[:100]}"
source: "https://xueqiu.com/{XUEQIU_USER_ID}/{art['id']}"
author: "liuyijuushi"
---

## Core Arguments

{args}

## Key Insights

{ana.get("key_insights","")}

## Investment Principle

{ana.get("investment_principle","")}

## Market View

{ana.get("market_view","")}

## Original Summary

{art.get("content","")[:2000]}

---

*Source: [Xueqiu](https://xueqiu.com/{XUEQIU_USER_ID}/{art['id']})*
*Analyzed: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
    os.makedirs(KB_CONTENT_DIR, exist_ok=True)
    with open(fp,"w",encoding="utf-8") as f: f.write(md)
    print(f"Updated: {fn}")

def get_existing():
    ex = {}
    for fp in glob.glob(os.path.join(KB_CONTENT_DIR,"*.md")):
        with open(fp,"r",encoding="utf-8") as f:
            m = re.search(r"source:.*/(\d+)", f.read())
            if m: ex[m.group(1)] = fp
    return ex

def fetch_list():
    try:
        subprocess.run(["bb-browser","goto",f"https://xueqiu.com/{XUEQIU_USER_ID}","--tab","e022"],capture_output=True,timeout=15)
        time.sleep(2)
        r = subprocess.run(["bb-browser","eval","""
            Array.from(document.querySelectorAll("a")).map(a=>({h:a.href,t:a.textContent.trim().substring(0,120)}))
            .filter(a=>a.h.match(/\\/9391624441\\/\\d+/)&&!a.h.includes("#"))
            .reduce((x,a)=>{if(!x.find(y=>y.h===a.h))x.push(a);return x},[])
            .map(a=>a.h+"|"+a.t).join("\\n")
        ""","--tab","e022"],capture_output=True,text=True,timeout=15)
        arts = []
        for line in r.stdout.strip().split("\n"):
            if "|" in line:
                url,txt = line.split("|",1)
                arts.append({"id":url.split("/")[-1],"url":url,"title_hint":txt})
        return arts
    except Exception as e:
        print(f"fetch list failed: {e}")
        return []

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--update-all",action="store_true")
    p.add_argument("--article-id")
    p.add_argument("--list-only",action="store_true")
    args = p.parse_args()
    if not LLM_API_KEY:
        print("Set LLM_API_KEY");sys.exit(1)
    print(f"Analyzing {XUEQIU_USER_NAME}...")
    arts = fetch_list()
    if not arts: print("No articles");sys.exit(1)
    print(f"Found {len(arts)} articles")
    if args.list_only:
        for a in arts: print(f"  {a['id']} | {a['title_hint'][:60]}")
        return
    existing = get_existing()
    if args.article_id: todo = [a for a in arts if a["id"]==args.article_id]
    elif args.update_all: todo = arts
    else: todo = [a for a in arts if a["id"] not in existing]
    if not todo: print("No new articles");return
    print(f"Processing {len(todo)} articles")
    for i,a in enumerate(todo):
        print(f"\n[{i+1}/{len(todo)}] {a['title_hint'][:50]}...")
        cd = fetch_article_content(a["id"])
        if not cd or not cd.get("content"): print("Skip");continue
        ana = analyze(cd["title"],cd["date"],cd["content"])
        if not ana: print("Skip");continue
        update_kb({"id":a["id"],"title":cd["title"],"date":cd["date"],"content":cd["content"]},ana)
        time.sleep(2)
    print("\nDone!")
    subprocess.run(["systemctl","restart","knowledge-base"],capture_output=True)
    print("KB restarted")

if __name__=="__main__": main()
