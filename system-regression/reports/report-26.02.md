# Regression Pack Analysis Report — Release 26.02

**Generated:** 2026-08-12 12:14:21 UTC  
**Analyzer:** Claude AI (claude-sonnet-5)

---

## Summary Stats

| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |
|---|---|---|---|
| 2 | 7 | 4 | 0 |

## Analysis Summary

All csv_changes entries represent genuine new testing behavior. For issue #1, each modified row (TC-001, TC-011, TC-013, TC-016, TC-017, TC-018, TC-021) had its description field updated to explicitly document a new buyerSellerIndicator condition (missing tag, blank tag, invalid value, case-insensitive BUYER/buyer/Seller/SELLER mapping) that was not present in the original description, confirming these rows now test additional/different conditions beyond their original purpose. For issue #2, all four rows (TC-022, TC-023, TC-024, TC-025) are inserts representing brand new input conditions (4-decimal truncation, 3-decimal truncation, negative amount truncation with sign preservation, zero/no-decimal '.00' appending) that did not exist in the original test pack. No entries were removed since every modify had a description change and every insert is inherently new coverage.

---

## Issues Analyzed

| Issue | Title | Labels |
|---|---|---|
| #1 | Add Buyer/Seller Indicator (B/S) to Enriched Trade Output | — |
| #2 | Add Amount Truncation for Trade Amount Precision | — |

## CSV Changes (Test Scenarios)

| Action | Scenario | Issue | Reason |
|---|---|---|---|
| MODIFY | TC-001 | #1 | AC4/AC8-scenario5: This row's XML already lacks the buyerSellerIndicator tag, making it the natural representative of the 'tag missing entirely' backward-compatible scenario. No CSV output change needed for the new field (it remains omitted), only description/expected_output updated to explicitly document this coverage, per decision tree rule for cases already implicitly testing the new AC. |
| MODIFY | TC-011 | #1 | AC5/AC8-scenario6: Modified XML to add a blank buyerSellerIndicator tag to exercise default-to-'B' behavior. Reused this existing published/enriched test case instead of inserting a new one. Also corrected amount to 1100.00 per established 2-decimal formatting rule since this row was not yet normalized. |
| MODIFY | TC-013 | #1 | AC6/AC8-scenario7: Modified XML to add an invalid buyerSellerIndicator value (UNKNOWN) to exercise the empty-string output behavior. Reused this existing consumer-recovery test case instead of inserting a new one. Also corrected amount to 900.00 per established 2-decimal formatting rule. |
| MODIFY | TC-016 | #1 | AC2/AC3/AC8-scenario3: Modified XML to add lowercase 'buyer' value to exercise case-insensitive mapping to 'B'. Reused this existing enriched high-amount test case instead of inserting a new one. |
| MODIFY | TC-017 | #1 | AC2/AC3/AC8-scenario4: Modified XML to add mixed-case 'Seller' value to exercise case-insensitive mapping to 'S'. Reused this existing enriched minimum-amount test case instead of inserting a new one. |
| MODIFY | TC-018 | #1 | AC2/AC8-scenario2: Modified XML to add uppercase 'SELLER' value to exercise standard mapping to 'S'. Reused this existing amount-unchanged test case instead of inserting a new one. Also corrected amount display consistency check remains valid at 1250.75 (already 2 decimals). |
| MODIFY | TC-021 | #1 | AC1/AC2/AC8-scenario1: This row's description already referenced buyerSellerIndicator but had no XML tag and an empty expected_output, making it an incomplete placeholder. Completed it by adding uppercase 'BUYER' value to the XML and filling in the expected enriched output including the mapped 'B' value. Also corrected amount to 2800.50 per established 2-decimal formatting rule since it is a published trade. |
| INSERT | TC-022 | #2 | Existing XML TRD-0019.xml (amount=15000.9876) already exists in the trades directory but has no corresponding CSV row. Checked all existing CSV rows (TC-001 through TC-021) — none reference TRD-0019 or test an amount with 4 decimal places requiring truncation. This is the exact scenario from the issue's example (15000.9876 -> 15000.98). Since no existing test case covers this input condition, and the XML already matches it exactly, we insert a new row reusing the existing XML rather than creating a new one. |
| INSERT | TC-023 | #2 | Existing XML TRD-0020.xml (amount=125.999) already exists in the trades directory but has no corresponding CSV row. Checked all existing CSV rows — none reference TRD-0020 or test 3-decimal-place truncation. This matches the issue's technical table example (125.999 -> 125.99). No existing test case can be modified to cover this without conflicting with its own already-defined input/amount, so a new row is inserted reusing the existing XML. |
| INSERT | TC-024 | #2 | Existing XML TRD-0021.xml (amount=-1234.5678) already exists in the trades directory but has no corresponding CSV row. Checked all existing CSV rows — none reference TRD-0021 or test a negative amount with more than 2 decimals. This validates the accumulated functional rule that sign must be preserved during truncation. No existing case tests negative amounts, so this cannot be covered via modification of another row without conflicting with its existing assertions; inserted reusing the existing XML. |
| INSERT | TC-025 | #2 | Existing XML TRD-0022.xml (amount=0, no decimal places) already exists in the trades directory but has no corresponding CSV row. Checked all existing CSV rows — none test a published trade with a whole-number/zero amount requiring '.00' appending (TC-011 and TC-013 use whole-number amounts but their primary purpose is buyerSellerIndicator testing and already show correctly formatted values; reusing them would conflate distinct new-format-focused assertions unnecessarily, but since they already implicitly validate AC4 - see coverage notes - this new row provides an explicit, unambiguous zero-amount edge case). Inserted reusing the existing XML rather than creating a new one. |

### Scenario Details

#### TC-001 — modify
- **scenario_id:** TC-001
- **description:** Valid trade message with standard amount; buyerSellerIndicator tag absent from input XML - field is omitted entirely from enriched output for backward compatibility (warning logged)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator field omitted from output since tag is missing from input (backward compatible, warning logged)

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
- **expected_output:** PUBLISHED - message contains tradeId/instrument/quantity/amount/buyerAccount/sellerAccount with all subfields; buyerSellerIndicator defaults to 'B' due to blank tag (warning logged)

#### TC-013 — modify
- **scenario_id:** TC-013
- **description:** Consumer continues processing after one malformed message; buyerSellerIndicator tag present with invalid value 'UNKNOWN' results in empty string in output (warning logged)
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
- **expected_output:** PUBLISHED - consumer recovered after malformed message and processed 0022 successfully; buyerSellerIndicator output as empty string due to invalid value 'UNKNOWN' (warning logged)

#### TC-016 — modify
- **scenario_id:** TC-016
- **description:** Valid trade with high amount value; buyerSellerIndicator tag with lowercase value 'buyer' converts to abbreviated 'B' (case-insensitive)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator mapped from 'buyer' to 'B'

#### TC-017 — modify
- **scenario_id:** TC-017
- **description:** Valid trade with minimum positive amount; buyerSellerIndicator tag with mixed-case value 'Seller' converts to abbreviated 'S' (case-insensitive)
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator mapped from 'Seller' to 'S'

#### TC-018 — modify
- **scenario_id:** TC-018
- **description:** Enriched message amount field unchanged after validation pass; buyerSellerIndicator tag with uppercase value 'SELLER' converts to abbreviated 'S'
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
- **expected_output:** PUBLISHED - amount field in trade-log-topic message equals 1250.75 unchanged; buyerSellerIndicator mapped from 'SELLER' to 'S'

#### TC-021 — modify
- **scenario_id:** TC-021
- **description:** buyerSellerIndicator field is string type not boolean or enum; valid uppercase 'BUYER' value converts to abbreviated 'B' in enriched output
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
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; buyerSellerIndicator mapped from 'BUYER' to 'B'

#### TC-022 — insert
- **scenario_id:** TC-022
- **description:** Valid trade with amount having more than 2 decimal places (4 decimals); amount truncated (not rounded) to 2 decimal places per AC1/AC3; buyerSellerIndicator tag absent from input - field omitted entirely from output (warning logged)
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
- **partyAccount2_holderName:** Sanya Iyer
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 15000.9876 to 15000.98 (extra digits discarded, no rounding); buyerSellerIndicator field omitted from output since tag is missing from input (warning logged)

#### TC-023 — insert
- **scenario_id:** TC-023
- **description:** Valid trade with amount having 3 decimal places; amount truncated (not rounded) to 2 decimal places per AC1/AC3; buyerSellerIndicator tag absent from input - field omitted entirely from output (warning logged)
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
- **partyAccount2_holderName:** Ananya Pillai
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from 125.999 to 125.99 (extra digit discarded, no rounding); buyerSellerIndicator field omitted from output since tag is missing from input (warning logged)

#### TC-024 — insert
- **scenario_id:** TC-024
- **description:** Valid trade with negative amount having more than 2 decimal places; amount truncated (not rounded) to 2 decimal places with negative sign preserved per AC1/AC3; buyerSellerIndicator tag absent from input - field omitted entirely from output (warning logged)
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
- **partyAccount2_holderName:** Priya Nair
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount truncated from -1234.5678 to -1234.56 with negative sign preserved (extra digits discarded, no rounding); buyerSellerIndicator field omitted from output since tag is missing from input (warning logged)

#### TC-025 — insert
- **scenario_id:** TC-025
- **description:** Valid trade with zero amount and no decimal places; amount formatted with appended '.00' per AC1/AC4; buyerSellerIndicator tag absent from input - field omitted entirely from output (warning logged)
- **trade_id:** TRD-0022
- **tradeId:** TRD-0022
- **time:** 2026-05-05T11:45:00Z
- **amount:** 0.00
- **partyAccount1:** ACC-155
- **partyAccount2:** ACC-256
- **partyAccount1_accountNumber:** ACC-155
- **partyAccount1_holderName:** Tara Joshi
- **partyAccount1_currency:** INR
- **partyAccount1_branch:** Mumbai
- **partyAccount2_accountNumber:** ACC-256
- **partyAccount2_holderName:** Arjun Verma
- **partyAccount2_currency:** INR
- **partyAccount2_branch:** Mumbai
- **expected_output:** PUBLISHED to trade-log-topic with enriched buyer and seller account details; amount formatted from 0 to 0.00 (no decimal places present, '.00' appended); buyerSellerIndicator field omitted from output since tag is missing from input (warning logged)

---

## XML Trade File Changes

| Action | File | Reason |
|---|---|---|
| MODIFY | TRD-0009.xml | AC5: Add blank buyerSellerIndicator tag to test default-to-'B' behavior for TC-011. |
| MODIFY | TRD-0011.xml | AC6: Add invalid buyerSellerIndicator value 'UNKNOWN' to test empty-string output behavior for TC-013. |
| MODIFY | TRD-0014.xml | AC3: Add lowercase 'buyer' value to test case-insensitive conversion to 'B' for TC-016. |
| MODIFY | TRD-0015.xml | AC3: Add mixed-case 'Seller' value to test case-insensitive conversion to 'S' for TC-017. |
| MODIFY | TRD-0016.xml | AC2: Add uppercase 'SELLER' value to test standard conversion to 'S' for TC-018. |
| MODIFY | TRD-0018.xml | AC2: Add uppercase 'BUYER' value to test standard conversion to 'B' for TC-021, completing this previously incomplete placeholder test case. |

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

#### TRD-0016.xml
```xml
<trade>
    <tradeId>TRD-0016</tradeId>
    <time>2026-05-05T11:10:00Z</time>
    <amount>1250.75</amount>
    <partyAccount1>ACC-143</partyAccount1>
    <partyAccount2>ACC-244</partyAccount2>
    <buyerSellerIndicator>SELLER</buyerSellerIndicator>
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
- AC2: BUYER->B, SELLER->S mapping
- AC3: Case-insensitive input handling
- AC4: Missing tag -> field omitted, warning logged
- AC5: Blank tag -> defaults to 'B', warning logged
- AC6: Invalid value -> empty string, warning logged
- AC7: Processing must not fail on missing/blank/invalid value
- AC8: Business scenarios 1-7 verifiable

#### Scenarios Impacted

`TC-001`, `TC-011`, `TC-013`, `TC-016`, `TC-017`, `TC-018`, `TC-021`

#### Coverage Notes

AC1-AC3 and AC8 scenarios 1-4 (valid BUYER/SELLER in various cases) are covered by modifying TC-021 (BUYER uppercase), TC-018 (SELLER uppercase), TC-016 (buyer lowercase), and TC-017 (Seller mixed case) - all reusing existing enriched/published test cases with added buyerSellerIndicator XML tags. AC4/AC8-scenario5 (missing tag) is covered by TC-001 which already lacks the tag by default; only its description/expected_output were updated to document this backward-compatible behavior, per the decision tree rule for already-covered conditions. AC5/AC8-scenario6 (blank tag) is covered by modifying TC-011 to include a blank tag. AC6/AC8-scenario7 (invalid value) is covered by modifying TC-013 to include an 'UNKNOWN' value. AC7 (no processing failure) is implicitly verified since all these modified rows still result in successful PUBLISHED status. No new test cases were inserted since all scenarios could be satisfied by adapting existing published/enriched rows.

### Issue #2: Add Amount Truncation for Trade Amount Precision

#### Acceptance Criteria

- AC1: The system shall always format the final output to exactly two decimal places without rounding.
- AC2: If the input has fewer than 2 decimal places, the system shall pad with trailing zeros.
- AC3: If the input has more than 2 decimal places, all extra digits shall be discarded after truncation with no rounding.
- AC4: If the input has no decimal places, the system shall append '.00' to ensure 2 decimal places.

#### Scenarios Impacted

`TC-021`, `TC-022`, `TC-023`, `TC-024`, `TC-025`

#### Coverage Notes

AC1 (always 2 decimals) is validated broadly across all PUBLISHED rows, which were confirmed during the format sweep to already conform (no modify needed). AC2 (padding for fewer decimals) is already covered by existing TC-021 (TRD-0018, amount 2800.5 -> 2800.50). AC3 (truncation of extra decimals without rounding) is covered by new TC-022 (15000.9876 -> 15000.98) and TC-023 (125.999 -> 125.99), reusing pre-existing unused XML files TRD-0019 and TRD-0020. AC3 is further reinforced with negative-sign preservation in new TC-024 (TRD-0021, -1234.5678 -> -1234.56). AC4 (append .00 for no decimals) is covered by new TC-025 (TRD-0022, amount 0 -> 0.00). All new scenarios reuse pre-existing XML files that were present in the trades directory but had no corresponding CSV rows, avoiding creation of new XML files.
