"""LLM prompt templates."""


def relevance_prompt(title: str, text: str, include_keywords: list, exclude_keywords: list) -> str:
    """Generate prompt for relevance filtering."""
    return f"""Analyze this article and determine if it's relevant for finding startup team members to network with.

Article Title: {title}

Article Text (first 2000 chars):
{text[:2000]}

Keywords that indicate relevance: {', '.join(include_keywords)}
Keywords that indicate irrelevance: {', '.join(exclude_keywords)}

Determine if this article:
1. Mentions startups, new companies, or entrepreneurial ventures
2. Discusses hiring, team building, or new team members
3. Covers funding rounds, product launches, or company milestones
4. Contains information that could help identify people to reach out to

Return your analysis as JSON with:
- is_relevant: boolean (true if article is useful for networking outreach)
- reason: string (brief explanation of your decision)
- confidence: float between 0.0 and 1.0
"""


def company_extraction_prompt(text: str) -> str:
    """Generate prompt for extracting companies from article."""
    return f"""Extract all startup companies and their teams mentioned in this article.

Article Text:
{text[:4000]}

For each company mentioned, provide:
- name: The company name
- description: Brief description of what they do (if available)
- team_page_url: URL to their team/about page if mentioned in the article
- mentioned_context: Why they were mentioned (e.g., "raised Series A", "hired new CTO", "launched product")

Focus on:
- Startups and new companies
- Companies mentioned in the context of funding, hiring, or team changes
- Companies with identifiable team members

Return as JSON with a "companies" array containing the extracted companies.
If no relevant companies are found, return an empty array.
"""


def person_extraction_prompt(html_text: str, company_name: str) -> str:
    """Generate prompt for extracting people from team page."""
    return f"""Extract team members from this company team/about page.

Company: {company_name}

Page Content:
{html_text[:6000]}

Extract information for each team member you can identify:
- full_name: Their full name
- title: Their job title/role
- linkedin_url: LinkedIn profile URL if present
- email: Email address if visible
- bio: Brief bio or description if available

Return as JSON with a "people" array containing all team members found.
Focus on leadership and senior team members.
If no team members are found, return an empty array.
"""


def person_vetting_prompt(
    person_name: str,
    title: str,
    bio: str,
    linkedin_url: str,
    schools: list,
    roles: list,
    industries: list,
    seniority_levels: list,
    locations: list,
) -> str:
    """Generate prompt for vetting person against preferences."""
    return f"""Analyze this person's profile and determine if they match the target networking criteria.

Person Information:
- Name: {person_name}
- Title: {title or 'Not specified'}
- Bio: {bio or 'Not available'}
- LinkedIn: {linkedin_url or 'Not available'}

Target Criteria:
- Preferred Schools: {', '.join(schools) if schools else 'Any'}
- Preferred Roles: {', '.join(roles) if roles else 'Any'}
- Preferred Industries: {', '.join(industries) if industries else 'Any'}
- Preferred Seniority: {', '.join(seniority_levels) if seniority_levels else 'Any'}
- Preferred Locations: {', '.join(locations) if locations else 'Any'}

Based on the available information, infer and extract:
- school: Educational institution (if identifiable from bio/LinkedIn, otherwise null)
- role_category: Role category that best matches (Engineering, Product, Design, etc.)
- seniority_level: Seniority level (Senior, Lead, Staff, Principal, Director, VP, C-level, etc.)
- location: Geographic location (if identifiable, otherwise null)
- industry_experience: Array of relevant industry tags based on their experience
- matches_criteria: Boolean indicating if they match at least some target criteria
- reasoning: Brief explanation of your assessment and what criteria they match

Return as JSON with these fields. Be generous with matching - if someone is close to the criteria or has relevant experience, mark them as a match.
"""


def response_likelihood_prompt(
    person_name: str,
    title: str,
    bio: str,
    company_context: str,
    source_article: str,
) -> str:
    """Generate prompt for estimating response likelihood."""
    return f"""Estimate how likely this person is to respond to a networking outreach message.

Person: {person_name}
Title: {title or 'Not specified'}
Bio: {bio or 'Not available'}
Company Context: {company_context}
Why they're in the news: {source_article[:500]}

Consider factors like:
- Seniority level (more senior = often less responsive)
- Company stage (early stage founders often more accessible)
- Recent events (just raised funding, just hired - good timing)
- Role type (some roles like recruiting/BD more open to outreach)
- Public presence (if they seem engaged in community/content)

Return a score between 0.0 and 1.0, where:
- 0.0-0.3: Low likelihood (very senior, busy, not public-facing)
- 0.3-0.6: Medium likelihood (mid-senior, selectively responsive)
- 0.6-1.0: High likelihood (accessible, good timing, community-engaged)

Also provide a brief explanation of the score.

Return as JSON: {{"score": 0.7, "reasoning": "explanation..."}}
"""
