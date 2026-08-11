# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-08-11 08:49:49 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 4 | 0 |

## Analysis Summary

Retained all changes that introduce genuinely new testing conditions. From Issue #1, all 7 modified scenarios (TC-001, TC-011, TC-016, TC-017, TC-018, TC-021, TC-013) are kept because their descriptions changed from the original CSV state to explicitly test new buyerSellerIndicator business logic (valid BUYER/SELLER conversion, case-insensitivity, missing tag, blank tag defaulting, and invalid value handling) that did not exist in the original test descriptions. From Issue #2, the three global format-sweep modifies to TC-011, TC-013, and TC-021 were REMOVED because their descriptions are identical to the descriptions already established by the Issue #1 modifies to the same scenario_ids — these changes only corrected the amount field's decimal formatting to comply with the new truncation/padding rule and did not alter the underlying condition being tested (which remains the buyerSellerIndicator scenario). All 4 inserted scenarios (TC-022, TC-023, TC-024, TC-025) are kept since they are brand new scenario_ids covering previously untested amount-truncation conditions (>2 decimals, 3 decimals, negative amount sign preservation, and zero/integer amount padding) that did not exist in the original regression pack.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | Existing valid, published trade case reused to cover AC2/AC3 (valid BUYER uppercase converted to abbreviated 'B'). XML modified to add buyerSellerIndicator=BUYER; no conflict with existing amount/account assertions. |
| MODIFY | TC-011 | #1 | Existing valid, published trade case reused to cover AC2/AC3 (valid SELLER uppercase converted to abbreviated 'S'). XML modified to add buyerSellerIndicator=SELLER. |
| MODIFY | TC-016 | #1 | Existing valid, published trade case reused to cover AC3 (case-insensitive lowercase 'buyer' converted to abbreviated 'B'). XML modified to add buyerSellerIndicator=buyer. |
| MODIFY | TC-017 | #1 | Existing valid, published trade case reused to cover AC3 (case-insensitive mixed-case 'Seller' converted to abbreviated 'S'). XML modified to add buyerSellerIndicator=Seller. |
| MODIFY | TC-018 | #1 | Existing valid, published trade case with no buyerSellerIndicator tag already satisfies AC4 (tag missing entirely -> field omitted, backward compatible). No XML change needed - description and expected_output updated to explicitly assert this coverage. |
| MODIFY | TC-021 | #1 | This row was previously incomplete (blank expected_output) and already references TRD-0018. Repurposed to cover AC5 (tag present but blank -> defaults to 'B' with warning). XML modified to add an empty buyerSellerIndicator tag. |
| MODIFY | TC-013 | #1 | Existing valid, published trade case (consumer recovery scenario) reused to cover AC6 (tag present with invalid value -> empty string in output). XML modified to add buyerSellerIndicator=UNKNOWN; does not conflict with existing consumer-recovery assertion. |
| INSERT | TC-022 | #2 | No existing CSV row tests an amount with more than 2 decimal places on a published trade (AC1/AC3). The XML file TRD-0019.xml (amount=15000.9876) already exists in the trades directory but has no corresponding CSV row - checked all existing rows (TC-001 through TC-021) and none reference TRD-0019 or use a >2-decimal amount on a successfully enriched trade. Reused the existing XML rather than modifying another row since it represents a genuinely distinct input condition tied to its own trade_id. |
| INSERT | TC-023 | #2 | No existing CSV row tests an amount with exactly 3 decimal places on a published trade (AC1/AC3 truncate-only scenario). The XML file TRD-0020.xml (amount=125.999) already exists but has no CSV row - checked all existing rows and confirmed none use this trade_id or amount pattern. Reused the existing XML since it is a distinct trade_id/input condition. |
| INSERT | TC-024 | #2 | No existing CSV row tests a negative amount on a published trade, needed to verify sign preservation during truncation (functional context rule from issue #2). The XML file TRD-0021.xml (amount=-1234.5678) already exists but has no CSV row - checked all existing rows and none reference negative amounts. Reused existing XML for this distinct trade_id/condition. |
| INSERT | TC-025 | #2 | No existing CSV row tests a zero/integer amount with no decimal places at all combined with an otherwise-standard published trade to verify the '.00' append rule (AC4) distinctly from TC-011/TC-013 which use non-zero integers. The XML file TRD-0022.xml (amount=0) already exists but has no CSV row - checked all rows and confirmed none reference TRD-0022 or a literal zero amount. Reused existing XML for this distinct edge-case input. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount and valid buyerSellerIndicator BUYER (uppercase) converted to abbreviated B in enriched output
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator field set to B (converted from BUYER)

#### TC-011 — modify
- **scenario_id:** TC-011
- **description:** Published message contains all mandatory fields in correct structure; buyerSellerIndicator SELLER (uppercase) converted to abbreviated S
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
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields and buyerSellerIndicator field set to S (converted from SELLER)

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value; buyerSellerIndicator lowercase 'buyer' converted to abbreviated B (case-insensitive handling)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator field set to B (converted from lowercase buyer)

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount; buyerSellerIndicator mixed-case 'Seller' converted to abbreviated S (case-insensitive handling)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator field set to S (converted from mixed-case Seller)

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; buyerSellerIndicator tag missing entirely from input - field omitted from enriched output for backward compatibility (warning logged)
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
- **expected_output:** PUBLISHED - amount field in trade-log-topic message equals 1250.75 unchanged; buyerSellerIndicator tag absent from input so field is omitted entirely from output

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field present but blank/empty in XML - defaults to abbreviated B in enriched output with warning logged (verifies string type field default handling)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details and buyerSellerIndicator field defaulted to B due to blank input value

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; buyerSellerIndicator contains invalid value UNKNOWN resulting in empty string in enriched output with warning logged
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
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator field set to empty string due to invalid input value UNKNOWN

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Valid trade with amount containing 4 decimal places - truncated to 2 decimals without rounding (15000.9876 -> 15000.98); buyerSellerIndicator tag absent from input so field omitted from output
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 15000.9876 to 15000.98 (truncation, no rounding, exactly 2 decimal places); buyerSellerIndicator omitted since tag absent from input

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Valid trade with amount containing 3 decimal places - truncated to 2 decimals without rounding (125.999 -> 125.99); buyerSellerIndicator tag absent from input so field omitted from output
- **trade_id:** TRD-0020
- **tradeId:** TRD-0020
- **time:** 2026-05-05T11:35:00Z
- **amount:** 125.99
- **partyAccount1:** ACC-151
- **partyAccount2:** ACC-252
- **partyAccount1_accountNumber:** ACC-151
- **partyAccount1_holderName:** Karan Malhotra
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-252
- **partyAccount2_holderName:** Priya Nair
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 125.999 to 125.99 (truncation only, no rounding); buyerSellerIndicator omitted since tag absent from input

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Valid trade with negative amount containing 4 decimal places - truncated to 2 decimals with sign preserved (-1234.5678 -> -1234.56); buyerSellerIndicator tag absent from input so field omitted from output
- **trade_id:** TRD-0021
- **tradeId:** TRD-0021
- **time:** 2026-05-05T11:40:00Z
- **amount:** -1234.56
- **partyAccount1:** ACC-153
- **partyAccount2:** ACC-254
- **partyAccount1_accountNumber:** ACC-153
- **partyAccount1_holderName:** Vikram Singh
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-254
- **partyAccount2_holderName:** Ananya Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; negative amount truncated from -1234.5678 to -1234.56 with sign preserved (no rounding); buyerSellerIndicator omitted since tag absent from input

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Valid trade with zero amount and no decimal places - formatted with trailing zeros to 0.00; buyerSellerIndicator tag absent from input so field omitted from output
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Arjun Nair
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Neha Joshi
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; zero amount with no decimal places formatted with appended .00 (0 -> 0.00); buyerSellerIndicator omitted since tag absent from input

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0001.xml | Add buyerSellerIndicator=BUYER (uppercase) to test AC2/AC3 valid conversion to 'B'. |
| MODIFY | TRD-0009.xml | Add buyerSellerIndicator=SELLER (uppercase) to test AC2/AC3 valid conversion to 'S'. |
| MODIFY | TRD-0014.xml | Add buyerSellerIndicator=buyer (lowercase) to test AC3 case-insensitivity conversion to 'B'. |
| MODIFY | TRD-0015.xml | Add buyerSellerIndicator=Seller (mixed case) to test AC3 case-insensitivity conversion to 'S'. |
| MODIFY | TRD-0018.xml | Add empty buyerSellerIndicator tag to test AC5 (blank tag defaults to 'B'). |
| MODIFY | TRD-0011.xml | Add buyerSellerIndicator=UNKNOWN to test AC6 (invalid value results in empty string). |

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

#### TRD-0018.xml
```xml
<trade>
    <tradeId>TRD-0018</tradeId>
    <time>2026-05-05T11:25:00Z</time>
    <amount>2800.5</amount>
    <partyAccount1>ACC-147</partyAccount1>
    <partyAccount2>ACC-248</partyAccount2>
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

- AC1: identify buyer/seller role via buyerSellerIndicator field
- AC2: valid indicator converts BUYER->B, SELLER->S
- AC3: case-insensitive handling
- AC4: missing tag -> field omitted, warning logged
- AC5: blank tag -> defaults to 'B', warning logged
- AC6: invalid value -> empty string, warning logged
- AC7: processing must not fail due to missing/blank/invalid value
- AC8: business scenario matrix (7 scenarios)

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-016`, `TC-017`, `TC-018`, `TC-021`, `TC-013`

#### Coverage Notes

AC1/AC2/AC3 covered by TC-001 (BUYER uppercase->B), TC-011 (SELLER uppercase->S), TC-016 (lowercase buyer->B), TC-017 (mixed-case Seller->S). AC4 covered by TC-018 which already had no buyerSellerIndicator tag (backward-compatible default state) - only description/expected_output updated, no XML change needed. AC5 covered by TC-021 (previously incomplete row) with blank tag added to TRD-0018, defaulting to 'B'. AC6 covered by TC-013 with invalid value UNKNOWN added to TRD-0011, resulting in empty string. AC7 is implicitly validated since all these trades still reach PUBLISHED state despite missing/blank/invalid indicator values. All ACs satisfied via MODIFY actions on existing published-trade scenarios; no new XML files or scenario_ids were required.

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: The system shall always format the final output to exactly two decimal places without rounding.
- AC2: If the input has fewer than 2 decimal places, the system shall pad with trailing zeros.
- AC3: If the input has more than 2 decimal places, all extra digits shall be discarded after truncation with no rounding.
- AC4: If the input has no decimal places, the system shall append .00 to ensure 2 decimal places.

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1 (always 2 decimals) is validated across all published rows (TC-001, TC-016, TC-017, TC-018 already conform; no change needed). AC2 (pad trailing zeros) is covered by corrected TC-021 (2800.5 -> 2800.50). AC4 (append .00 for integers) is covered by corrected TC-011 (1100 -> 1100.00) and TC-013 (900 -> 900.00), and new TC-025 (0 -> 0.00) for the zero-amount edge case with sign/format distinctness. AC3 (truncate extra decimals, no rounding) is covered by new TC-022 (15000.9876 -> 15000.98, 4 decimals) and TC-023 (125.999 -> 125.99, 3 decimals). Sign preservation for negative amounts (an implicit extension of AC1/AC3 per accumulated functional context) is covered by new TC-024 (-1234.5678 -> -1234.56). Existing orphaned XML files (TRD-0019 to TRD-0022) were reused via INSERT since no existing CSV row referenced them and their input conditions (multi-decimal, negative, zero amounts) were not present in any other test case.
