-- :name get_projects :many
SELECT *
FROM projects
WHERE
	is_deleted = false
	AND type IN :types
	AND status IN :statuses
LIMIT :offset, :row_count;

-- :name get_project :one
SELECT *
FROM projects
WHERE
	id = :id
	AND is_deleted = false;

-- :name count_projects :scalar
SELECT count(*)
FROM projects
WHERE
	is_deleted = false
	AND type IN :types
	AND status IN :statuses;

-- :name create_project :insert
INSERT INTO projects (name, type, cover_image_id, status)
VALUES (:name, :type, :cover_image_id, :status);

-- :name delete_project :affected
UPDATE projects
SET is_deleted = true
WHERE id = :id;

-- :name update_project_name :affected
UPDATE projects
SET name = :name
WHERE id = :id;

-- :name update_project_cover_image :affected
UPDATE projects
SET cover_image_id = :cover_image_id
WHERE id = :id;
