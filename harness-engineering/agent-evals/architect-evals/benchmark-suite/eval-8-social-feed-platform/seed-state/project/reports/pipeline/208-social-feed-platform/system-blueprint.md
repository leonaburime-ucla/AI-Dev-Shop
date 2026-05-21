# System Blueprint: Social Feed Platform

## Domain Decomposition

- **Feed Service**: generates and delivers personalized feeds
- **Post Service**: handles content creation, storage, and retrieval
- **User Service**: manages profiles, follows, and relationships
- **Notification Service**: delivers real-time notifications via WebSocket and push
- **Moderation Service**: automated content scanning + human review queue
- **API Gateway**: rate limiting, authentication, request routing

## High-Level Topology

```
[Clients] → [API Gateway] → [Feed Service] → [Post Store]
                           → [Post Service] → [Post Store]
                           → [User Service] → [User DB]
                           → [Notification Service] → [WebSocket / Push]
                           → [Moderation Service] → [Review Queue]
```

## Storage Decisions

- **Post Store**: PostgreSQL with hash-partitioned tables by post_id
- **User DB**: PostgreSQL for profiles and follow relationships
- **Feed Cache**: Redis for pre-computed feed timelines (top 200 posts per user)
- **Notification Queue**: RabbitMQ for async notification delivery

## Capacity Estimates

- Registered users: 10M
- Daily active: 2M
- Posts per day: 4M (2 per active user)
- Feed reads per day: 100M (50 per active user)
- Average followers per user: 150
- Storage growth: ~2TB/year for posts + metadata

## Feed Strategy

Fan-out-on-write: when a user posts, push the post_id to every follower's feed cache.
This gives instant feed reads (just read from cache) at the cost of write amplification.

## Rate Limiting

Global rate limiter at the API gateway using a fixed-window counter.
Limits: free=100/min, standard=1000/min, enterprise=10000/min.

## Notification Delivery

When a post receives a like/mention, enqueue a notification job.
The notification worker processes jobs and delivers via WebSocket.
Retry on failure with 1-second fixed interval.

## Moderation

Content scanned on upload by automated classifier.
Spam reports go to human review queue.
No automated enforcement — all moderation actions require human approval.

## Observability

- Application metrics via Prometheus
- Distributed tracing via OpenTelemetry
- Centralized logging via ELK

## Security

- OAuth 2.0 for API authentication
- HTTPS everywhere
- Input sanitization on all user content

## Webhook Integration

Third-party clients register webhook URLs for mention/reply events.
When triggered, POST the event payload to the registered URL.
On timeout, retry delivery 3 times.
