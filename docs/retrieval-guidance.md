# Retrieval guidance: M365 Copilot and SharePoint agent grounding

Settles SLO-102 and SLO-109. Verified 2026-06-18 against current Microsoft documentation.

The corpus design referenced "Microsoft's retrieval guidance" with no citation. For a GS compliance context that is not a citation to build on. This note records which build-shaping claims are confirmed against live Microsoft docs, which are not, and what that means for the corpus.

## BLUF

Four of the five claims hold. The "restate tables as bullets" advice is not documented by Microsoft and must be labeled an internal heuristic, not vendor guidance. Numeric limits are thinner than the design assumed: the only figures to rely on are the 512 MB index ceiling and the roughly 3,000-word-per-rich-text-block guidance for SharePoint page content.

## Claim verdicts

### 1. SharePoint agents ground on libraries, folders, and files, not on Lists. Confirmed.

> "Currently, you can include up to 20 source items as the knowledge source of an agent. These source items can be sites, document libraries, folders and files."
> "Agents currently don't use data from Lists. Also, you can't add pages from the Site Pages library as source for an agent."

Source: https://support.microsoft.com/en-us/office/frequently-asked-questions-about-copilot-in-sharepoint-eb1b7668-3d98-4a93-98ef-f0c6dfc694f0

### 2. Small, lightly formatted files retrieve better, with concrete size limits. Partially confirmed.

Confirmed: a 512 MB index ceiling, guidance to split long or complex files, and a roughly 3,000-word recommendation per SharePoint rich-text block. LLM position bias is documented. The granular per-task word counts often cited elsewhere could not be verified verbatim on the current pages.

> "Files up to 512 MB are now supported for PDF, PPTX, and DOCX extensions." (Semantic index, ms.date 2026-04-23)
> "If you have a very long document, large PDF, or spreadsheet with many formulas, consider splitting it into smaller documents and providing them to Copilot separately."
> "SharePoint rich text editor has a high word limit (around 30,000 words in English), but Copilot currently has a lower word processing limit... we recommend keeping the total word count in each rich text editor to less than 3,000 words."
> "Large language models (LLMs) tend to prioritize content that is at the beginning and end of a file."

Sources: https://learn.microsoft.com/en-us/microsoftsearch/semantic-index-for-copilot ; https://support.microsoft.com/en-us/microsoft-365-copilot/file-formats-supported-by-microsoft-365-copilot ; https://support.microsoft.com/en-us/office/frequently-asked-questions-about-copilot-in-sharepoint-eb1b7668-3d98-4a93-98ef-f0c6dfc694f0 ; https://support.microsoft.com/en-us/topic/keep-it-short-and-sweet-a-guide-on-the-length-of-documents-that-you-provide-to-copilot-66de2ffd-deb2-4f0c-8984-098316104389

### 3. Copilot struggles with tables and dense formatting; restate tables as bullets. Not confirmed.

No current first-party Microsoft page states that Copilot struggles with tables, and none gives the "restate tables as bullets" advice for grounded source content. The nearest documented guidance addresses length and complexity generically (split long or formula-heavy files), not table formatting. Treat the table advice as an internal practitioner heuristic, not Microsoft guidance.

### 4. Copilot respects existing M365 permissions; oversharing posture. Confirmed.

> "Microsoft 365 Copilot only surfaces organizational data to which individual users have at least view permissions."
> "Semantic Index honors the user identity-based access boundary so that the grounding process only accesses content that the current user is authorized to access."
> "If you don't have permission to specific content, even if this content is included in the agent's sources, you will not see information from this content in your chat with the agent."

Microsoft's documented posture: Copilot makes pre-existing oversharing more visible, so admins remediate with SharePoint Advanced Management (Restricted Content Discovery, Restricted Access Control) and Microsoft Purview (DLP for Copilot, sensitivity labels).

Sources: https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-privacy ; https://learn.microsoft.com/en-us/microsoftsearch/semantic-index-for-copilot ; https://learn.microsoft.com/en-us/microsoft-365/copilot/configure-secure-governed-data-foundation-microsoft-365-copilot

### 5. Indexing freshness and latency. Confirmed.

> "New documents that are added to SharePoint Online sites that are accessible, via site inheritance, by two or more users are indexed daily. When an indexed user and tenant level document is updated, the changes are immediately indexed."

Source: https://learn.microsoft.com/en-us/microsoftsearch/semantic-index-for-copilot

## Implications for the corpus

- Structure the corpus as document libraries, not Lists. Agents ground on sites, libraries, folders, and files and ignore Lists and Site Pages, capped at 20 source items per agent.
- Keep each file well under the 512 MB index ceiling and split long or complex files. Front-load the key facts, since models weight the beginning and end of a file.
- Treat permissions as the security boundary. Right-size access before grounding, because Copilot will surface anything a user is already over-permissioned to see.
- "Refresh frequently" is well supported for edits to existing files, which re-index immediately. Allow up to roughly a one-day lag for net-new shared files on first ingestion.
- Relabel the "restate tables as bullets" rule as an internal heuristic. Do not attribute it to Microsoft.
