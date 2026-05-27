# Kafka Trade Processing POC — Agent Context

## System Overview
A microservices pipeline that ingests raw XML trades via REST, enriches them with account data, and publishes enriched JSON to a Kafka audit topic.

## Services

| Service | Port | Role |
|---|---|---|
| `account-service` | `8085` | Manages account master data (PostgreSQL) |
| `trade-service` | `8086` | Ingests, enriches, and audits trades via Kafka |

## End-to-End Flow

1. Client POSTs raw XML to `POST /trade/publish`
2. Trade Service publishes raw XML to `trade-topic`
3. `TradeConsumer` picks it up via `@KafkaListener`
4. XML is parsed into a `Trade` object
5. `AccountClient` calls Account Service (REST) to fetch `partyAccount1` and `partyAccount2` details
6. `TradeService` builds an `EnrichedTrade` combining trade + account info
7. `LoggingClient` publishes the `EnrichedTrade` as JSON to `trade-log-topic`

## Data Models

### Trade — Raw Input (XML)
```xml
<trade>
    <tradeId>TRD-XXXX</tradeId>
    <time>2026-05-05TXX:XX:XXZ</time>
    <amount>XXXX</amount>
    <partyAccount1>ACC-XXX</partyAccount1>  <!-- buyer account -->
    <partyAccount2>ACC-XXX</partyAccount2>  <!-- seller account -->
</trade>
```

### AccountDTO — from Account Service
```json
{
  "accountNumber": "ACC-XXX",
  "holderName": "...",
  "currency": "USD",
  "branch": "..."
}
```

### EnrichedTrade — Final Kafka Output (JSON to `trade-log-topic`)
```json
{
  "tradeId": "TRD-XXXX",
  "time": "...",
  "amount": 15000.00,
  "partyAccount1": "ACC-XXX",
  "partyAccount2": "ACC-XXX",
  "partyAccount1Details": { "accountNumber": "...", "holderName": "...", "currency": "...", "branch": "..." },
  "partyAccount2Details": { "accountNumber": "...", "holderName": "...", "currency": "...", "branch": "..." }
}
```

## Kafka Topics

| Topic | Format | Purpose |
|---|---|---|
| `trade-topic` | Raw XML string | Input queue for trade processing |
| `trade-log-topic` | JSON `EnrichedTrade` | Audit trail of all successfully processed trades |
| `trade-dlt` | Raw XML string | Dead letter — trades that exhausted all retries |

## Exception Handling & Retry Behavior

| Exception | Retryable | Outcome |
|---|---|---|
| `InvalidXmlException` | No | Message silently skipped |
| `HttpClientErrorException` (4xx) | No | Account not found — trade skipped |
| `RecoverableException` | Yes | Retried 4x with exponential backoff (5s→10s→20s), then → `trade-dlt` |
| `ResourceAccessException` | Yes | Network issue → wrapped as `RecoverableException` → retry |
| `HttpServerErrorException` (5xx) | Yes | Server issue → wrapped as `RecoverableException` → retry |

## Account Service API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/accounts/{accNo}` | Fetch account by number |
| `POST` | `/accounts` | Create account |

## Field Semantics
- `partyAccount1` = **buyer** account
- `partyAccount2` = **seller** account
- `partyAccount1Details` / `partyAccount2Details` = enriched account info embedded in Kafka output
- For **rejected/failed** trades, enriched detail fields are typically empty
- For **valid/enriched** trades, all detail fields are populated from Account Service
