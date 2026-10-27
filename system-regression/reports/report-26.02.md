# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-10-27 06:03:47 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 4 | 0 |

## Analysis Summary

Kept changes represent genuine new testing behavior introduced by Issue #1 (buyerSellerIndicator field). Seven existing rows (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021) had their descriptions updated to explicitly test a new buyerSellerIndicator condition (valid BUYER uppercase, valid SELLER uppercase, lowercase buyer, mixed-case Seller, missing tag, blank tag, invalid value) that did not exist in the original test description, so these are retained as genuine new coverage. Four new scenarios (TC-022, TC-023, TC-024, TC-025) were inserted to cover amount truncation, sign preservation, and zero-padding conditions (Issue #2) that had no prior CSV representation at all, so these are retained as genuine new coverage. Removed were the three Issue #2 'global sweep' modifications to TC-011, TC-013, and TC-021: these rows' descriptions were already updated by Issue #1's changes to reflect the buyerSellerIndicator condition, and the Issue #2 edits only corrected the expected amount value (e.g., 1100 -> 1100.00) to conform to the new formatting rule without altering the description or tested condition at all — these are pure expected-value corrections on an already-tested condition, not new testing behavior.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | TRD-0001 is an existing valid/published trade; extended to also carry buyerSellerIndicator=SELLER (uppercase) to cover AC2/AC3/AC8-scenario2 without conflicting with its original amount/enrichment assertions. |
| MODIFY | TC-011 | #1 | TRD-0009 already asserts full published message structure; extended to carry buyerSellerIndicator='buyer' (lowercase) to cover AC3/AC8-scenario3 (case-insensitivity). |
| MODIFY | TC-013 | #1 | TRD-0011 tests consumer recovery after malformed message; extended to carry buyerSellerIndicator='Seller' (mixed case) to cover AC3/AC8-scenario4. |
| MODIFY | TC-016 | #1 | TRD-0014.xml already has no buyerSellerIndicator tag, which exactly matches the 'tag missing entirely' input condition (AC4/AC8-scenario5). No XML change needed; only description/expected_output updated to assert the field is omitted from output. |
| MODIFY | TC-017 | #1 | TRD-0015 is a valid published trade; extended with blank buyerSellerIndicator tag to cover AC5/AC8-scenario6 (default to 'B'). |
| MODIFY | TC-018 | #1 | TRD-0016 asserts amount unchanged; extended with invalid buyerSellerIndicator='UNKNOWN' to cover AC6/AC8-scenario7 (invalid value -> empty string). |
| MODIFY | TC-021 | #1 | This pre-existing row's description already referenced buyerSellerIndicator as a string field but had no expected_output filled in and TRD-0018.xml lacked the tag. Completed the test by adding buyerSellerIndicator='BUYER' to XML and filling in the full expected output to cover AC1/AC2/AC3/AC7/AC8-scenario1. |
| INSERT | TC-022 | #2 | Checked all existing XML files - no existing CSV row tests a published trade with an amount containing more than 2 decimal places (4 decimals) requiring truncation (AC1, AC3). TRD-0019.xml already exists in the trades directory with amount 15000.9876 but has no CSV row referencing it. Existing published rows (TC-001, TC-016, TC-017, TC-018) all have amounts with <=2 decimals already, so none could be modified without changing their original input condition/XML. Reusing the existing TRD-0019.xml and inserting a new scenario is the correct action. |
| INSERT | TC-023 | #2 | Checked all existing XML files - no existing CSV row tests a published trade with an amount containing exactly 3 decimal places requiring truncation (AC3). TRD-0020.xml already exists in the trades directory with amount 125.999 but has no CSV row referencing it. No existing published test case could be modified to this exact input without altering its original tested condition, so a new scenario row was inserted reusing this existing XML. |
| INSERT | TC-024 | #2 | Checked all existing XML files - no existing CSV row tests a published trade with a negative amount containing more than 2 decimal places, which is required to validate sign preservation during truncation (AC3, sign preservation rule). TRD-0021.xml already exists with amount -1234.5678 but has no CSV row referencing it. No existing row covers negative amounts at all, so an existing test case could not be modified without conflicting with its current tested condition; inserting a new scenario reusing this existing XML was the correct action. |
| INSERT | TC-025 | #2 | Checked all existing XML files - while TC-011 and TC-013 (after modification) cover integer amounts padded to .00, no existing row specifically tests the edge case of a zero-value amount for the 2-decimal formatting rule (AC4). TRD-0022.xml already exists with amount 0 but has no CSV row referencing it. This zero-value edge case is a distinct boundary condition worth explicit coverage and could not be merged into TC-011/TC-013 without changing their already-distinct input conditions, so a new scenario was inserted reusing this existing XML. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount; buyerSellerIndicator SELLER (uppercase) converted to abbreviated 'S'
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator 'SELLER' converted to abbreviated 'S'

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure; buyerSellerIndicator lowercase 'buyer' converted to abbreviated 'B'
- **trade_id:** TRD-0009
- **tradeId:** TRD-0009
- **time:** 2026-05-05T10:35:00Z
- **amount:** 1100
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields; buyerSellerIndicator lowercase 'buyer' converted to abbreviated 'B'

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; buyerSellerIndicator mixed-case 'Seller' converted to abbreviated 'S'
- **trade_id:** TRD-0011
- **tradeId:** TRD-0011
- **time:** 2026-05-05T10:45:00Z
- **amount:** 900
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator mixed-case 'Seller' converted to abbreviated 'S'

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value; buyerSellerIndicator tag missing entirely so field is omitted from enriched output (backward compatible), warning logged
- **trade_id:** TRD-0014
- **tradeId:** TRD-0014
- **time:** 2026-05-05T11:00:00Z
- **amount:** 9999999.99
- **partyAccount1:** ACC-139
- **partyAccount2:** ACC-240
- **partyAccount1_accountNumber:** ACC-139
- **partyAccount1_holderName:** Rahul Gupta
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-240
- **partyAccount2_holderName:** Aditya Mishra
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator field is omitted entirely from output since tag is missing from input, warning logged

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount; buyerSellerIndicator tag present but blank defaults to 'B', warning logged
- **trade_id:** TRD-0015
- **tradeId:** TRD-0015
- **time:** 2026-05-05T11:05:00Z
- **amount:** 0.01
- **partyAccount1:** ACC-141
- **partyAccount2:** ACC-242
- **partyAccount1_accountNumber:** ACC-141
- **partyAccount1_holderName:** Kavya Reddy
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-242
- **partyAccount2_holderName:** Lakshmi Nambiar
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator blank tag defaults to 'B', warning logged

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; buyerSellerIndicator invalid value 'UNKNOWN' results in empty string, warning logged
- **trade_id:** TRD-0016
- **tradeId:** TRD-0016
- **time:** 2026-05-05T11:10:00Z
- **amount:** 1250.75
- **partyAccount1:** ACC-143
- **partyAccount2:** ACC-244
- **partyAccount1_accountNumber:** ACC-143
- **partyAccount1_holderName:** Nikhil Jain
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-244
- **partyAccount2_holderName:** Harsh Trivedi
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED - amount field in trade-log-topic message equals 1250.75 unchanged; buyerSellerIndicator invalid value 'UNKNOWN' results in empty string '', warning logged

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field is string type not boolean or enum; valid BUYER (uppercase) converted to abbreviated 'B'
- **trade_id:** TRD-0018
- **tradeId:** TRD-0018
- **time:** 2026-05-05T11:25:00Z
- **amount:** 2800.5
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator 'BUYER' converted to abbreviated 'B'

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Published trade with amount containing 4 decimal places; amount truncated (not rounded) to 2 decimal places in Kafka output; buyerSellerIndicator tag missing entirely so field is omitted from output, warning logged
- **trade_id:** TRD-0019
- **tradeId:** TRD-0019
- **time:** 2026-05-05T11:30:00Z
- **amount:** 15000.98
- **partyAccount1:** ACC-149
- **partyAccount2:** ACC-250
- **partyAccount1_accountNumber:** ACC-149
- **partyAccount1_holderName:** Rohan Verma
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-250
- **partyAccount2_holderName:** Simran Kaur
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 15000.9876 to 15000.98 with no rounding applied; buyerSellerIndicator field omitted entirely from output since tag is missing from input, warning logged

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Published trade with amount containing 3 decimal places; amount truncated (not rounded) to 2 decimal places in Kafka output; buyerSellerIndicator tag missing entirely so field is omitted from output, warning logged
- **trade_id:** TRD-0020
- **tradeId:** TRD-0020
- **time:** 2026-05-05T11:35:00Z
- **amount:** 125.99
- **partyAccount1:** ACC-151
- **partyAccount2:** ACC-252
- **partyAccount1_accountNumber:** ACC-151
- **partyAccount1_holderName:** Vikram Nair
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-252
- **partyAccount2_holderName:** Anjali Rao
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 125.999 to 125.99 with no rounding applied; buyerSellerIndicator field omitted entirely from output since tag is missing from input, warning logged

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Published trade with negative amount containing 4 decimal places; amount truncated (not rounded) to 2 decimal places with sign preserved in Kafka output; buyerSellerIndicator tag missing entirely so field is omitted from output, warning logged
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Karan Mehta
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Priya Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; negative amount truncated from -1234.5678 to -1234.56 with sign preserved and no rounding applied; buyerSellerIndicator field omitted entirely from output since tag is missing from input, warning logged

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Published trade with zero-value integer amount (no decimal places); amount formatted to exactly 2 decimal places by appending .00 in Kafka output; buyerSellerIndicator tag missing entirely so field is omitted from output, warning logged
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Suresh Kumar
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Neha Joshi
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; zero-value amount formatted as 0.00 with two decimal places appended; buyerSellerIndicator field omitted entirely from output since tag is missing from input, warning logged

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0001.xml | Add buyerSellerIndicator=SELLER (uppercase) to cover valid SELLER conversion scenario (AC2/AC8-scenario2) for TC-001. |
| MODIFY | TRD-0009.xml | Add buyerSellerIndicator=buyer (lowercase) to cover case-insensitivity scenario (AC3/AC8-scenario3) for TC-011. |
| MODIFY | TRD-0011.xml | Add buyerSellerIndicator=Seller (mixed case) to cover case-insensitivity scenario (AC3/AC8-scenario4) for TC-013. |
| MODIFY | TRD-0015.xml | Add blank buyerSellerIndicator tag to cover the 'present but blank -> default B' scenario (AC5/AC8-scenario6) for TC-017. |
| MODIFY | TRD-0016.xml | Add invalid buyerSellerIndicator=UNKNOWN to cover the invalid-value -> empty string scenario (AC6/AC8-scenario7) for TC-018. |
| MODIFY | TRD-0018.xml | Add buyerSellerIndicator=BUYER to complete TC-021's intended assertion on string-type field with a valid value (AC1/AC2/AC8-scenario1). |

### XML File Contents

#### TRD-0001.xml
```xml
<trade>
    <tradeId>TRD-0001</tradeId>
    <time>2026-05-05T09:00:00Z</time>
    <amount>1500.25</amount>
    <partyAccount1>ACC-101</partyAccount1>
    <partyAccount2>ACC-202</partyAccount2>
    <buyerSellerIndicator>SELLER</buyerSellerIndicator>
</trade>
```

#### TRD-0009.xml
```xml
<trade>
    <tradeId>TRD-0009</tradeId>
    <time>2026-05-05T10:35:00Z</time>
    <amount>1100</amount>
    <partyAccount1>ACC-129</partyAccount1>
    <partyAccount2>ACC-230</partyAccount2>
    <buyerSellerIndicator>buyer</buyerSellerIndicator>
</trade>
```

#### TRD-0011.xml
```xml
<trade>
    <tradeId>TRD-0011</tradeId>
    <time>2026-05-05T10:45:00Z</time>
    <amount>900</amount>
    <partyAccount1>ACC-133</partyAccount1>
    <partyAccount2>ACC-234</partyAccount2>
    <buyerSellerIndicator>Seller</buyerSellerIndicator>
</trade>
```

#### TRD-0015.xml
```xml
<trade>
    <tradeId>TRD-0015</tradeId>
    <time>2026-05-05T11:05:00Z</time>
    <amount>0.01</amount>
    <partyAccount1>ACC-141</partyAccount1>
    <partyAccount2>ACC-242</partyAccount2>
    <buyerSellerIndicator></buyerSellerIndicator>
</trade>
```

#### TRD-0016.xml
```xml
<trade>
    <tradeId>TRD-0016</tradeId>
    <time>2026-05-05T11:10:00Z</time>
    <amount>1250.75</amount>
    <partyAccount1>ACC-143</partyAccount1>
    <partyAccount2>ACC-244</partyAccount2>
    <buyerSellerIndicator>UNKNOWN</buyerSellerIndicator>
</trade>
```

#### TRD-0018.xml
```xml
<trade>
    <tradeId>TRD-0018</tradeId>
    <time>2026-05-05T11:25:00Z</time>
    <amount>2800.5</amount>
    <partyAccount1>ACC-147</partyAccount1>
    <partyAccount2>ACC-248</partyAccount2>
    <buyerSellerIndicator>BUYER</buyerSellerIndicator>
</trade>
```

---

## Traceability Matrix

### Issue #1: Add Buyer/Seller Indicator (B/S) to Enriched Trade Output

#### Acceptance Criteria

- AC1: Identify buyer/seller role via buyerSellerIndicator field
- AC2: Valid values convert BUYER->B, SELLER->S
- AC3: Case-insensitive input handling
- AC4: Missing tag -> field omitted entirely, warning logged
- AC5: Blank tag -> defaults to 'B', warning logged
- AC6: Invalid value -> empty string, warning logged
- AC7: Processing must not fail due to missing/blank/invalid value
- AC8: Business scenarios 1-7 (BUYER upper, SELLER upper, buyer lower, Seller mixed, missing, blank, invalid)

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`

#### Coverage Notes

All 7 AC8 scenarios and AC1-AC7 are covered by modifying 7 existing published/valid trade test cases rather than inserting new ones. TC-021 (BUYER uppercase) and TC-001 (SELLER uppercase) cover AC2. TC-011 (lowercase buyer) and TC-013 (mixed-case Seller) cover AC3 case-insensitivity. TC-016 reuses TRD-0014.xml as-is (already lacking the tag) to cover AC4 missing-tag/omission without any XML change. TC-017 adds a blank tag to cover AC5 default-to-B. TC-018 adds an invalid value to cover AC6 empty-string behavior. AC7 (no processing failure) is demonstrated by TC-016/TC-017/TC-018 all still being PUBLISHED successfully despite missing/blank/invalid indicator values.

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: The system shall always format the final output to exactly two decimal places without rounding.
- AC2: If the input has fewer than 2 decimal places, the system shall pad with trailing zeros.
- AC3: If the input has more than 2 decimal places, all extra digits shall be discarded after truncation with no rounding.
- AC4: If the input has no decimal places, the system shall append .00 to ensure 2 decimal places.

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1 (always exactly 2 decimals) is validated across all PUBLISHED rows (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021-025). AC2 (padding fewer decimals) is covered by TC-021 (2800.5->2800.50). AC3 (truncation of extra decimals, no rounding) is covered by newly inserted TC-022 (4 decimals), TC-023 (3 decimals), and TC-024 (negative amount with 4 decimals, validating sign preservation). AC4 (append .00 for no decimal places) is covered by corrected TC-011 (1100->1100.00), TC-013 (900->900.00), and newly inserted TC-025 (zero-value edge case). Three existing rows were MODIFIED via the global format sweep since their amounts did not conform to the new rule but their input/XML and tested condition remained otherwise unchanged. Four rows were INSERTED because existing XML files (TRD-0019 to TRD-0022) already existed with unique decimal-precision input conditions not referenced by any CSV row, and no existing published row could be modified to cover these conditions without losing its original distinct test purpose.
