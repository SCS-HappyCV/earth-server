-- :name get_conversations_by_project_id :many
SELECT *
FROM conversations
WHERE project_id = :project_id;

-- :name get_conversation_by_id :one
SELECT *
FROM conversations
WHERE id = :id;
