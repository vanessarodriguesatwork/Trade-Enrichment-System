# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-05-09 17:22:01 UTC  
**Analyzer:** Claude AI (claude-sonnet-4-20250514)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 1 | 8 | 4 | 0 |

## Analysis Summary

Issue #2 introduces amount truncation rules requiring all trade amounts to be truncated to exactly 2 decimal places without rounding. Need to modify existing test cases to validate truncation behavior and add new test cases for edge cases like padding with zeros and handling various decimal precisions.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #2 | Update expected output amount to show exact 2 decimal places formatting as per AC2 |
| MODIFY | TC-006 | #2 | Update expected output amount from 4500.5 to 4500.50 as per AC2 requiring exactly 2 decimal places |
| MODIFY | TC-008 | #2 | Update expected output amount from 4500.50 to match truncated input from 4500.5 as per AC2 |
| MODIFY | TC-009 | #2 | Update expected output amount from 2200.00 to match padded input from 2200 as per AC5 |
| MODIFY | TC-011 | #2 | Update expected output amount from 1100.00 to match padded input from 1100 as per AC5 |
| MODIFY | TC-013 | #2 | Update expected output amount from 900.00 to match padded input from 900 as per AC5 |
| MODIFY | TC-017 | #2 | Update expected output amount from 3300.00 to match padded input from 3300 as per AC5 |
| MODIFY | TC-021 | #2 | Update expected output amount from 2800.50 to match padded input from 2800.5 as per AC4 |
| INSERT | TC-022 | #2 | Test AC1 and AC6 - truncation of amounts with more than 2 decimal places without rounding |
| INSERT | TC-023 | #2 | Test AC3 and AC6 - truncation should not round 125.999 to 126.00 but truncate to 125.99 |
| INSERT | TC-024 | #2 | Test AC8 - negative amounts should be handled consistently with truncation rules |
| INSERT | TC-025 | #2 | Test AC8 - zero amount should be formatted to 0.00 as per AC5 |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount
- **trade_id:** TRD-0001
- **tradeId:** TRD-0001
- **time:** 2026-05-05T09:00:00Z
- **amount:** 1500.25
- **partyAccount1:** ACC-101
- **partyAccount2:** ACC-202
- **partyAccount1_accountNumber:** ACC-101
- **partyAccount1_holderName:** Aarav Sharma
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-202
- **partyAccount2_holderName:** Ishaan Malhotra
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details

#### TC-006 — modify
- **scenario_id:** TC-006
- **description:** Invalid trade - missing amount field in XML
- **trade_id:** TRD-0004
- **tradeId:** TRD-0004
- **time:** 2026-05-05T10:00:00Z
- **amount:** MISSING
- **partyAccount1:** ACC-117
- **partyAccount2:** ACC-218
- **expected_output:** REJECTED - routed to trade-topic-dlt with rejectionReason=MISSING_MANDATORY_FIELD

#### TC-008 — modify
- **scenario_id:** TC-008
- **description:** Enrichment failure - sellerId not found in Account Service (404)
- **trade_id:** TRD-0006
- **tradeId:** TRD-0006
- **time:** 2026-05-05T10:10:00Z
- **amount:** 4500.50
- **partyAccount1:** ACC-119
- **partyAccount2:** ACC-INVALID
- **expected_output:** ENRICHMENT_FAILED - routed to trade-topic-dlt with rejectionReason=ENRICHMENT_FAILED

#### TC-009 — modify
- **scenario_id:** TC-009
- **description:** Enrichment failure - Account Service returns 500 for buyerId
- **trade_id:** TRD-0007
- **tradeId:** TRD-0007
- **time:** 2026-05-05T10:15:00Z
- **amount:** 2200.00
- **partyAccount1:** ACC-121
- **partyAccount2:** ACC-222
- **expected_output:** ENRICHMENT_FAILED after 3 retries - routed to trade-topic-dlt with rejectionReason=ENRICHMENT_FAILED

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure
- **trade_id:** TRD-0009
- **tradeId:** TRD-0009
- **time:** 2026-05-05T10:35:00Z
- **amount:** 1100.00
- **partyAccount1:** ACC-129
- **partyAccount2:** ACC-230
- **partyAccount1_accountNumber:** ACC-129
- **partyAccount1_holderName:** Divya Rao
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-230
- **partyAccount2_holderName:** Aisha Menon
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message
- **trade_id:** TRD-0011
- **tradeId:** TRD-0011
- **time:** 2026-05-05T10:45:00Z
- **amount:** 900.00
- **partyAccount1:** ACC-133
- **partyAccount2:** ACC-234
- **partyAccount1_accountNumber:** ACC-133
- **partyAccount1_holderName:** Meera Desai
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-234
- **partyAccount2_holderName:** Prachi Doshi
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully

#### TC-017 — modify
- **scenario_id:** TC-020
- **description:** Partial enrichment - only buyer account available seller is 404
- **trade_id:** TRD-0017
- **tradeId:** TRD-0017
- **time:** 2026-05-05T11:20:00Z
- **amount:** 3300.00
- **partyAccount1:** ACC-145
- **partyAccount2:** ACC-INVALID
- **expected_output:** ENRICHMENT_FAILED - routed to trade-topic-dlt as complete enrichment is required before publish

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field is string type not boolean or enum
- **trade_id:** TRD-0018
- **tradeId:** TRD-0018
- **time:** 2026-05-05T11:25:00Z
- **amount:** 2800.50
- **partyAccount1:** ACC-147
- **partyAccount2:** ACC-248
- **partyAccount1_accountNumber:** ACC-147
- **partyAccount1_holderName:** Amit Chauhan
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-248
- **partyAccount2_holderName:** Deepika Shetty
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Amount truncation - more than 2 decimal places should be truncated without rounding
- **trade_id:** TRD-0019
- **tradeId:** TRD-0019
- **time:** 2026-05-05T11:30:00Z
- **amount:** 15000.98
- **partyAccount1:** ACC-149
- **partyAccount2:** ACC-250
- **partyAccount1_accountNumber:** ACC-149
- **partyAccount1_holderName:** Rohit Kumar
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-250
- **partyAccount2_holderName:** Sneha Patel
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - amount 15000.9876 truncated to 15000.98 without rounding

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Amount truncation - verify no rounding occurs for 125.999
- **trade_id:** TRD-0020
- **tradeId:** TRD-0020
- **time:** 2026-05-05T11:35:00Z
- **amount:** 125.99
- **partyAccount1:** ACC-151
- **partyAccount2:** ACC-252
- **partyAccount1_accountNumber:** ACC-151
- **partyAccount1_holderName:** Arjun Singh
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-252
- **partyAccount2_holderName:** Pooja Agarwal
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - amount 125.999 truncated to 125.99 without rounding

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Amount truncation - negative amount with multiple decimal places
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Vikram Joshi
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Anjali Verma
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - negative amount -1234.5678 truncated to -1234.56

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Amount truncation - zero amount should be formatted to 0.00
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Gaurav Mehta
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Rashmi Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - zero amount 0 formatted to 0.00

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| CREATE | TRD-0019.xml | New test case for amount truncation with multiple decimal places |
| CREATE | TRD-0020.xml | New test case for verifying no rounding occurs during truncation |
| CREATE | TRD-0021.xml | New test case for negative amount truncation |
| CREATE | TRD-0022.xml | New test case for zero amount formatting |

### XML File Contents

#### TRD-0019.xml
```xml
<trade>
    <tradeId>TRD-0019</tradeId>
    <time>2026-05-05T11:30:00Z</time>
    <amount>15000.9876</amount>
    <partyAccount1>ACC-149</partyAccount1>
    <partyAccount2>ACC-250</partyAccount2>
</trade>
```

#### TRD-0020.xml
```xml
<trade>
    <tradeId>TRD-0020</tradeId>
    <time>2026-05-05T11:35:00Z</time>
    <amount>125.999</amount>
    <partyAccount1>ACC-151</partyAccount1>
    <partyAccount2>ACC-252</partyAccount2>
</trade>
```

#### TRD-0021.xml
```xml
<trade>
    <tradeId>TRD-0021</tradeId>
    <time>2026-05-05T11:40:00Z</time>
    <amount>-1234.5678</amount>
    <partyAccount1>ACC-153</partyAccount1>
    <partyAccount2>ACC-254</partyAccount2>
</trade>
```

#### TRD-0022.xml
```xml
<trade>
    <tradeId>TRD-0022</tradeId>
    <time>2026-05-05T11:45:00Z</time>
    <amount>0</amount>
    <partyAccount1>ACC-155</partyAccount1>
    <partyAccount2>ACC-256</partyAccount2>
</trade>
```

---

## Traceability Matrix

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: The system shall truncate incoming trade amounts to a maximum of two decimal places
- AC2: The system shall always format the final output to exactly two decimal places
- AC3: No rounding shall be applied under any circumstance
- AC4: If the input has fewer than 2 decimal places, the system shall pad with trailing zeros
- AC5: If the input has no decimal places, the system shall append .00
- AC6: If the input has more than 2 decimal places, all extra digits shall be discarded after truncation
- AC7: The formatting shall be consistent across all enriched trade outputs and downstream systems
- AC8: The system shall support positive, zero, and negative numeric values consistently

#### Scenarios Impacted

`TC-001`, `TC-006`, `TC-008`, `TC-009`, `TC-011`, `TC-013`, `TC-020`, `TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1&AC6 covered by TC-022,TC-023 (truncation); AC2&AC7 covered by all modified scenarios (exact 2 decimal format); AC3 covered by TC-023 (no rounding); AC4 covered by existing scenarios with 1 decimal; AC5 covered by TC-009,TC-011,TC-013,TC-020,TC-025 (padding zeros); AC8 covered by TC-024 (negative) and TC-025 (zero)
