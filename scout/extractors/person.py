"""Person vetting and extraction."""

import logging
from typing import Optional

from scout.llm.base import BaseLLMProvider
from scout.llm.prompts import person_vetting_prompt
from scout.models.person import PersonExtraction, PersonVetting
from scout.models.config import Preferences

logger = logging.getLogger(__name__)


class PersonVetter:
    """Vet people against user preferences using LLM."""

    def __init__(self, llm: BaseLLMProvider, preferences: Preferences):
        """
        Initialize person vetter.

        Args:
            llm: LLM provider instance
            preferences: User preferences for matching
        """
        self.llm = llm
        self.preferences = preferences

    def vet(self, person: PersonExtraction) -> Optional[PersonVetting]:
        """
        Vet person against preferences.

        Args:
            person: Person extraction data

        Returns:
            PersonVetting result or None if vetting fails
        """
        try:
            logger.debug(f"Vetting person: {person.full_name}")

            # Generate prompt
            prompt = person_vetting_prompt(
                person_name=person.full_name,
                title=person.title or "",
                bio=person.bio or "",
                linkedin_url=person.linkedin_url or "",
                schools=self.preferences.schools,
                roles=self.preferences.roles,
                industries=self.preferences.industries,
                seniority_levels=self.preferences.seniority_levels,
                locations=self.preferences.locations,
            )

            # Call LLM with structured output
            vetting = self.llm.generate_structured(prompt, PersonVetting)

            logger.debug(
                f"Vetted {person.full_name}: matches={vetting.matches_criteria}"
            )
            return vetting

        except Exception as e:
            logger.error(f"Failed to vet person {person.full_name}: {e}")
            return None
