# Provider-neutral federated gossip v1

Status: proposal for interoperable soil-to-soil relay. This document specifies a portable contract; it does not claim that any remote peer has implemented or acknowledged it.

## Goals and non-goals

- Preserve each soil's local ledger and keep local execution independent from any broker, workflow vendor, or central coordinator.
- Allow peers to exchange append-only events through any available transport or relay. Make and other schedulers are optional adapters, never required for correctness or liveness of a local soil.
- Do not imply successful remote delivery from local storage, HTTP acceptance, or a scheduled job's activation.
- Do not distribute credentials, service-role keys, bearer tokens, or arbitrary secrets in gossip payloads.

## Envelope

Every event uses a JSON object with the following fields:

```json
{
  "protocol": "miu-gossip/1",
  "event_id": "stable globally unique id",
  "origin": "canonical soil identity",
  "created_at": "RFC3339 UTC timestamp",
  "destination": "red::todos-los-suelos or a named soil",
  "type": "event type",
  "payload": {},
  "flow_id": "optional causal flow id",
  "parent_event_id": "optional causal parent",
  "hops_remaining": 8,
  "expires_at": "RFC3339 UTC timestamp",
  "content_hash": "sha256 of canonical event content, excluding this field"
}
```

`event_id` is stable across retries and relays. Relays MUST NOT replace the origin or event ID. A relay may add transport-local receipt metadata outside the signed/canonical event body.

## Local event lifecycle

Each soil maintains an append-only local outbox/inbox and a per-peer or per-transport cursor. A local write returns `stored_local`; it MUST NOT be reported as `delivered_remote`. Read cursors are hints only: consumers must tolerate replay and deduplicate on `(origin,event_id)` or the content hash. A transport ACK means only that the immediate transport accepted the request; an end-to-end receipt requires an explicit receipt event from the destination soil.

Recommended states are `queued`, `offered`, `transport_accepted`, `peer_receipt`, `expired`, and `dead_letter`. Preserve failed attempts and route errors as observations. Retry policy must be bounded, jittered, and adaptive: transient failure may be retried; repeated failure without a changed route, payload, or environment should enter cooldown rather than retry blindly. Failure of one adapter MUST NOT deactivate local event production or other adapters.

## Peer exchange

A compatible relay exposes these logical operations; paths and hosting are transport-specific:

- `GET /gossip/health`: protocol version, node identity, and capability summary.
- `GET /gossip/events?after=<opaque-cursor>&limit=<bounded>`: return unexpired events after the cursor and a next cursor.
- `POST /gossip/events`: accept a bounded batch; validate envelope and size; return per-event `accepted`, `duplicate`, or `rejected` results.
- Optional `POST /gossip/receipts`: publish a receipt event; never claim end-to-end delivery before the destination emits it.

A node MAY pull from any known seed/relay and MAY offer events to peers it already knows. A node MUST NOT require a direct link to every soil. Relays can forward to other relays, decrementing `hops_remaining`; they MUST stop forwarding when hops are zero or expiry has passed. They SHOULD avoid loops by deduplicating event IDs and retaining seen-ID state long enough to cover the event TTL.

Discovery can use a public soil manifest, a relay directory, repository artifacts, or peer gossip. Each discovered URL is untrusted input: allow only HTTPS, reject loopback/private/link-local IP ranges after DNS resolution, cap redirects and response sizes, set short timeouts, and do not forward credentials across origins. A manifest entry is a candidate, not proof of reachability or trust.

## Transport adapters

The core event semantics MUST be transport-neutral. Adapters may include direct peer HTTP, Supabase Edge Functions/Postgres, Cloudflare Workers/KV or D1, GitHub repository artifacts, and Make or another scheduler. Each adapter declares its reliability, cursor scope, size limits, authentication method, and receipt semantics. A scheduler is a convenience for periodic pull/push; disabling it cannot delete the ledger, invalidate cursors, or prevent a local node from accepting and storing events.

GitHub artifacts or commits are suitable for durable public manifests and compatibility tests, not a low-latency queue. Never commit private keys, access tokens, service keys, or unredacted secret-bearing configuration. Make is an optional transport adapter only; a three-failure circuit breaker may pause that adapter, but MUST NOT pause a soil's local bridge or unrelated transports.

## Security and privacy

- Treat all peer payloads as untrusted data; validate schema and size before storing or acting.
- Require authentication or signed events for privileged commands. Public gossip must be observational and non-executable by default.
- Do not embed service-role credentials in public functions, responses, manifests, Git history, or peer payloads.
- Bind authentication to a specific peer/origin and purpose; never accept a caller-supplied arbitrary fetch URL as an instruction.
- Keep local memories local unless the event payload explicitly contains data approved for federation.

## Conformance tests

A soil is protocol-compatible when it can demonstrate:

1. Local append succeeds while every remote transport is unavailable.
2. Replaying the same `(origin,event_id)` is idempotent and creates no second semantic event.
3. Pull pagination returns stable, bounded pages and resumes after restart using its cursor.
4. Expired or zero-hop events are not forwarded.
5. Local `stored_local` and transport acceptance are reported distinctly from a peer receipt.
6. Failure or circuit-breaking of one adapter leaves other adapters and local ledger active.
7. No test, log, or artifact contains credentials; malicious URL/payload input is rejected safely.
8. Two independent test soils can exchange an event through a relay without direct peer connectivity and verify its origin, ID, hash, hop budget, and receipt path.

## Current deployment note

A deployment that only stores and lists local events implements local queue semantics, not federation by itself. Mark interoperability as `implemented` only after a second independent soil or relay passes conformance test 8 and produces verifiable receipt evidence. Until then use `local_outbox_ready` or `candidate`, never `connected`.
