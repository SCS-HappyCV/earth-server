-- :name get_conversation :many
SELECT
	p.name,
	p.created_time,
	p.updated_time,
	c.messages,
	c.project_id,
	ci.conversation_id,
	ci.image_id
FROM
	conversations AS c,
	conversation_images AS ci,
	projects AS p
WHERE
	c.project_id = p.id
	AND c.id = ci.conversation_id
	AND c.id = :id
	AND p.is_deleted = false;

-- :name get_conversation_by_project_id :many
SELECT
	p.name,
	p.created_time,
	p.updated_time,
	c.messages,
	c.project_id,
	ci.conversation_id,
	ci.image_id
FROM
	conversations AS c,
	conversation_images AS ci,
	projects AS p
WHERE
	c.project_id = p.id
	AND c.id = ci.conversation_id
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
	projects.updated_time = NOW(),
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
