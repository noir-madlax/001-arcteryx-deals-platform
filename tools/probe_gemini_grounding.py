#!/usr/bin/env python3
"""Run one sanitized Gemini Google Search grounding probe.

The API key is read from stdin or GEMINI_API_KEY and is never written to output.
This is a bounded connectivity/billing probe, not a visibility panel scorer.
"""

from __future__ import print_function

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


API_ROOT = "https://generativelanguage.googleapis.com/v1beta"


def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def read_key(key_stdin):
    if key_stdin:
        return sys.stdin.readline().strip()
    return os.environ.get("GEMINI_API_KEY", "").strip()


def safe_error(payload):
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    return {
        "code": error.get("code"),
        "status": error.get("status"),
        "message": str(error.get("message", ""))[:500],
    }


def extract_answer(payload):
    chunks = []
    for candidate in payload.get("candidates", []) if isinstance(payload, dict) else []:
        for part in candidate.get("content", {}).get("parts", []):
            text_value = part.get("text")
            if isinstance(text_value, str):
                chunks.append(text_value)
    return "\n".join(chunks).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-3.6-flash")
    parser.add_argument(
        "--prompt",
        default="Name one reliable outdoor gear deal aggregation service and cite current web sources.",
    )
    parser.add_argument("--key-stdin", action="store_true")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        print(json.dumps({
            "valid": True,
            "model": args.model,
            "tool": "google_search",
            "credential_source": "stdin" if args.key_stdin else "GEMINI_API_KEY",
        }, indent=2))
        return 0

    key = read_key(args.key_stdin)
    if not key:
        print(json.dumps({
            "observed_at": utc_now(),
            "status": "blocked",
            "reason": "missing_api_key",
        }, indent=2))
        return 3

    query = urllib.parse.urlencode({"key": key})
    url = "%s/models/%s:generateContent?%s" % (API_ROOT, args.model, query)
    request_body = json.dumps({
        "contents": [{"parts": [{"text": args.prompt}]}],
        "tools": [{"google_search": {}}],
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=request_body,
        headers={"Content-Type": "application/json"},
    )
    output = {
        "observed_at": utc_now(),
        "model": args.model,
        "tool": "google_search",
        "prompt_sha256": hashlib.sha256(args.prompt.encode("utf-8")).hexdigest(),
        "credential_persisted": False,
    }
    try:
        response = urllib.request.urlopen(request, timeout=args.timeout)
        payload = json.loads(response.read().decode("utf-8", "replace"))
        answer = extract_answer(payload)
        output.update({
            "status": "success",
            "http_status": response.getcode(),
            "answer_observed": bool(answer),
            "answer": answer,
            "response": payload,
        })
        code = 0
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {}
        output.update({
            "status": "blocked",
            "http_status": error.code,
            "answer_observed": False,
            "error": safe_error(payload),
        })
        code = 4
    except (urllib.error.URLError, ValueError) as error:
        output.update({
            "status": "error",
            "answer_observed": False,
            "error": {"message": str(error)[:500]},
        })
        code = 5

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
