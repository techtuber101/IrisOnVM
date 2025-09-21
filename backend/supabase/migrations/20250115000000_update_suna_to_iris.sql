-- Migration to update all existing Suna agents to Iris
-- This updates the agent names and descriptions for centrally managed agents

BEGIN;

-- Update all agents that are marked as Suna default agents to use the new Iris name and description
UPDATE agents 
SET 
    name = 'Iris',
    description = 'Iris is your AI assistant with access to various tools and integrations to help you with tasks across domains.',
    metadata = jsonb_set(
        jsonb_set(
            metadata, 
            '{last_central_update}', 
            to_jsonb(now())
        ),
        '{management_version}',
        '"iris-v1"'
    )
WHERE 
    COALESCE((metadata->>'is_suna_default')::boolean, false) = true
    AND COALESCE((metadata->>'centrally_managed')::boolean, false) = true
    AND name = 'Suna';

-- Log the update count
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated % Suna agents to Iris', updated_count;
END $$;

COMMIT;
