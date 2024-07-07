-- :name get_projects :many
SELECT *
FROM projects
WHERE
	is_deleted = false
	AND type IN :types
LIMIT :offset, :row_count;

-- :name get_project :one
SELECT *
FROM projects
WHERE
	id = :id
	AND is_deleted = false;

-- :name create_project :insert
INSERT INTO projects (name, type, cover_image_id)
VALUES (:name, :type, :cover_image_id);

-- :name delete_project :affected
UPDATE projects
SET is_deleted = true
WHERE id = :id;
