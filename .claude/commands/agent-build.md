# Build New AI Agent Command

## Agent Architecture Pattern
Every EsportsForge AI agent follows this pattern:

1. CREATE: backend/app/services/ai/[agentname].py
   - Async class using ForgeCore singleton or direct AsyncAnthropic client
   - Model: claude-sonnet-4-20250514, max_tokens: 1000
   - System prompt from: backend/app/services/ai/prompts.py SYSTEM_PROMPTS dict
   - Always check IntegrityMode before returning recommendations

2. CREATE: backend/app/api/v1/endpoints/[agentname].py
   - FastAPI router with POST endpoint
   - Authenticate via get_current_user dependency
   - Check Redis cache (5 min TTL) before calling Claude
   - Return: { recommendation, confidence, evidence, agent, action }

3. Mount in: backend/app/api/v1/router.py
   - _mount("app.api.v1.endpoints.[agentname]", prefix="/[agentname]", tags=["[AgentName]"])

4. Wire into ForgeCore: backend/app/services/ai/forgecore.py
   - Add agent system prompt to SYSTEM_PROMPTS dict in prompts.py

5. Add to LoopAI feedback: backend/app/services/ai/loop_ai.py
   - Agent outputs tracked for outcome attribution

## Agent to Build
$ARGUMENTS
