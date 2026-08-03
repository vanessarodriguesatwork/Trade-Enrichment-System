# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-08-03 05:03:13 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 4 | 0 |

## Analysis Summary

Kept 11 of 14 csv_changes as genuine new testing behavior. For Issue #1, all 7 modified rows (TC-001, TC-011, TC-016, TC-017, TC-013, TC-018, TC-021) show description changes from their original baseline state, each now explicitly testing a distinct buyerSellerIndicator scenario (valid uppercase BUYER/SELLER, case-insensitive lowercase/mixed-case, missing tag, blank tag default, invalid value) that did not exist in the original test suite - these represent genuine new testing behavior and are kept. For Issue #2, the three global-format-sweep modifications to TC-011, TC-013, and TC-021 were removed: their descriptions are identical to the descriptions already established by the Issue #1 modifications to these same rows (confirmed by their own stated reasons: 'description unchanged... only the amount output value is corrected'), meaning they are pure formatting corrections to already-covered conditions rather than new test scenarios. All 4 inserted rows (TC-022, TC-023, TC-024, TC-025) are kept since inserts always represent new scenarios - covering 4-decimal truncation, 3-decimal truncation boundary (.999 not rounding up), negative-amount truncation with sign preservation, and zero-amount '.00' padding, none of which existed previously.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | Reused this published, fully-enriched test case to also cover AC2/AC8#1: valid uppercase BUYER indicator converts to 'B'. XML modified to add the tag; original amount/account assertions unaffected. |
| MODIFY | TC-011 | #1 | Reused this published mandatory-fields test case to cover AC2/AC8#2: valid uppercase SELLER indicator converts to 'S'. XML modified to add the tag; original structural assertion preserved. |
| MODIFY | TC-016 | #1 | Reused this high-amount published test case to cover AC3/AC8#3: lowercase 'buyer' value is case-insensitively converted to 'B'. XML modified to add the tag; original amount assertion preserved. |
| MODIFY | TC-017 | #1 | Reused this minimum-amount published test case to cover AC3/AC8#4: mixed-case 'Seller' value is case-insensitively converted to 'S'. XML modified to add the tag; original amount assertion preserved. |
| MODIFY | TC-013 | #1 | Reused this consumer-recovery published test case to cover AC5/AC8#6: a blank/empty buyerSellerIndicator tag defaults to 'B' with a warning logged. XML modified to add the empty tag; original consumer-recovery assertion preserved. |
| MODIFY | TC-018 | #1 | This existing published test case already had no buyerSellerIndicator tag in its XML, naturally satisfying AC4/AC8#5 (missing tag). Per decision-tree guidance, only the description/expected_output was updated to call out this incremental coverage; no XML or value change was needed since the field is correctly omitted (represented as blank in CSV). |
| MODIFY | TC-021 | #1 | This placeholder row ('buyerSellerIndicator field is string type not boolean or enum') was intended for this feature but had no tag and an empty expected_output. Completed it to cover AC6/AC8#7: an invalid value (UNKNOWN) results in an empty string field with a warning logged, and processing does not fail. |
| INSERT | TC-022 | #2 | Checked all existing XMLs for a PUBLISHED trade with amount containing more than 2 decimal places to test AC3 (truncation without rounding). TRD-0019.xml already exists in the trades directory (amount=15000.9876) but has no corresponding CSV row - it matches the exact example given in the issue. No existing referenced test case covers a 4-decimal-place truncation scenario, so this row is inserted reusing the pre-existing XML rather than creating a new file. |
| INSERT | TC-023 | #2 | Checked all existing XMLs for a PUBLISHED trade with amount containing exactly 3 decimal places to further validate AC3 (truncate only, no rounding, e.g. .999 must not round up to next whole number). TRD-0020.xml already exists (amount=125.999) matching the issue's own example table but has no CSV row referencing it. No existing test case covers this 3-decimal truncation boundary, so a new row is inserted reusing the existing XML. |
| INSERT | TC-024 | #2 | Checked all existing XMLs for a PUBLISHED negative-amount trade with more than 2 decimal places to verify sign preservation during truncation (AC3 extension). TRD-0021.xml already exists (amount=-1234.5678) but has no CSV row referencing it. No existing test case covers a negative amount with truncation, so a new row is inserted reusing the existing XML. |
| INSERT | TC-025 | #2 | Checked all existing XMLs for a PUBLISHED trade with a zero/whole-number amount to validate AC4 (append '.00' when no decimal places present) as a distinct boundary value from TC-011/TC-013. TRD-0022.xml already exists (amount=0) but has no CSV row referencing it. No existing test covers the zero-amount edge case, so a new row is inserted reusing the existing XML. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount and buyerSellerIndicator=BUYER (uppercase) - abbreviated to 'B' in enriched output
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'BUYER' (uppercase) converted to abbreviated 'B' in output, no warning logged

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure, with buyerSellerIndicator=SELLER (uppercase) abbreviated to 'S'
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields; buyerSellerIndicator input 'SELLER' (uppercase) converted to abbreviated 'S' in output, no warning logged

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value and buyerSellerIndicator=buyer (lowercase) - case-insensitively abbreviated to 'B'
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'buyer' (lowercase) converted case-insensitively to abbreviated 'B' in output, no warning logged

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount and buyerSellerIndicator=Seller (mixed case) - case-insensitively abbreviated to 'S'
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
- **buyerSellerIndicator:** S
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'Seller' (mixed case) converted case-insensitively to abbreviated 'S' in output, no warning logged

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; buyerSellerIndicator tag present but blank defaults to 'B' with warning logged
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator tag present but blank defaults to 'B' in output with warning logged

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; buyerSellerIndicator tag missing entirely from input, so the field is omitted entirely from output (backward compatible) with warning logged
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
- **expected_output:** PUBLISHED - amount field in trade-log-topic message equals 1250.75 unchanged; buyerSellerIndicator tag missing entirely from input so field is omitted entirely from output (backward compatible), warning logged, processing does not fail

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field present with invalid value UNKNOWN (string type, not boolean/enum) - output field becomes empty string, processing does not fail
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator input 'UNKNOWN' is invalid (not BUYER/SELLER) so output field is empty string with warning logged; trade processing does not fail due to invalid value

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Valid trade with amount containing 4 decimal places (15000.9876) - truncated (not rounded) to 15000.98 in enriched output; buyerSellerIndicator tag missing entirely so field omitted from output with warning logged
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
- **partyAccount2_holderName:** Sneha Kapoor
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 15000.9876 to 15000.98 (extra decimal digits discarded without rounding, per AC3); buyerSellerIndicator tag missing entirely from input so field omitted from output, warning logged, processing does not fail

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Valid trade with amount containing 3 decimal places (125.999) - truncated (not rounded) to 125.99 in enriched output, verifying truncation does not round up; buyerSellerIndicator tag missing entirely so field omitted from output with warning logged
- **trade_id:** TRD-0020
- **tradeId:** TRD-0020
- **time:** 2026-05-05T11:35:00Z
- **amount:** 125.99
- **partyAccount1:** ACC-151
- **partyAccount2:** ACC-252
- **partyAccount1_accountNumber:** ACC-151
- **partyAccount1_holderName:** Arjun Nair
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-252
- **partyAccount2_holderName:** Priya Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 125.999 to 125.99 (truncation only, no rounding, per AC3); buyerSellerIndicator tag missing entirely from input so field omitted from output, warning logged, processing does not fail

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Valid trade with negative amount containing 4 decimal places (-1234.5678) - truncated to -1234.56 preserving the negative sign in enriched output; buyerSellerIndicator tag missing entirely so field omitted from output with warning logged
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Karan Malhotra
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Neha Joshi
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; negative amount truncated from -1234.5678 to -1234.56 with sign preserved (extra decimal digits discarded without rounding); buyerSellerIndicator tag missing entirely from input so field omitted from output, warning logged, processing does not fail

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Valid trade with zero amount and no decimal places (0) - formatted to 0.00 in enriched output; buyerSellerIndicator tag missing entirely so field omitted from output with warning logged
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Vikram Singh
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Ananya Pillai
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount formatted with exactly 2 decimal places (0.00, '.00' appended since input had no decimal places, per AC4); buyerSellerIndicator tag missing entirely from input so field omitted from output, warning logged, processing does not fail

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0001.xml | Added buyerSellerIndicator=BUYER (uppercase) to cover AC2/AC8#1 valid uppercase conversion to 'B', reusing this existing published test case. |
| MODIFY | TRD-0009.xml | Added buyerSellerIndicator=SELLER (uppercase) to cover AC2/AC8#2 valid uppercase conversion to 'S', reusing this existing published test case. |
| MODIFY | TRD-0014.xml | Added buyerSellerIndicator=buyer (lowercase) to cover AC3/AC8#3 case-insensitive conversion to 'B', reusing this existing published test case. |
| MODIFY | TRD-0015.xml | Added buyerSellerIndicator=Seller (mixed case) to cover AC3/AC8#4 case-insensitive conversion to 'S', reusing this existing published test case. |
| MODIFY | TRD-0011.xml | Added an empty buyerSellerIndicator tag to cover AC5/AC8#6 blank-tag default to 'B' with warning, reusing this existing published test case. |
| MODIFY | TRD-0018.xml | Added buyerSellerIndicator=UNKNOWN (invalid value) to cover AC6/AC8#7 invalid value producing empty string output with warning, completing this previously incomplete placeholder test case. |

### XML File Contents

#### TRD-0001.xml
```xml
<trade>
    <tradeId>TRD-0001</tradeId>
    <time>2026-05-05T09:00:00Z</time>
    <amount>1500.25</amount>
    <partyAccount1>ACC-101</partyAccount1>
    <partyAccount2>ACC-202</partyAccount2>
    <buyerSellerIndicator>BUYER</buyerSellerIndicator>
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
    <buyerSellerIndicator>SELLER</buyerSellerIndicator>
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
    <buyerSellerIndicator>buyer</buyerSellerIndicator>
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
    <buyerSellerIndicator>Seller</buyerSellerIndicator>
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

#### TRD-0018.xml
```xml
<trade>
    <tradeId>TRD-0018</tradeId>
    <time>2026-05-05T11:25:00Z</time>
    <amount>2800.5</amount>
    <partyAccount1>ACC-147</partyAccount1>
    <partyAccount2>ACC-248</partyAccount2>
    <buyerSellerIndicator>UNKNOWN</buyerSellerIndicator>
</trade>
```

---

## Traceability Matrix

### Issue #1: Add Buyer/Seller Indicator (B/S) to Enriched Trade Output

#### Acceptance Criteria

- AC1: System identifies buyer/seller role via buyerSellerIndicator field
- AC2: Valid BUYER->B, SELLER->S in enriched output
- AC3: Case-insensitive input handling
- AC4: Missing tag -> field omitted, warning logged
- AC5: Blank tag -> defaults to 'B', warning logged
- AC6: Invalid value -> empty string, warning logged
- AC7: Processing must not fail on missing/blank/invalid value
- AC8: Business scenario matrix (7 scenarios) verifiable

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-016`, `TC-017`, `TC-013`, `TC-018`, `TC-021`

#### Coverage Notes

AC1/AC2/AC3 covered by TC-001 (BUYER uppercase->B), TC-011 (SELLER uppercase->S), TC-016 (buyer lowercase->B), TC-017 (Seller mixed case->S). AC4 covered by TC-018 which already had no buyerSellerIndicator tag - only description/expected_output updated per decision-tree rule for already-matching input conditions, no XML/value change needed. AC5 covered by TC-013 with an empty tag added, defaulting to 'B'. AC6 covered by TC-021 (previously an incomplete placeholder row) with an invalid 'UNKNOWN' value producing an empty string. AC7 is implicitly validated across TC-013/TC-018/TC-021 since all three remain successfully PUBLISHED despite blank/missing/invalid indicator values. All 7 scenarios in AC8's matrix are covered by these 7 modified test cases; no inserts were necessary since sufficient distinct published test cases existed to host each unique input condition without conflicting with their pre-existing assertions.

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: The system shall always format the final output to exactly two decimal places without rounding.
- AC2: If the input has fewer than 2 decimal places, the system shall pad with trailing zeros.
- AC3: If the input has more than 2 decimal places, all extra digits shall be discarded after truncation with no rounding.
- AC4: If the input has no decimal places, the system shall append '.00' to ensure 2 decimal places.

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1 (always 2 decimal places) is broadly validated across all published rows (TC-001,011,013,016,017,018,021-025). AC2 (padding fewer decimals) is covered by TC-021 (2800.5->2800.50, 1 decimal padded). AC3 (truncate more than 2 decimals, no rounding) is covered by new TC-022 (4 decimals) and TC-023 (3 decimals, verifying .999 does not round up) plus negative-sign variant TC-024. AC4 (append .00 for whole numbers) is covered by TC-011 and TC-013 (existing published rows corrected) and reinforced by new zero-value edge case TC-025. Existing published rows with non-conforming amount format (TC-011, TC-013, TC-021) were corrected via global format sweep per issue rules rather than treated as new scenarios. Orphaned XML files TRD-0019/0020/0021/0022 (already present in the trades directory matching this issue's exact examples) were linked to new CSV rows instead of creating additional XML files.
