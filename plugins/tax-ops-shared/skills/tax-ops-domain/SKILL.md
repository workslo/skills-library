---
name: tax-ops-domain
description: Prime brokerage tax-ops domain reference covering break taxonomy, routing rules, tax-form mappings, and the three-test framework that other skills pull from.
# skills-library metadata (ignored by Claude Code)
type: skill
stage: research
tier: 1
source: "skills-library .claude/skills/tax-ops-domain.md"
---

# Tax-ops domain knowledge

This is the domain content that turns a generic skill into a role-specific one. When a content entry carries a bracketed insert (for example `[INSERT: cause taxonomy]`), the text comes from here. Confirm box numbers, income codes, and rates against the current-year IRS instructions and the firm's tax guidance each filing season. Codes and thresholds change.

## Break-cause taxonomy

A break is a reconciliation discrepancy between the client back-office transaction log and an authoritative reference (custodian, depository, the tax engine, or a client statement). Classify every break into one category before proposing a fix. When the cause is unclear, mark it unclassified rather than guess.

Use one primary cause. Add a secondary cause only when it changes the remediation path. If the analyst corrects the classification, record the original cause, corrected cause, evidence, and final value. Repeated corrections are the signal for improving this taxonomy.

**1. Timing and settlement-date straddle.** A transaction lands in different periods across the two sources because trade date and settle date fall on opposite sides of a cutoff. Signature: the same trade appears in both with different dates, or in one period and not the other. Origin: T versus T+1 or T+2 conventions, period-end cutoff, feed lag.

**2. Quantity and share mismatch.** Share or par amounts differ on otherwise matched records. Signature: same instrument and date, different quantity. Origin: partial fills aggregated differently, a corporate-action share adjustment posted to one source only, fractional-share handling.

**3. Price and amount difference.** Cash amounts differ when quantity matches. Signature: same quantity, different gross. Origin: dirty versus clean price, accrued interest treatment, FX rate or rate date, rounding, fees netted in one source and not the other.

**4. Corporate action processing.** A dividend, split, merger, spin-off, or return of capital is booked late, mis-booked, or absent. Signature: an event-driven entry in one source with no counterpart, or a quantity or basis change that traces to an event. Origin: event captured late, wrong ratio, wrong record or pay date, return of capital booked as an ordinary dividend.

**5. Income classification.** The amount ties but the income type is wrong. Signature: gross matches, `income_type` differs (qualified versus nonqualified dividend, ordinary versus capital, dividend versus return of capital, payment in lieu). Origin: the holding-period test for qualified status, substitute payments on loaned securities, issuer reclassification.

**6. Cost-basis and tax-lot error.** Basis, lot relief, or holding period is wrong. Signature: gain or loss differs on a matched sale, or basis is absent on a transfer-in. Origin: a wash-sale adjustment missing or miscomputed, a lot relief method mismatch (FIFO versus specific identification), basis not stepped for a corporate action, transferred-lot basis not received on a broker-to-broker transfer.

**7. Withholding error.** Tax withheld differs or is missing. Signature: gross matches, withholding differs. Origin: wrong NRA rate, a treaty rate applied without a valid claim or a valid claim not applied, backup withholding triggered or skipped, chapter 4 (FATCA) withholding, deliberate over- or under-withholding pending a later correction.

**8. Account and static-data error.** The break traces to account-level reference data, so a whole class of transactions breaks the same way. Signature: every transaction for one account breaks identically. Origin: stale tax status, a missing or expired W-8 or W-9, wrong treaty country or residency, wrong FATCA classification, wrong default lot-relief method on the account.

**9. Missing or duplicate transaction.** A record exists in one source only, or twice. Signature: an orphan record, or two identical entries. Origin: a dropped or failed feed, a double-booking, a reversal not paired with its original.

**10. Identifier and security-master mismatch.** The same security carries different identifiers across sources. Signature: economic terms match, CUSIP, ISIN, or SEDOL differ. Origin: a stale security master, an identifier change after a corporate action, a vendor mapping gap.

**11. Reclass, amendment, or prior-period carryover.** A post-period issuer reclassification changes prior reporting, or the current break is explained by a prior correction. Signature: a prior-period figure moves after close, or the same unresolved discrepancy carries forward. Origin: an issuer reclass (common for RICs and REITs), a late corrected income statement, an amended tax document, or carryforward from an earlier unresolved break. This is corrected-form territory; assume a 1099 correction may follow.

**12. Source parsing and extraction error.** A value was read incorrectly from a log, statement, tax engine output, or screenshot. Signature: the authoritative source shows one value, but the normalized table carries another. Origin: OCR error, column shift, sign convention, split description field, truncated export, or inferred value treated as source fact.

**13. Tax reporting mapping error.** The source value is right, but the reporting destination is wrong. Signature: income type, recipient classification, form, box, income code, chapter, exemption code, or withholding treatment does not match the account facts. Origin: wrong income-type-to-form mapping, stale recipient classification, missing treaty basis, or form logic applied to the wrong account regime.

**14. Workflow coverage gap or analyst judgment call.** The records tie mechanically, but the treatment depends on a policy call or no approved path covers the case. Signature: documentation quality, materiality, client communication risk, correction threshold, or desk convention determines the answer. Origin: edge case, absent procedure, conflicting guidance, or judgment reserved to the analyst.

## Remediation routing rules

Pick the path with the smallest blast radius that does the job. These are desk conventions; confirm each against the firm's change-control policy before a write. Read before you write, every time.

Work the decision in order and stop at the first match:

1. **Investigation only, no change yet.** Use a read-only path: a UI view or a read-only query. Never open a write path to look.
2. **One record or a few, field editable in the front end.** Use the **UI**. It logs the change and the audit trail comes for free. First choice for one-offs.
3. **Many records, or a field the UI does not expose, but the system accepts a structured message for the change.** Use an **XML update**. Re-send a corrected transaction or static-data message against the known schema. Use for medium volume that follows a message contract.
4. **The same multi-step correction recurs and a vetted routine exists for it.** Use the **plugin**. Examples: a batch wash-sale recompute, a bulk withholding re-rate. Use when the pattern repeats and the tool is approved.
5. **High volume, back-end only, no UI field, no message path, no plugin.** Use a **write SQL query**, under change control, with sign-off before execution and a tested rollback. Highest blast radius, most controls, last resort.

| Path | Scope | UI exposes the field | Message schema exists | Recurring pattern | Controls |
|---|---|---|---|---|---|
| UI | one to a few | yes | n/a | no | built-in audit log |
| XML | medium | no | yes | sometimes | schema validation, message log |
| Plugin | medium to high | n/a | n/a | yes | tool must be vetted |
| Write SQL | high | no | no | no | change control, sign-off, rollback |

Two standing rules. A read query needs no sign-off; a write query always does. A correction that touches more than one account through static data is an account-level fix (taxonomy category 8), so fix the static data once rather than patching each transaction.

## Income-type to tax-form mappings

Map every reportable item to its form before you reconcile withholding or basis. US-person reporting is the 1099 series; foreign-person reporting is 1042-S. Account documentation decides which regime applies.

| Item or event | Recipient | Form | Key fields |
|---|---|---|---|
| Corporate dividend, RIC or mutual fund distribution, REIT distribution | US person | 1099-DIV | 1a ordinary, 1b qualified, 2a capital gain distribution, 3 nondividend distribution (return of capital), 5 section 199A, 7 foreign tax paid |
| Sale, redemption, or closing of a security | US person | 1099-B | proceeds, cost basis, wash-sale loss disallowed, short or long term, covered versus noncovered |
| Interest | US person | 1099-INT | interest income, early-withdrawal penalty, federal tax withheld |
| Original issue discount | US person | 1099-OID | OID, other periodic interest |
| Substitute payment in lieu of a dividend | US person | 1099-MISC | box 8, substitute payments in lieu of dividends or interest |
| US-source dividend, interest, or other FDAP | Foreign person (NRA) | 1042-S | income code, gross income, withholding rate, chapter 3 versus chapter 4, exemption code, recipient country |

1042-S income codes seen most on the desk: 06 dividends, 01 interest, 23 other income. Use the exemption code when a treaty reduces or removes withholding.

Verified 2026-06-18 against current IRS instructions: substitute payments in lieu of dividends or interest are reported in 1099-MISC Box 8, not other income (Instructions for Forms 1099-MISC and 1099-NEC, Rev. 04/2025, https://www.irs.gov/instructions/i1099mec); 1042-S "other income" is income code 23, while code 51 is interest on certain actively traded or publicly offered securities (2026 Instructions for Form 1042-S, https://www.irs.gov/instructions/i1042s).

### Account classification drives reporting and withholding

- **US person with a valid W-9.** Report on the 1099 series. Apply backup withholding at 24% only on a B-notice or a missing or incorrect TIN.
- **Foreign person with a valid W-8BEN (individual) or W-8BEN-E (entity).** Report on 1042-S. Apply NRA withholding at 30% on US-source FDAP by default. Reduce to a treaty rate only with a valid treaty claim: correct article, correct rate, correct country of residence, and a US or foreign TIN where required.
- **No valid documentation.** Apply the presumption rules. A presumed foreign payee on FDAP defaults to 30% NRA; a presumed US payee defaults to backup withholding.
- **FATCA, chapter 4.** Classify entity accounts as FFI or NFFE (active or passive). An undocumented entity or a recalcitrant account holder takes 30% chapter 4 withholding on withholdable payments. Documentation drives the classification, so a withholding break often traces to a documentation gap.
- **CRS.** Residence-based reporting to partner jurisdictions, driven by self-certification of tax residence. No withholding, reporting only. A CRS gap is a documentation and classification problem, never a withholding one.

When a withholding break (taxonomy category 7) and a documentation gap (category 8) both appear, fix the documentation first. The withholding follows from the classification.

## Three-test asset framework

Run every candidate asset through three tests before it earns a place in the library. An asset that cannot pass all three visibly is not ready.

1. **Understand it.** Read the prompt or procedure end to end. If the steps are not legible to you, you cannot defend the output, and it does not ship.
2. **Decompose it.** Strip the asset to its core function, the part that names no tool. State that core in one sentence. If the sentence names a database, a runtime, or a connector, keep stripping. If you cannot rebuild the core from scratch, even imperfectly, you do not own it yet.
3. **Adapt it.** Pour in the domain knowledge the source could not have: the break taxonomy above, the routing rules above, the form mappings above. Write the `domain_gap` note to say exactly what gets poured in and what changes once it is filled.

The framing behind the tests: treat credible repos as specifications, not software. Harvest the workflow decomposition, drop the code that will not run in the tools at hand, re-express the rest as prompts the available assistant runs. The durable edge is the domain knowledge encoded into the gap the repo cannot fill. A generic reconciliation skill is a commodity. The same skill with the firm's break taxonomy, routing rules, and form mappings inside it is defensible and specific to the desk.
