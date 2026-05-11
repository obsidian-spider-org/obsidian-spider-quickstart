**Show HN: A markdown prompt that fans out free Copilot subagents from one parent call**

I built a markdown prompt that turns one GitHub Copilot premium request into a small fan-out of subagent reviewers — and writes a cryptographically signed log of what they each said.

You paste the prompt into Copilot's coding-agent surface. The parent call delegates to N subagents (I run 4-8) who each critique the PR independently. Their outputs land in a JSONL file with an HMAC chain, so you can audit who said what later.

What it does:

- One premium request → multiple reviewers inside the parent message
- Each reviewer logs a signed line; the chain is tamper-evident
- Works today on Copilot Pro+ ($39/mo, 1500 premium requests)

What it doesn't do:

- It is not magic. Free fanout is a current Copilot policy, not a guarantee.
- It catches obvious quorum-style misses; it will not save a broken pipeline.
- I have more infrastructure around this. The markdown alone is the gift.

Repo + prompt: https://github.com/obsidian-spider-org/obsidian-spider-quickstart
License: MIT.

Try it on a real PR. Measure your own ratio. Decide.
