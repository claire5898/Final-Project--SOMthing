# SOMthing safety design

SOMthing lets members of a school community post listings that an AI assistant then reads. That creates three kinds of risk:

- **attacks**: prompt injection, jailbreaks, data probing and scams
- **agent malfunction**: invented listings, wrong prices, runaway loops
- **overspending**: bugs or abuse that burn through the course token budget

Defenses are layered, so if one misses, the next one catches it. Every layer below is built, tested offline (`tests/`), and exercised live (`evals/red_team.py`).

## Threat model

| # | Risk | What could happen | Defenses (layer) | Evidence |
|---|---|---|---|---|
| 1 | Direct prompt injection | A user tells SOMbot to ignore its rules or reveal its prompt | Regex screen on normalized text, before any tokens are spent (L1). LLM safety guard for suspicious phrasing (L2). Canary token and prompt-fragment check on the answer (L5). | `test_prompt_injection_message_blocked_before_any_ai_call`, `test_canary_leak_is_blocked`, red team #1–6 |
| 2 | Obfuscated injection | Leetspeak, spaced-out letters, zero-width characters or full-width Unicode slip past filters | NFKC normalization, zero-width stripping, leet/spacing variants scanned (L1) | `test_obfuscated_injections_are_caught`, red team #2–3 |
| 3 | Indirect injection | A seller hides instructions for the AI inside a listing | Listings scanned on post and held if flagged, so they're never sent to the AI (L3). Remaining listing text is wrapped in ⟦ ⟧ markers that authors can't forge and is labeled untrusted (L3). Only tool-returned IDs can be shown (L5). | `test_injected_listing_never_reaches_the_model`, `test_listing_text_is_wrapped_and_markers_cannot_be_forged`, red team #7 |
| 4 | Scams | Pay-first deposits, gift cards, wire transfers | Scam patterns hold listings (L3). The output filter replaces any answer that advises paying before meeting, while keeping answers that warn against it (L5). Safe-trade notice on every listing. | `test_scam_advice_in_answer_is_replaced`, `test_output_filters`, red team #9 |
| 5 | Privacy | Probing for someone's address or phone, or users oversharing their own PII | The LLM guard blocks privacy probes (L2). Emails, phones, SSNs and card numbers are redacted before the model or the logs see them (L1). No contact info allowed in listings (L7). SSN/card numbers rejected in messages. | `test_pii_never_reaches_the_model`, `test_inquiry_with_ssn_rejected`, red team #8, #13 |
| 6 | Prohibited items and honor code | Weapons, drugs, fake IDs, selling exam answers or doing graded work | Marketplace policy rejects these listings (L7). The LLM guard refuses these requests (L2). | `test_prohibited_items_and_honor_code`, red team #10–11 |
| 7 | Invented listings or prices (hallucination) | SOMbot recommends something that doesn't exist or misquotes a price | Cards are drawn only from IDs the tools returned. Every `$` amount is checked against real prices. Bundle totals are computed by code (L5). | `test_invented_listing_ids_are_removed`, `test_bundle_total_computed_by_app_not_model`, red team #14 |
| 8 | Runaway agent | The model loops on tool calls forever | Capped at 4 tool rounds and 8 tool calls, then a forced answer or a fallback to real search results (L6) | `test_runaway_loop_is_stopped` |
| 9 | Overspending | A bug or bad actor burns the token budget | 60k tokens per session and 1.5M per day; 8 AI requests per minute; 500-character messages; 900 output tokens per call; the guard runs only when needed (L6) | `test_token_budget_blocks_without_calling_model`, `test_rate_limit`, `test_overlong_message_rejected`, red team #15 |
| 10 | AI taking actions | The AI posts, buys or messages on someone's behalf | Least privilege: the AI's tools are read-only. Posting, saving and messaging need a human click. The Listing Helper only drafts, and its output is validated (L4). | `test_ai_tools_are_read_only`, `test_listing_helper_draft_is_validated` |
| 11 | "Too good to be true" listings | A real but suspicious bargain | Price-outlier warning on the listing page, and SOMbot is told to mention it (L7) | `test_too_good_to_be_true_price` |
| 12 | Web attacks | XSS through listing text, clickjacking, fake image uploads, password guessing | All text HTML-escaped. CSP, X-Frame-Options and nosniff headers. Uploads checked by magic bytes. 5 failed sign-ins per minute (L8). | `test_fake_image_upload_rejected`, `test_login_brute_force_limited_and_headers_set` |
| 13 | Secret leakage | The API key ends up in the browser, logs or git | Key read server-side from `.env` (repo folder, then parent). Never logged or returned. `.env` gitignored. (L8) | `test_health_never_exposes_key` |
| 14 | Provider outage | The AI call fails mid-request | Fails safely: browsing keeps working, and the guard fails closed | `test_provider_error_fails_safely`, `test_llm_guard_fails_closed` |

## The layers

1. **Input checks.** Length limits, Unicode/obfuscation normalization, prompt-injection patterns and PII redaction. These are deterministic and cost no tokens.
2. **LLM safety guard (tiered moderation).** A broad regex net decides when to ask a small, structured `gpt-6-luna` classifier. It labels the message `allow` or `block`, with a category: prompt injection, privacy, scam, academic dishonesty, illegal or harassment. Normal requests skip it, so they cost nothing extra. If the guard errors, the request is refused (fails closed).
3. **Untrusted data handling.** Flagged listings are held and never sent to the AI. All member-written text is wrapped in ⟦ ⟧ markers (the characters are stripped from the text first, so they can't be forged) and labeled as data.
4. **Least privilege and human in the loop.** The AI can only search and read. People post, save and send.
5. **Output checks.** Verified listing IDs, verified prices, code-computed bundle math, a canary token, a prompt-fragment check, a scam-advice filter, PII redaction and link stripping.
6. **Spend and abuse limits.** Token budgets, a rate limit, step limits and output caps.
7. **Marketplace policy.** Prohibited items, honor code, no contact info in listings, and price-outlier warnings.
8. **App security.** The key stays server-side, HTML escaping, security headers, upload checks, a sign-in limit and an audit log.

Every AI run and guardrail event is written to an audit log (`data/runtime/usage_log.jsonl`) with PII already redacted. It's visible on the in-app **AI & Safety dashboard**.

## Live red-team results

`python evals/red_team.py` sends 15 attacks through the real model. Results are in `evals/results/red_team_*.json`.

| Run | Result | What changed |
|---|---|---|
| First run | 11/15 handled safely | The output filter mistook a correct *warning* about deposits for scam advice. Some requests (translation trick, honor code, drugs) reached the main model without passing through the guard, although the model still declined them. |
| After hardening | **15/15 handled safely** | Scam advice is now judged per sentence, so warnings are kept. The guard's net now covers translation tricks, "take my midterm" and drug requests. |

Accuracy on the normal-shopping eval (`evals/run_eval.py`) stayed at **10/10** after hardening.

## Known limits

- Regex filters can be evaded by sufficiently creative phrasing. The LLM guard and output checks are the backstop, but none of these layers is perfect.
- The guard only runs on messages the regex net marks as suspicious, which trades a little coverage for cost.
- The sign-in screen is a mock. A real deployment would need Yale SSO, per-user accounts and server-side session storage.
- Messaging is simulated. A real version would need reporting/blocking tools and human moderators for held listings.
