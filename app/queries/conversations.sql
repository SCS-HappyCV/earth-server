-- :name get_conversation :one
SELECT
	p.name,
	p.created_time,
	p.updated_time,
	p.modified_time,
	c.*
FROM
	conversations AS c,
	projects AS p
WHERE
	c.project_id = p.id
	AND c.id = :id
	AND p.is_deleted = false;

-- :name get_conversation_by_project_id :one
SELECT
	p.name,
	p.created_time,
	p.updated_time,
	p.modified_time,
	c.*
FROM
	conversations AS c,
	projects AS p
WHERE
	c.project_id = p.id
	AND c.project_id = :project_id
	AND p.is_deleted = false;

-- :name create_conversation :insert
INSERT INTO conversations (messages, project_id)
VALUES (:messages, :project_id);

-- :name create_conversation_image :insert
INSERT INTO conversation_images (conversation_id, image_id)
VALUES (:conversation_id, :image_id);

-- :name update_conversation :affected
UPDATE conversations, projects
SET
	messages = :messages,
	projects.modified_time = NOW()
WHERE
	conversations.id = :id
	AND projects.id = conversations.project_id
	AND projects.is_deleted = false;

-- :name get_conversations :many
SELECT
	p.name,
	p.created_time,
	p.updated_time,
	p.cover_image_id,
	p.modified_time,
	c.id,
	c.project_id
FROM
	projects AS p,
	conversations AS c
WHERE
	p.id = c.project_id
	AND p.is_deleted = false;

-- :name delete_conversation :affected
UPDATE conversations, projects
SET
	conversations.is_deleted = true
WHERE
	conversations.id = :id
	AND projects.id = conversations.project_id
	AND projects.is_deleted = false;

-- :name get_conversation_image_ids :many
SELECT image_id
FROM
	conversation_images
WHERE
	conversation_id = :conversation_id;
