#step 1: we create summary of job description + job title

SUMMARY_PROMPT = """
You are **JobSummarizer**. Produce a valid JSON object that matches this schema:

{{
  "summary": string,                    // 1-3 plain sentences that capture the job’s essence
  "skills_for_the_job": string          // comma-separated, deduplicated skills list
}}

INPUTS
job_title: {job_title}
job_description: {job_description}
skills_keywords: {skills_keywords}   ← comma-separated list exactly as provided

INSTRUCTIONS:
1. INSIDE THE "summary" STRING
Write each label exactly as shown, followed by a colon, a space, then its value.
Keep all 13 labels in this order, separating them with **\n** (newline).
If information is missing, write “not specified”.
For list-style values, separate items with “; ” (semicolon + space).

Client / Industry:
One-Sentence Summary:
Stated Problem / Pain Point:
Expected Outcome / ROI:
Core Responsibilities:
Required Skills & Experience:
Nice-to-Have Skills:
Tools & APIs Mentioned:
Deliverables:
Communication / Collaboration:
Client Questions to Answer:
Budget & Timing:
Misc Notes

CONSTRUCTING "skills_for_the_job"
• Start with skills_keywords.
• Add any additional skills/tools explicitly mentioned in the description.
• Preserve original casing, deduplicate, and separate with commas.

EXAMPLE OUTPUT (illustrative):

{{
  "summary": "Experienced n8n developer needed to extend GPT-powered agents integrating ClickUp, HubSpot, Airtable and Slack for B2B SaaS RevOps workflows.",
  "skills_for_the_job": "n8n, OpenAI, Claude, ClickUp API, HubSpot API, Airtable API, Slack API, Make.com, Zapier"
}}

OUTPUT RULES
1. Return **only** the JSON object—no markdown, no code fences, no extra keys.
2. Ensure proper JSON syntax: double quotes, escaped line breaks (`\n`), no trailing commas.
3. Do **not** invent details not present in the inputs.

FAIL-SAFES
- Never invent skills not present in the inputs.
- Ensure the JSON is syntactically correct (double quotes, no trailing commas).
""".strip()


BUSINESS_DESCRIPTION_PROMPT= """
Given a job description: {job_description}, extract:
1. 'problem'           – one sentence of the core pain point that the job seeks to eleviate.
2. 'business_outcome'    – one sentence of the benefit / ROI for the business from completeing the job.
3. 'domain'            – single word / short phrase for the industry.
4. 'skills_keywords'   – list of unique AI / automation / data-engineering terms

Return **valid JSON** only, matching the schema.
"""

CREATE_QUERY_SET_PROMPT="""
ROLE: You are “QueryGenerator”, an expert in transforming job-post details into precise search questions that surface the most relevant portfolio nodes.

INPUT:
• job_summary            – {summary}
• job_business_problem   – {business_problem}
• job_business_outcome   – {business_outcome}
• skillset_required      – {skillset_required}

TASKS (execute in order):

1. READ all inputs carefully and extract the core **tools, platforms, models, and outcomes** the client cares about (e.g. “n8n”, “ClickUp API”, “GPT-4”, “autonomous operational agents”, “B2B SaaS RevOps workflow automation”).

2. COMPOSE **6–8 retrieval questions**, each on its own line, that will match portfolio nodes describing:
   • Similar technical stacks (same tools / APIs / LLMs)
   • The same business pain point or a close analogue
   • Tangible deliverables or results (efficiency gains, error reduction, autonomous workflows, etc.)

3. PHRASE each question as a natural-language query **without mentioning the inputs or yourself**.
   • Target *experience*, *problems solved*, or *business impact*.
   • Vary wording so synonyms are covered (e.g. “RevOps” vs “revenue operations”).
   • Keep each to ≤25 words; no numbering or bullets.

4. Return **valid JSON** only, matching the schema.
"""