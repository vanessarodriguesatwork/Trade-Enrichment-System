# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-08-13 08:46:44 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 2 | 0 |

## Analysis Summary

All 9 csv_changes represent genuine new testing behavior and are retained. For issue #1, seven existing rows (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021) had their descriptions substantively expanded to explicitly document new buyerSellerIndicator scenarios (missing tag, SELLER uppercase, blank tag, invalid value, BUYER uppercase, Seller mixed-case, buyer lowercase respectively) that were not previously described or tested in these rows, even though the underlying trade validity condition remains the same base scenario. Each of these descriptions differs from the original CSV state, confirming a new condition is now being exercised alongside the original one. For issue #2, two new rows (TC-022, TC-023) are inserts covering previously untested truncation-without-rounding logic (AC3) including negative-sign preservation, both genuinely new conditions with no prior equivalent in the pack.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | Existing valid trade already lacks a buyerSellerIndicator tag, so it already exercises AC4 (tag missing -> field omitted, backward compatible). Per decision tree, description updated to explicitly document this coverage; no XML or other output changes needed. |
| MODIFY | TC-011 | #1 | No existing XML contained a valid SELLER (uppercase) buyerSellerIndicator. Modified TRD-0009 to add this tag so the existing 'all mandatory fields' test also verifies AC2/AC8-scenario2 (SELLER->S). Also corrected amount output to 2 decimal places per previously established amount formatting rule (issue #2) since the row is being touched. |
| MODIFY | TC-013 | #1 | No existing XML contained a blank buyerSellerIndicator tag. Modified TRD-0011 to add an empty tag so this existing consumer-recovery test also verifies AC5/AC8-scenario6 (blank tag defaults to 'B'). Also corrected amount output to 2 decimal places per accumulated amount formatting rule. |
| MODIFY | TC-016 | #1 | No existing XML contained an invalid buyerSellerIndicator value. Modified TRD-0014 to add 'UNKNOWN' so this existing high-amount valid trade test also verifies AC6/AC8-scenario7 (invalid value -> empty string). |
| MODIFY | TC-017 | #1 | No existing XML contained a valid BUYER (uppercase) buyerSellerIndicator. Modified TRD-0015 to add this tag so the existing minimum-amount valid trade test also verifies AC2/AC8-scenario1 (BUYER->B). |
| MODIFY | TC-018 | #1 | No existing XML contained a valid mixed-case 'Seller' buyerSellerIndicator. Modified TRD-0016 to add this tag so the existing amount-unchanged test also verifies AC3/AC8-scenario4 (Seller mixed-case -> S, case-insensitivity). |
| MODIFY | TC-021 | #1 | This row was already thematically tied to buyerSellerIndicator ('field is string type not boolean or enum') but had no expected_output populated and no tag in its XML. Modified TRD-0018 to add lowercase 'buyer' and completed the expected output to verify AC1/AC3/AC8-scenario3 (lowercase input -> 'B'). Also corrected amount output to 2 decimal places per accumulated amount formatting rule since the row is being touched. |
| INSERT | TC-022 | #2 | No existing CSV row exercises an input amount with MORE than 2 decimal places to validate truncation-without-rounding (AC3). Checked all existing XMLs: TC-001 (1500.25), TC-011 (1100 int), TC-013 (900 int), TC-016 (9999999.99), TC-017 (0.01), TC-018 (1250.75), TC-021 (2800.5) all have <=2 decimal places in input. The orphaned TRD-0019.xml (amount 15000.9876) exactly matches the issue's own example and has no CSV row referencing it, so it is reused via a new scenario rather than creating a new XML. |
| INSERT | TC-023 | #2 | No existing CSV row exercises a NEGATIVE amount with more than 2 decimal places to validate that truncation preserves the sign. Checked all existing published rows (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021, TC-022) - none use a negative amount. The orphaned TRD-0021.xml (amount -1234.5678) already exists with this exact condition and has no CSV row, so it is reused rather than creating a new XML. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount; also verifies buyerSellerIndicator tag is completely absent from input resulting in the field being omitted entirely from the enriched output, with a warning logged (backward compatibility, AC4)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator tag absent from input so the field is omitted entirely from output (warning logged)

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure; also verifies buyerSellerIndicator 'SELLER' (uppercase) is converted to abbreviated 'S' in enriched output (AC2)
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields; buyerSellerIndicator input 'SELLER' converted to 'S' in output

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; also verifies buyerSellerIndicator tag present but blank defaults to 'B' with a warning logged (AC5)
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator tag present but blank defaults to 'B' in output (warning logged)

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value; also verifies buyerSellerIndicator invalid value 'UNKNOWN' results in an empty string in output, with a warning logged (AC6)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'UNKNOWN' is invalid so output field is an empty string (warning logged)

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount; also verifies buyerSellerIndicator 'BUYER' (uppercase) converts to abbreviated 'B' in output (AC2)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'BUYER' converted to 'B' in output

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; also verifies buyerSellerIndicator 'Seller' (mixed case) converts to abbreviated 'S' in output demonstrating case-insensitivity (AC3)
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
- **expected_output:** PUBLISHED - amount field in trade-log-topic message equals 1250.75 unchanged; buyerSellerIndicator input 'Seller' (mixed case) converted to 'S' in output

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field is string type not boolean or enum; validates lowercase input 'buyer' converts to abbreviated 'B' in output, demonstrating case-insensitive handling (AC1, AC3)
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'buyer' (lowercase) converted to 'B' in output demonstrating case-insensitive handling

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Valid trade with amount containing 4 decimal places (15000.9876); verifies truncation without rounding to exactly 2 decimal places per AC3, and buyerSellerIndicator tag absent from input results in the field being omitted entirely from output (with warning logged)
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
- **partyAccount2_holderName:** Sneha Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount input 15000.9876 truncated (not rounded) to 15000.98 per AC3; buyerSellerIndicator tag absent from input so field omitted entirely from output (warning logged)

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Valid trade with negative amount containing 4 decimal places (-1234.5678); verifies truncation without rounding while preserving the negative sign per AC3, and buyerSellerIndicator tag absent from input results in the field being omitted entirely from output (with warning logged)
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Karan Kapoor
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Priya Nair
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount input -1234.5678 truncated (not rounded) to -1234.56 with negative sign preserved per AC3; buyerSellerIndicator tag absent from input so field omitted entirely from output (warning logged)

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0009.xml | Add buyerSellerIndicator=SELLER (uppercase) to cover AC2/AC8-scenario2 without conflicting with the original 'all mandatory fields' assertion. |
| MODIFY | TRD-0011.xml | Add blank buyerSellerIndicator tag to cover AC5/AC8-scenario6 (defaults to 'B') without conflicting with the consumer-recovery assertion. |
| MODIFY | TRD-0014.xml | Add invalid buyerSellerIndicator=UNKNOWN to cover AC6/AC8-scenario7 (empty string output) without conflicting with the high-amount valid trade assertion. |
| MODIFY | TRD-0015.xml | Add buyerSellerIndicator=BUYER (uppercase) to cover AC2/AC8-scenario1 without conflicting with the minimum-amount assertion. |
| MODIFY | TRD-0016.xml | Add buyerSellerIndicator=Seller (mixed case) to cover AC3/AC8-scenario4 (case-insensitivity) without conflicting with the amount-unchanged assertion. |
| MODIFY | TRD-0018.xml | Add buyerSellerIndicator=buyer (lowercase) to cover AC1/AC3/AC8-scenario3 (case-insensitivity), completing the previously unfinished test intent of this row. |
| DELETE | TRD-0020.xml | Orphaned XML (no CSV row references it) testing 3-decimal truncation (125.999->125.99). Redundant with TC-022 (TRD-0019) which already validates the truncate-without-rounding rule (AC3) with a different decimal count; the truncation logic being tested is identical regardless of the number of extra decimal digits, so this file is removed to avoid duplicate coverage per consolidation guidance. |
| DELETE | TRD-0022.xml | Orphaned XML (no CSV row references it) testing zero/no-decimal amount (0->0.00). Redundant with TC-011 (TRD-0009, amount 1100->1100.00) and TC-013 (TRD-0011, amount 900->900.00), which already validate AC4 (no decimal places -> append '.00'). Removed to avoid duplicate coverage. |

### XML File Contents

#### TRD-0009.xml
```xml
<trade>
    <tradeId>TRD-0009</tradeId>
    <time>2026-05-05T10:35:00Z</time>
    <amount>1100</amount>
    <partyAccount1>ACC-129</partyAccount1>
    <partyAccount2>ACC-230</partyAccount2>
    <buyerSellerIndicator>SELLER</buyerSellerIndicator>
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
    <buyerSellerIndicator></buyerSellerIndicator>
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
    <buyerSellerIndicator>UNKNOWN</buyerSellerIndicator>
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
    <buyerSellerIndicator>BUYER</buyerSellerIndicator>
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
    <buyerSellerIndicator>buyer</buyerSellerIndicator>
</trade>
```

---

## Traceability Matrix

### Issue #1: Add Buyer/Seller Indicator (B/S) to Enriched Trade Output

#### Acceptance Criteria

- AC1: Identify buyer/seller role via buyerSellerIndicator field
- AC2: Valid BUYER->"B", SELLER->"S"
- AC3: Case-insensitive input handling
- AC4: Missing tag -> field omitted entirely, warning logged
- AC5: Blank tag -> defaults to "B", warning logged
- AC6: Invalid value -> empty string, warning logged
- AC7: Processing must not fail on missing/blank/invalid value
- AC8: Business scenarios 1-7 (BUYER upper, SELLER upper, buyer lower, Seller mixed, missing, blank, invalid)

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`

#### Coverage Notes

TC-001 covers AC4/scenario5 (tag missing, already the case in existing XML, description updated only). TC-017 covers AC2/scenario1 (BUYER uppercase->B). TC-011 covers AC2/scenario2 (SELLER uppercase->S). TC-021 covers AC1/AC3/scenario3 (buyer lowercase->B). TC-018 covers AC3/scenario4 (Seller mixed-case->S). TC-013 covers AC5/scenario6 (blank->B). TC-016 covers AC6/scenario7 (invalid->empty string). AC7 (no processing failure) is demonstrated across all these rows since they all remain PUBLISHED despite missing/blank/invalid indicator values. All coverage achieved via MODIFY of existing valid-trade test cases per decision tree, avoiding unnecessary INSERTs.

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: Output shall always show exactly 2 decimal places
- AC2: Fewer than 2 decimal places shall be padded with trailing zeros
- AC3: More than 2 decimal places shall be truncated (no rounding)
- AC4: No decimal places shall have '.00' appended

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`, `TC-022`, `TC-023`

#### Coverage Notes

AC1 (general 2-decimal formatting) is validated across all existing published rows, all of which were already corrected in a prior sweep to conform to the 2-decimal rule (e.g., TC-001=1500.25, TC-016=9999999.99, TC-017=0.01). AC2 (padding fewer decimals) is covered by TC-021 (2800.5 -> 2800.50). AC4 (no decimals -> append .00) is covered by TC-011 (1100 -> 1100.00) and TC-013 (900 -> 900.00). AC3 (truncate extra decimals without rounding) was NOT covered by any existing row and required reusing two previously-orphaned XML files (TRD-0019, TRD-0021) via new scenarios TC-022 and TC-023, the latter also confirming sign preservation for negative amounts. Redundant orphaned XMLs (TRD-0020, TRD-0022) testing the same ACs with no new input dimension were removed.
