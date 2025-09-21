# Updating Suna Agents to Iris

This guide explains how to update existing "Suna" agents to "Iris" for users with old accounts.

## Problem

Users who created accounts before the rebrand from "Suna" to "Iris" still have agents named "Suna" in their database. While the central configuration has been updated to "Iris", the agent names in the database remain "Suna".

## Solutions

### 1. Database Migration (Recommended for Production)

Run the SQL migration to update all Suna agents to Iris:

```bash
# Apply the migration
psql -d your_database -f backend/supabase/migrations/20250115000000_update_suna_to_iris.sql
```

This migration will:
- Update all centrally managed Suna agents to use the name "Iris"
- Update the description to match the new configuration
- Set the management version to "iris-v1"
- Log the update timestamp

### 2. Python Script (For Manual Updates)

Run the Python script to update agents programmatically:

```bash
cd backend
python core/utils/scripts/update_suna_to_iris.py
```

This script will:
- Show current statistics about Suna vs Iris agents
- Ask for confirmation before updating
- Update all agents that still have the name "Suna"
- Provide detailed results

### 3. Admin API Endpoints (For Individual Users)

Use the admin API endpoints to update specific users or all users:

#### Update a specific user's agent:
```bash
curl -X POST "https://your-api-url/admin/suna-agents/update-to-iris/{account_id}" \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

#### Update all users' agents:
```bash
curl -X POST "https://your-api-url/admin/suna-agents/update-all-to-iris" \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

## What Gets Updated

For each agent, the following fields are updated:
- `name`: "Suna" → "Iris"
- `description`: Updated to match the new central configuration
- `metadata.last_central_update`: Set to current timestamp
- `metadata.management_version`: Set to "iris-v1"

## Verification

After running any of these solutions, you can verify the update by:

1. Checking the agent name in the frontend
2. Looking at the database directly:
   ```sql
   SELECT agent_id, account_id, name, metadata->>'management_version' 
   FROM agents 
   WHERE metadata->>'is_suna_default' = 'true';
   ```

## Notes

- Only centrally managed agents (`is_suna_default: true` and `centrally_managed: true`) are updated
- Custom agents created by users are not affected
- The update is safe and can be run multiple times
- All solutions preserve existing agent functionality and configurations
