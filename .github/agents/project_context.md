# Project Context: Kafka Trade Enrichment POC

## Architecture
- **2 microservices** communicating via Kafka (async) and REST (sync)

| Service | Port | Role |
|---|---|---|
| `account-service` | 8085 | CRUD for account master data in PostgreSQL |
| `trade-service` | 8086 | Ingests XML trades, enriches with account data, publishes to audit topic |

## Data Flow
1. Client POSTs raw XML → `trade-service`
2. `trade-topic` receives raw XML string
3. `TradeConsumer` (`@KafkaListener`) parses XML via `XmlMapper`
4. `AccountClient` (`RestTemplate`) fetches account details synchronously
5. `TradeService` builds `EnrichedTrade`
6. `LoggingClient` publishes enriched JSON to `trade-log-topic`

## Kafka Topics
| Topic | Format | Purpose |
|---|---|---|
| `trade-topic` | Raw XML String | Ingest pipeline |
| `trade-log-topic` | JSON (EnrichedTrade) | Audit trail |
| `trade-dlt` | Raw XML String | Dead letter (auto-created by Spring) |

## Retry Strategy (Non-Negotiable)
- `@RetryableTopic`: 4 attempts (1 original + 3 retries)
- Exponential backoff: 5s → 10s → 20s (multiplier=2)
- `@DltHandler` routes to `trade-dlt` after all retries exhausted

## Exception Classification (Non-Negotiable)
| Exception | Retryable? | Expected Behavior |
|---|---|---|
| `InvalidXmlException` | ❌ No | Skip silently |
| `RecoverableException` | ✅ Yes | Retry → DLT |
| `HttpClientErrorException` (4xx) | ❌ No | Account not found → skip |
| `ResourceAccessException` | ✅ Yes | Wrap in `RecoverableException` → retry |
| `HttpServerErrorException` (5xx) | ✅ Yes | Wrap in `RecoverableException` → retry |

## Key Classes
| Class | Role |
|---|---|
| `TradeProducerController` | REST endpoint — POST /trade/publish |
| `TradeConsumer` | @KafkaListener + @RetryableTopic + @DltHandler |
| `TradeService` | Core enrichment logic |
| `AccountClient` | RestTemplate calls to account-service |
| `LoggingClient` | KafkaTemplate publisher to trade-log-topic |
| `Trade` | Raw XML-mapped entity (@JacksonXmlRootElement) |
| `EnrichedTrade` | Trade + AccountDTO details combined |
| `AccountDTO` | Account data transfer object |

## Technology Stack
- Java 17, Spring Boot 3.2.5, Spring Kafka
- PostgreSQL (account data), Jackson XmlMapper (XML parsing)
- RestTemplate (sync HTTP), KafkaTemplate (async messaging)
- JUnit 5 + Mockito (testing), JaCoCo (coverage)

---

## Team Engineering Standards — Enforce These Rules

### EX-1 · Exception Hierarchy Must Be Respected
- Custom exceptions for retryable failures MUST extend `RecoverableException`
- Custom exceptions for non-retryable failures MUST extend the non-retryable base (e.g. `InvalidXmlException`)
- Never catch a retryable exception and swallow it — must re-throw or wrap in `RecoverableException`

### EX-2 · Correct Wrapping for Network Errors
- `ResourceAccessException` and `HttpServerErrorException` (5xx) MUST be caught and wrapped in `RecoverableException`
- `HttpClientErrorException` (4xx) MUST be caught and handled as a skip (NOT wrapped for retry)
- Flag any handler that catches these exceptions but does not follow the classification

### CFG-1 · No Hardcoded Topic Names
- Kafka topic names MUST come from `@Value("${...}")` or `@ConfigurationProperties`
- String literals like `"trade-topic"` or `"trade-log-topic"` in `@KafkaListener`, `KafkaTemplate.send()`, or `@RetryableTopic` are defects

### CFG-2 · No Hardcoded URLs or Ports
- Service URLs, ports, and base paths MUST come from config (`@Value` or `@ConfigurationProperties`)
- Flag any hardcoded `http://localhost:8085` or similar strings

### STYLE-1 · Java 17 Idioms
- Prefer: `var` for local variables where type is obvious, `record` for pure DTOs, text blocks for multi-line strings
- Flag: raw types, unnecessary casts, pre-Java-8 collection patterns

### STYLE-2 · Method Length and SRP
- Methods over ~30 lines that mix concerns (parsing + enrichment + publishing in one method) should be flagged for extraction
- Each method should have one clear responsibility
