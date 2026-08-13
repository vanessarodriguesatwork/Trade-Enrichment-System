# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-08-13 10:54:04 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 4 | 0 |

## Analysis Summary

All csv_changes represent genuine new testing behavior. The 7 modified rows (TC-001, TC-021, TC-016, TC-017, TC-018, TC-011, TC-013) each had their description field updated to explicitly call out new buyerSellerIndicator conditions (tag missing, valid BUYER/SELLER uppercase, lowercase/mixed-case case-insensitivity, blank defaulting to B, invalid value producing empty string) that were not present in the original descriptions, confirming these rows now test additional/different conditions beyond their original intent. The 4 inserted rows (TC-022, TC-023, TC-024, TC-025) are brand new scenarios covering amount truncation without rounding (>2 decimal places), negative-amount sign preservation combined with truncation, and the zero-amount boundary case for padding - none of which existed in the original regression pack. All entries are retained as genuine new coverage.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | TRD-0001.xml already lacks a buyerSellerIndicator tag, making it the ideal existing case to cover AC4/AC8-scenario5 (tag missing entirely -> field omitted, warning logged). Updated description and expected_output to reflect this without any XML change. |
| MODIFY | TC-021 | #1 | Existing TC-021/TRD-0018 was an incomplete placeholder row already themed around buyerSellerIndicator field type. Modified to cover AC1-AC3/AC8-scenario1: valid BUYER (uppercase) converted to 'B'. Also corrected amount to comply with existing 2-decimal formatting rule since the row was already being edited. |
| MODIFY | TC-016 | #1 | TRD-0014 is an existing valid/published high-amount trade. Modified to additionally cover AC2/AC8-scenario2: valid SELLER (uppercase) converted to 'S', without conflicting with its original high-amount assertion. |
| MODIFY | TC-017 | #1 | TRD-0015 is an existing valid/published minimum-amount trade. Modified to additionally cover AC3/AC8-scenario3: valid lowercase 'buyer' converted to 'B' (case-insensitivity), without conflicting with its original min-amount assertion. |
| MODIFY | TC-018 | #1 | TRD-0016 is an existing valid/published trade used to assert amount unchanged. Modified to additionally cover AC3/AC8-scenario4: valid mixed-case 'Seller' converted to 'S', without conflicting with the amount-unchanged assertion. |
| MODIFY | TC-011 | #1 | TRD-0009 is an existing valid/published trade asserting mandatory field structure. Modified to additionally cover AC5/AC8-scenario6: blank buyerSellerIndicator tag defaults to 'B' with warning logged. Amount corrected to 2-decimal format per existing formatting rule since row was already being edited. |
| MODIFY | TC-013 | #1 | TRD-0011 is an existing valid/published trade asserting consumer recovery after a malformed message. Modified to additionally cover AC6/AC8-scenario7: invalid buyerSellerIndicator value results in empty string with warning logged. Amount corrected to 2-decimal format since row was already being edited. |
| INSERT | TC-022 | #2 | No existing CSV row exercises truncation of an amount with more than 2 decimal places (AC3). Checked all existing published rows (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021) - all have amounts with <=2 decimal places already. The orphan XML file TRD-0019.xml (amount=15000.9876) already exists specifically for this purpose but had no corresponding CSV row. Reusing this existing XML file to insert a new scenario testing truncation without rounding. |
| INSERT | TC-023 | #2 | No existing CSV row tests truncation of an amount with exactly 3 decimal places (AC3, 125.999 example from issue). The orphan XML file TRD-0020.xml (amount=125.999) already exists for this purpose but was not referenced by any CSV row. Reusing this existing XML file to insert a new scenario. |
| INSERT | TC-024 | #2 | No existing CSV row tests a negative amount with more than 2 decimal places to verify sign preservation combined with truncation. The orphan XML file TRD-0021.xml (amount=-1234.5678) already exists for this purpose but was not referenced by any CSV row. Reusing this existing XML file to insert a new scenario covering the negative-amount sign-preservation rule together with AC3. |
| INSERT | TC-025 | #2 | While integer-amount padding (AC4) is already covered by TC-011 (amount=1100) and TC-013 (amount=900), the boundary value amount=0 is not explicitly tested. The orphan XML file TRD-0022.xml (amount=0) already exists but was not referenced by any CSV row. Reusing this existing XML file to insert a scenario explicitly covering the zero-amount boundary case for AC4. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount and buyerSellerIndicator tag missing entirely from input - field omitted from enriched output for backward compatibility (warning logged)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator field omitted entirely since tag missing from input XML (warning logged)

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** Valid trade with buyerSellerIndicator=BUYER (uppercase) provided in input - converted to abbreviated 'B' in enriched output
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator=B

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value and buyerSellerIndicator=SELLER (uppercase) provided - converted to abbreviated 'S' in enriched output
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator=S

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount and buyerSellerIndicator=buyer (lowercase) - case-insensitive conversion to 'B'
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator=B

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; buyerSellerIndicator=Seller (mixed case) - case-insensitive conversion to 'S'
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

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure; buyerSellerIndicator tag present but blank - defaults to 'B' (warning logged)
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
- **buyerSellerIndicator:** B
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields; buyerSellerIndicator defaults to B since tag present but blank (warning logged)

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; buyerSellerIndicator tag present with invalid value UNKNOWN - results in empty string output (warning logged)
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
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator is empty string since invalid value UNKNOWN provided (warning logged)

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Valid trade with amount having 4 decimal places (15000.9876) - truncated to 2 decimals without rounding (15000.98) in enriched output; buyerSellerIndicator tag missing entirely from input - field omitted (warning logged)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated to 15000.98 from input 15000.9876 (extra digits discarded, no rounding); buyerSellerIndicator field omitted entirely since tag missing from input XML (warning logged)

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Valid trade with amount having 3 decimal places (125.999) - truncated to 2 decimals without rounding (125.99) in enriched output; buyerSellerIndicator tag missing entirely from input - field omitted (warning logged)
- **trade_id:** TRD-0020
- **tradeId:** TRD-0020
- **time:** 2026-05-05T11:35:00Z
- **amount:** 125.99
- **partyAccount1:** ACC-151
- **partyAccount2:** ACC-252
- **partyAccount1_accountNumber:** ACC-151
- **partyAccount1_holderName:** Karan Malhotra
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Delhi
- **partyAccount2_accountNumber:** ACC-252
- **partyAccount2_holderName:** Priya Nair
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Delhi
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated to 125.99 from input 125.999 (extra digit discarded, no rounding); buyerSellerIndicator field omitted entirely since tag missing from input XML (warning logged)

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Valid trade with negative amount having 4 decimal places (-1234.5678) - truncated to 2 decimals without rounding with sign preserved (-1234.56) in enriched output; buyerSellerIndicator tag missing entirely from input - field omitted (warning logged)
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Arjun Rao
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Chennai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Neha Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Chennai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated to -1234.56 from input -1234.5678 (extra digits discarded, no rounding, negative sign preserved); buyerSellerIndicator field omitted entirely since tag missing from input XML (warning logged)

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Valid trade with zero amount value (boundary case, no decimal places) - formatted with .00 appended (0.00) in enriched output; buyerSellerIndicator tag missing entirely from input - field omitted (warning logged)
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Vikram Joshi
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Pune
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Ananya Bhat
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Pune
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount formatted as 0.00 since input has no decimal places (.00 appended); buyerSellerIndicator field omitted entirely since tag missing from input XML (warning logged)

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0018.xml | Add buyerSellerIndicator=BUYER (uppercase) to test AC1-AC3/AC8-scenario1 valid conversion to 'B'. |
| MODIFY | TRD-0014.xml | Add buyerSellerIndicator=SELLER (uppercase) to test AC8-scenario2 valid conversion to 'S'. |
| MODIFY | TRD-0015.xml | Add buyerSellerIndicator=buyer (lowercase) to test AC3/AC8-scenario3 case-insensitivity conversion to 'B'. |
| MODIFY | TRD-0016.xml | Add buyerSellerIndicator=Seller (mixed case) to test AC3/AC8-scenario4 case-insensitivity conversion to 'S'. |
| MODIFY | TRD-0009.xml | Add blank buyerSellerIndicator tag to test AC5/AC8-scenario6 default to 'B' with warning logged. |
| MODIFY | TRD-0011.xml | Add invalid buyerSellerIndicator=UNKNOWN to test AC6/AC8-scenario7 empty string output with warning logged. |

### XML File Contents

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

---

## Traceability Matrix

### Issue #1: Add Buyer/Seller Indicator (B/S) to Enriched Trade Output

#### Acceptance Criteria

- AC1: Identify buyer/seller role from buyerSellerIndicator field
- AC2: Valid values map BUYER->B, SELLER->S
- AC3: Case-insensitive handling
- AC4: Missing tag -> field omitted, warning logged
- AC5: Blank tag -> defaults to B, warning logged
- AC6: Invalid value -> empty string, warning logged
- AC7: Processing must not fail on missing/blank/invalid value
- AC8: All 7 business scenarios verifiable

#### Scenarios Impacted

`TC-001`, `TC-021`, `TC-016`, `TC-017`, `TC-018`, `TC-011`, `TC-013`

#### Coverage Notes

All 7 AC8 scenarios and AC1-AC7 are covered by modifying existing published/enriched test cases rather than inserting new ones, per prioritization rules. TC-001 (tag missing) required no XML change since the condition already existed. TC-021, TC-016, TC-017, TC-018 cover the four valid case variations (BUYER, SELLER, buyer, Seller). TC-011 covers blank tag defaulting to B. TC-013 covers invalid value resulting in empty string. All modified trades continue to be PUBLISHED, confirming AC7 (no processing failure).

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: Final output always formatted to exactly two decimal places without rounding
- AC2: Fewer than 2 decimal places input padded with trailing zeros
- AC3: More than 2 decimal places input truncated (no rounding)
- AC4: No decimal places input gets .00 appended

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1/AC2/AC4 were already fully covered by existing published rows: TC-011 and TC-013 cover integer amounts (no decimals -> .00), TC-021 covers single-decimal padding (2800.5 -> 2800.50), and TC-001/TC-016/TC-017/TC-018 confirm 2-decimal amounts pass through unchanged. A global sweep of all existing rows confirmed no corrections were needed since amounts already conformed to the format. AC3 (truncation without rounding for >2 decimals) and sign preservation for negative amounts were NOT covered by any existing scenario, so new CSV rows (TC-022, TC-023, TC-024) were inserted reusing pre-existing orphan XML files (TRD-0019, TRD-0020, TRD-0021) that were already present in the trades directory but unreferenced by any CSV row. TC-025 was added to explicitly cover the zero-amount boundary case reusing TRD-0022.xml.
