# Change: agent-answer-presentation-hardening

## Why

AskPage assistant answers can look noisy when models emit Markdown heading markers such as `#`, and large heading/body size differences make long answers feel fragmented. Complex questions also need stronger response-structure guidance so the model separates conclusions, evidence, steps, and risks.

## What Changes

- Normalize assistant Markdown headings into compact emphasized section labels instead of visible or oversized `#` headings.
- Reduce assistant message heading visual hierarchy so headings and body text feel like one coherent answer.
- Add AI Runtime answer style guidance for complex questions: conclusion first, layered reasoning, clear priorities, and no Markdown `#` headings.

## Out Of Scope

- No provider changes.
- No retrieval algorithm changes.
- No report rendering changes outside AskPage assistant messages.
