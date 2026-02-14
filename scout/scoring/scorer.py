"""Person scoring logic."""

import logging
from datetime import datetime

from scout.models.person import PersonExtraction, PersonVetting, ScoredPerson
from scout.models.company import Company
from scout.models.config import Preferences, ScoringWeights

logger = logging.getLogger(__name__)


class PersonScorer:
    """Score people based on fit and response likelihood."""

    def __init__(self, preferences: Preferences, weights: ScoringWeights):
        """
        Initialize person scorer.

        Args:
            preferences: User preferences for matching
            weights: Scoring weights
        """
        self.preferences = preferences
        self.weights = weights

    def calculate_fit_score(self, vetting: PersonVetting) -> tuple[float, str]:
        """
        Calculate fit score based on matching criteria.

        Args:
            vetting: Person vetting results

        Returns:
            Tuple of (score, reasoning)
        """
        score = 0.0
        reasons = []

        # School match
        if vetting.school and self.preferences.schools:
            for target_school in self.preferences.schools:
                if target_school.lower() in vetting.school.lower():
                    score += self.weights.school_match
                    reasons.append(f"School match: {vetting.school}")
                    break

        # Role match
        if vetting.role_category and self.preferences.roles:
            for target_role in self.preferences.roles:
                if target_role.lower() in vetting.role_category.lower():
                    score += self.weights.role_match
                    reasons.append(f"Role match: {vetting.role_category}")
                    break

        # Industry match
        if vetting.industry_experience and self.preferences.industries:
            matched_industries = []
            for industry in vetting.industry_experience:
                for target_industry in self.preferences.industries:
                    if (
                        target_industry.lower() in industry.lower()
                        or industry.lower() in target_industry.lower()
                    ):
                        matched_industries.append(industry)
                        break
            if matched_industries:
                score += self.weights.industry_match * len(matched_industries)
                reasons.append(f"Industry match: {', '.join(matched_industries)}")

        # Seniority match
        if vetting.seniority_level and self.preferences.seniority_levels:
            for target_seniority in self.preferences.seniority_levels:
                if target_seniority.lower() in vetting.seniority_level.lower():
                    score += self.weights.seniority_match
                    reasons.append(f"Seniority match: {vetting.seniority_level}")
                    break

        # Location match
        if vetting.location and self.preferences.locations:
            for target_location in self.preferences.locations:
                if (
                    target_location.lower() in vetting.location.lower()
                    or vetting.location.lower() in target_location.lower()
                ):
                    score += self.weights.location_match
                    reasons.append(f"Location match: {vetting.location}")
                    break

        # Use vetting reasoning if no specific matches
        if not reasons and vetting.reasoning:
            reasons.append(vetting.reasoning)

        reasoning = "; ".join(reasons) if reasons else "No specific matches found"
        return score, reasoning

    def calculate_response_score(
        self, vetting: PersonVetting, company: Company
    ) -> tuple[float, str]:
        """
        Calculate response likelihood score.

        Args:
            vetting: Person vetting results
            company: Company information

        Returns:
            Tuple of (score, reasoning)
        """
        score = 0.5  # Base score
        reasons = []

        # Seniority affects response rate (more senior = less responsive)
        if vetting.seniority_level:
            level_lower = vetting.seniority_level.lower()
            if any(x in level_lower for x in ["c-level", "ceo", "cto", "cfo"]):
                score -= 0.2
                reasons.append("C-level (typically busy)")
            elif any(x in level_lower for x in ["vp", "director"]):
                score -= 0.1
                reasons.append("Director/VP level")
            elif any(x in level_lower for x in ["senior", "lead", "staff"]):
                score += 0.1
                reasons.append("Senior IC (often accessible)")

        # Recent company activity (funding, hiring) increases response likelihood
        if company.source_article_url:
            reasons.append("Recently in the news (good timing)")
            score += 0.2

        # Role type affects response rate
        if vetting.role_category:
            role_lower = vetting.role_category.lower()
            if any(x in role_lower for x in ["recruiting", "hr", "people"]):
                score += 0.2
                reasons.append("Recruiting role (open to outreach)")
            elif any(x in role_lower for x in ["bd", "business development", "sales"]):
                score += 0.15
                reasons.append("BD/Sales role (network-oriented)")

        # Cap score between 0 and 1
        score = max(0.0, min(1.0, score))

        reasoning = "; ".join(reasons) if reasons else "Standard response likelihood"
        return score, reasoning

    def score_person(
        self,
        extraction: PersonExtraction,
        vetting: PersonVetting,
        company: Company,
        article_url: str,
    ) -> ScoredPerson:
        """
        Create fully scored person.

        Args:
            extraction: Person extraction data
            vetting: Person vetting results
            company: Company information
            article_url: Source article URL

        Returns:
            ScoredPerson with all scores calculated
        """
        fit_score, fit_reasons = self.calculate_fit_score(vetting)
        response_score, response_reasons = self.calculate_response_score(
            vetting, company
        )

        # Total score is fit + response (weighted equally for now)
        total_score = fit_score + response_score

        # Collect profile URLs
        profile_urls = []
        if extraction.linkedin_url:
            profile_urls.append(extraction.linkedin_url)
        if company.team_page_url:
            profile_urls.append(company.team_page_url)

        scored_person = ScoredPerson(
            full_name=extraction.full_name,
            title=extraction.title,
            linkedin_url=extraction.linkedin_url,
            email=extraction.email,
            company_name=company.name,
            company_url=company.team_page_url,
            school=vetting.school,
            role_category=vetting.role_category,
            seniority_level=vetting.seniority_level,
            location=vetting.location,
            industry_experience=vetting.industry_experience,
            fit_score=fit_score,
            response_score=response_score,
            total_score=total_score,
            fit_reasons=fit_reasons,
            response_reasons=response_reasons,
            source_article_url=article_url,
            source_profile_urls=profile_urls,
            extracted_at=datetime.now(),
        )

        logger.debug(
            f"Scored {extraction.full_name}: fit={fit_score:.2f}, "
            f"response={response_score:.2f}, total={total_score:.2f}"
        )

        return scored_person
