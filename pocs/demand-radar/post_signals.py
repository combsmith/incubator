#!/usr/bin/env python3
"""
DemandRadar — post the Analyst's weekly signals comment to the incubator Discussion
thread THREAD_TITLE (created in CATEGORY on first use).

Runs in the workflow's isolated `post-signals` job, after analyst_check.py passed on a
clean checkout. It only ever adds ONE comment per ISO week to that one thread (a hidden
week marker makes a re-run a no-op), and it refuses the Ideas category outright: it never
opens, comments on, or labels an Ideas Discussion — promoting an idea stays a human call.

  GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo python post_signals.py
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
COMMENT_PATH = os.path.join(HERE, "output", "signals-comment.md")  # fixed; never argv
API = "https://api.github.com/graphql"
THREAD_TITLE = "DemandRadar — weekly signals"
CATEGORY = "General"
FORBIDDEN_CATEGORY = "ideas"
MARKER = "<!-- demand-radar-weekly-signals:{week} -->"
THREAD_BODY = (
    "One comment a week from the DemandRadar weekly run: the Analyst's read of the weekly digest "
    "and the new deep-dive briefs, naming up to three ideas that may be worth an Ideas Discussion. "
    "Every claim cites a board record or a deep-dive. Nothing here is promoted automatically."
)
FOOTER = (
    "\n\n---\n_Posted by the DemandRadar weekly run. This comment promotes nothing: opening an Ideas "
    "Discussion for any of these is a human call._"
)


class PostError(Exception):
    """The comment could not (or must not) be posted."""


def _today():
    return datetime.now(timezone.utc).date()


def _gql(token, query, variables):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "DemandRadar-weekly-signals",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    if out.get("errors"):
        raise PostError("GraphQL: " + "; ".join((e or {}).get("message", "?") if isinstance(e, dict) else "?" for e in out["errors"]))
    return out.get("data", {})


def find_thread(token, repo):
    q = """query($q: String!) { search(query: $q, type: DISCUSSION, first: 10) {
      nodes { ... on Discussion { id title url category { name } } } } }"""
    data = _gql(token, q, {"q": f'repo:{repo} in:title "{THREAD_TITLE}"'})
    for d in data.get("search", {}).get("nodes", []):
        cat = ((d or {}).get("category") or {}).get("name", "")
        if d and d.get("title") == THREAD_TITLE and cat.lower() != FORBIDDEN_CATEGORY:
            return d
    return None


def create_thread(token, repo):
    owner, name = repo.split("/", 1)
    q = """query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) {
      id discussionCategories(first: 50) { nodes { id name } } } }"""
    data = _gql(token, q, {"owner": owner, "name": name})
    r = data.get("repository") or {}
    cat = next((c for c in r.get("discussionCategories", {}).get("nodes", []) if c.get("name") == CATEGORY), None)
    if cat is None:
        raise PostError(f"no {CATEGORY!r} discussion category in {repo}")
    m = """mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
        discussion { id url } } }"""
    d = _gql(
        token, m, {"repositoryId": r.get("id"), "categoryId": cat.get("id"), "title": THREAD_TITLE, "body": THREAD_BODY}
    )
    discussion = d.get("createDiscussion", {}).get("discussion") or {}
    url = discussion.get("url")
    if not url:
        raise PostError("failed to create the discussion thread")
    print(f"created the {THREAD_TITLE!r} thread: {url}")
    return discussion


def already_posted(token, discussion_id, marker):
    q = """query($id: ID!) { node(id: $id) { ... on Discussion { comments(last: 30) { nodes { body } } } } }"""
    data = _gql(token, q, {"id": discussion_id})
    nodes = data.get("node", {}).get("comments", {}).get("nodes") or []
    return any(marker in (c.get("body") or "") for c in nodes)


def post(body, today, repo, token):
    """Add this week's comment; return its URL, or None when this week was already posted."""
    if CATEGORY.lower() == FORBIDDEN_CATEGORY:
        raise PostError("refusing to post into the Ideas category — promotion is a human call")
    y, w, _ = today.isocalendar()
    marker = MARKER.format(week=f"{y}-W{w:02d}")
    thread = find_thread(token, repo)
    if thread is None:
        thread = create_thread(token, repo)
    else:
        thread_id = thread.get("id")
        if thread_id and already_posted(token, thread_id, marker):
            print(f"this week's signals are already posted ({marker}); nothing to do")
            return None
    m = """mutation($id: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $id, body: $body}) { comment { url } } }"""
    text = f"{marker}\n{body.strip()}{FOOTER}"
    thread_id = thread.get("id")
    if not thread_id:
        raise PostError("no discussion id in thread")
    data = _gql(token, m, {"id": thread_id, "body": text})
    url = data.get("addDiscussionComment", {}).get("comment", {}).get("url")
    if not url:
        raise PostError("failed to add the signals comment")
    return url


def main():
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GITHUB_TOKEN and GITHUB_REPOSITORY are required", file=sys.stderr)
        return 1
    try:
        with open(COMMENT_PATH, encoding="utf-8") as f:
            body = f.read()
    except (OSError, UnicodeError) as e:  # file-access / encoding — report, don't traceback
        print(f"could not read the signals comment: {e}", file=sys.stderr)
        return 1
    try:
        url = post(body, _today(), repo=repo, token=token)
    except (PostError, OSError) as e:  # OSError: HTTP/network failure talking to the API
        print(f"could not post the weekly signals: {e}", file=sys.stderr)
        return 1
    if url:
        print(f"posted: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
