# Add New Title Intelligence Module Command

## Title Module Architecture
Each title has: mock data, agents, and empty states.

## Files to Create for Each Title
1. backend/app/api/v1/endpoints/[titleid]/ — title-specific endpoints
2. backend/app/models/[titleid].py — title-specific SQLAlchemy model
3. frontend/src/lib/titles.ts — update FULL_TITLE_LIST array
4. backend/app/services/ai/prompts.py — add title-specific system prompt context
5. Test: Switch to this title in the sidebar — verify all pages update correctly

## Title to Add
$ARGUMENTS
