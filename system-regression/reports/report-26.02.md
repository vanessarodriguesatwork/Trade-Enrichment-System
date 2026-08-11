# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-08-11 10:55:11 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 4 | 0 |

## Analysis Summary

Kept all issue #1 changes (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021) because each of these modify entries added new descriptive text about buyerSellerIndicator behavior (missing tag, blank tag, invalid value, valid BUYER/SELLER in various cases) that was not present in the original descriptions, indicating each now tests a genuinely new condition. Also kept all four issue #2 inserts (TC-022, TC-023, TC-024, TC-025) as they introduce brand new scenario_ids covering truncation edge cases (4-decimal truncation, 3-decimal truncation, negative-sign truncation, zero-decimal padding) that did not exist in the original test pack. Removed the three issue #2 'modify' entries for TC-011, TC-013, and TC-021 because their descriptions are identical to the versions already established by the issue #1 changes to the same scenario_ids - these were pure formatting corrections to the amount output value (e.g., 1100->1100.00) applied via a global sweep, not new testing conditions, as explicitly stated in their own reason fields ('Description unchanged... only the amount output value is corrected').

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | TRD-0001.xml already lacks the buyerSellerIndicator tag entirely, which is the exact input condition for AC4/AC8-scenario#5 (tag missing -> field omitted, warning logged). No XML change needed; only description updated to reflect this additional assertion being verified. |
| MODIFY | TC-011 | #1 | TRD-0009.xml is a published trade used to verify mandatory field structure. Modified XML to add an empty buyerSellerIndicator tag to cover AC5/AC8-scenario#6 (blank tag defaults to 'B', warning logged), avoiding a new insert. |
| MODIFY | TC-013 | #1 | TRD-0011.xml is a published trade used for consumer resilience testing. Modified XML to add an invalid buyerSellerIndicator value (UNKNOWN) to cover AC6/AC8-scenario#7 (invalid value -> empty string, warning logged), combining non-conflicting scenarios in one test case. |
| MODIFY | TC-016 | #1 | TRD-0014.xml is a published high-amount trade. Modified XML to add buyerSellerIndicator=SELLER (uppercase) to cover AC2/AC8-scenario#2 (valid SELLER -> 'S'), reusing an existing scenario rather than inserting a new one. |
| MODIFY | TC-017 | #1 | TRD-0015.xml is a published minimum-amount trade. Modified XML to add buyerSellerIndicator=buyer (lowercase) to cover AC3/AC8-scenario#3 (case-insensitive valid buyer -> 'B'), reusing an existing scenario. |
| MODIFY | TC-018 | #1 | TRD-0016.xml is a published trade verifying amount unchanged. Modified XML to add buyerSellerIndicator=Seller (mixed case) to cover AC3/AC8-scenario#4 (case-insensitive valid Seller -> 'S'), reusing an existing scenario. |
| MODIFY | TC-021 | #1 | TRD-0018.xml/TC-021 was already a stub scenario intended to verify buyerSellerIndicator field typing but had no expected_output. Modified XML to add buyerSellerIndicator=BUYER (uppercase) to cover AC2/AC8-scenario#1 (valid BUYER -> 'B') and populated the missing expected_output. |
| INSERT | TC-022 | #2 | Existing XML TRD-0019.xml (amount=15000.9876, 4 decimal places) exists in the trades directory but has no corresponding CSV row. Checked all existing CSV rows for a published trade with >2 decimal input amount: none exist (TC-001, TC-016, TC-017, TC-018 all have exactly 2 decimal inputs already). This XML precisely matches the issue's own example (15000.9876 -> 15000.98) for AC1/AC3, so a new row is inserted reusing the existing XML rather than modifying an unrelated row, since none of the existing published-trade rows carry this specific >2-decimal-place input condition. |
| INSERT | TC-023 | #2 | Existing XML TRD-0020.xml (amount=125.999, 3 decimal places) exists in the trades directory but has no corresponding CSV row. Checked all existing rows: none test a published trade with a 3-decimal amount requiring truncation (matches issue example 125.999->125.99). Inserted new row reusing this XML rather than modifying an existing row, since no existing published row carries this exact 3-decimal input condition. |
| INSERT | TC-024 | #2 | Existing XML TRD-0021.xml (amount=-1234.5678, negative with 4 decimal places) exists in the trades directory but has no corresponding CSV row. Checked all existing rows: none test a negative amount value requiring truncation with sign preservation. This is a genuinely unique input condition (negative amount) absent from all other XMLs, so a new row is inserted reusing this XML. |
| INSERT | TC-025 | #2 | Existing XML TRD-0022.xml (amount=0, no decimal places) exists in the trades directory but has no corresponding CSV row. Checked all existing published-trade rows: none carry a zero/integer amount requiring '.00' padding for a successfully published trade (TC-011/TC-013 originally had integer amounts but tested different buyerSellerIndicator conditions and are already being modified/reused for AC4 coverage; this XML with amount=0 specifically covers the zero-value edge case). Inserted new row reusing this XML. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount; buyerSellerIndicator tag missing from input so field is omitted entirely from enriched output with warning logged (backward compatibility)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator field omitted from output since tag is missing (warning logged)

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure; buyerSellerIndicator tag present but blank defaults to 'B' with warning logged
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
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields; buyerSellerIndicator defaults to 'B' when tag is present but blank (warning logged)

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; buyerSellerIndicator tag present with invalid value UNKNOWN results in empty string output with warning logged
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
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator set to empty string "" since input value UNKNOWN is invalid (warning logged)

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value; buyerSellerIndicator SELLER (uppercase) converts to abbreviated 'S'
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator=S

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount; buyerSellerIndicator lowercase 'buyer' converts to 'B' (case-insensitive handling)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator=B

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; buyerSellerIndicator mixed-case 'Seller' converts to 'S' (case-insensitive handling)
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED - amount field in trade-log-topic message equals 1250.75 unchanged; buyerSellerIndicator=S

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field is string type not boolean or enum; valid BUYER (uppercase) converts to abbreviated 'B'
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator=B

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Valid trade with amount having 4 decimal places; amount truncated to 2 decimals without rounding (15000.9876->15000.98); buyerSellerIndicator tag missing from input so field omitted from output with warning logged
- **trade_id:** TRD-0019
- **tradeId:** TRD-0019
- **time:** 2026-05-05T11:30:00Z
- **amount:** 15000.98
- **partyAccount1:** ACC-149
- **partyAccount2:** ACC-250
- **partyAccount1_accountNumber:** ACC-149
- **partyAccount1_holderName:** Rohan Kapoor
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-250
- **partyAccount2_holderName:** Sneha Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 15000.9876 to 15000.98 (extra digits beyond 2 decimals discarded, no rounding); buyerSellerIndicator omitted from output since tag is missing (warning logged)

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Valid trade with amount having 3 decimal places; amount truncated to 2 decimals without rounding (125.999->125.99); buyerSellerIndicator tag missing from input so field omitted from output with warning logged
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
- **partyAccount2_holderName:** Priya Menon
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 125.999 to 125.99 (extra digit beyond 2 decimals discarded, no rounding); buyerSellerIndicator omitted from output since tag is missing (warning logged)

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Valid trade with negative amount having 4 decimal places; amount truncated to 2 decimals without rounding, sign preserved (-1234.5678->-1234.56); buyerSellerIndicator tag missing from input so field omitted from output with warning logged
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Arjun Verma
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Neha Kulkarni
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from -1234.5678 to -1234.56 (negative sign preserved, extra digits discarded without rounding); buyerSellerIndicator omitted from output since tag is missing (warning logged)

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Valid trade with zero amount and no decimal places; amount formatted to 0.00 by appending 2 decimal places; buyerSellerIndicator tag missing from input so field omitted from output with warning logged
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Karan Malhotra
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Tanvi Joshi
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount formatted as 0.00 ('.00' appended since input had no decimal places); buyerSellerIndicator omitted from output since tag is missing (warning logged)

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0009.xml | Add blank buyerSellerIndicator tag to cover AC5 (blank tag defaults to 'B', warning logged) for TC-011. |
| MODIFY | TRD-0011.xml | Add invalid buyerSellerIndicator value (UNKNOWN) to cover AC6 (invalid value -> empty string, warning logged) for TC-013. |
| MODIFY | TRD-0014.xml | Add buyerSellerIndicator=SELLER (uppercase) to cover AC2 valid SELLER scenario for TC-016. |
| MODIFY | TRD-0015.xml | Add buyerSellerIndicator=buyer (lowercase) to cover AC3 case-insensitivity scenario for TC-017. |
| MODIFY | TRD-0016.xml | Add buyerSellerIndicator=Seller (mixed case) to cover AC3 case-insensitivity scenario for TC-018. |
| MODIFY | TRD-0018.xml | Add buyerSellerIndicator=BUYER (uppercase) to cover AC2 valid BUYER scenario for TC-021, populating the previously stubbed test. |

### XML File Contents

#### TRD-0009.xml
```xml
<trade>
    <tradeId>TRD-0009</tradeId>
    <time>2026-05-05T10:35:00Z</time>
    <amount>1100</amount>
    <partyAccount1>ACC-129</partyAccount1>
    <partyAccount2>ACC-230</partyAccount2>
    <buyerSellerIndicator></buyerSellerIndicator>
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
    <buyerSellerIndicator>UNKNOWN</buyerSellerIndicator>
</trade>
```

#### TRD-0014.xml
```xml
<trade>
    <tradeId>TRD-0014</tradeId>
    <time>2026-05-05T11:00:00Z</time>
    <amount>9999999.99</amount>
    <partyAccount1>ACC-139</partyAccount1>
    <partyAccount2>ACC-240</partyAccount2>
    <buyerSellerIndicator>SELLER</buyerSellerIndicator>
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
    <buyerSellerIndicator>buyer</buyerSellerIndicator>
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
    <buyerSellerIndicator>Seller</buyerSellerIndicator>
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

- AC1: Identify buyer/seller role from buyerSellerIndicator field
- AC2: Valid BUYER -> 'B', SELLER -> 'S'
- AC3: Case-insensitive input handling
- AC4: Missing tag -> field omitted, warning logged
- AC5: Blank tag -> defaults to 'B', warning logged
- AC6: Invalid value -> empty string, warning logged
- AC7: Processing must not fail due to missing/blank/invalid value
- AC8: Business scenarios 1-7 verifiable

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`

#### Coverage Notes

AC4 (missing tag) covered by TC-001 which already lacked the tag - only description updated, no XML change. AC5 (blank tag) covered by modifying TRD-0009.xml/TC-011. AC6 (invalid value) covered by modifying TRD-0011.xml/TC-013. AC2/AC3 (valid BUYER uppercase) covered by TC-021 (previously a stub test with no expected output); valid SELLER uppercase covered by TC-016; valid lowercase buyer covered by TC-017; valid mixed-case Seller covered by TC-018. All scenarios reuse existing published test cases and their XML files, satisfying AC1 and AC7 implicitly since all trades continue to be PUBLISHED successfully. No inserts were required.

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: System shall always format final output amount to exactly two decimal places without rounding
- AC2: If input has fewer than 2 decimal places, pad with trailing zeros
- AC3: If input has more than 2 decimal places, discard extra digits after truncation with no rounding
- AC4: If input has no decimal places, append '.00' to ensure 2 decimal places

#### Scenarios Impacted

`TC-011`, `TC-013`, `TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1 (always 2 decimals) is validated across all modified/inserted PUBLISHED rows. AC2 (pad trailing zeros) covered by TC-021 (2800.5->2800.50). AC3 (truncate extra digits, no rounding) covered by TC-022 (15000.9876->15000.98), TC-023 (125.999->125.99), and TC-024 (-1234.5678->-1234.56, also validating sign preservation). AC4 (append .00 for integer amounts) covered by TC-011 (1100->1100.00), TC-013 (900->900.00), and TC-025 (0->0.00). Existing orphaned XML files (TRD-0019 to TRD-0022) were reused via INSERT since they already contained the exact precision-edge-case input conditions needed; global sweep MODIFYs were applied to TC-011, TC-013, TC-021 since their existing published amounts violated the new 2-decimal-place formatting rule.
