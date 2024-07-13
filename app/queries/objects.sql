-- :name insert_image :insert
INSERT INTO images (object_id, channel_count, height, width)
VALUES (:object_id, :channel_count, :height, :width);

-- :name insert_pointcloud :insert
INSERT INTO pointclouds (object_id, point_count)
VALUES (:object_id, :point_count);

-- :name insert_object :insert
INSERT INTO objects (
	name,
	etag,
	created_time,
	updated_time,
	modified_time,
	size,
	type,
	content_type,
	folders,
	origin_name,
	origin_type
) VALUES (
	:name,
	:etag,
	:created_time,
	:updated_time,
	:modified_time,
	:size,
	:type,
	:content_type,
	:folders,
	:origin_name,
	:origin_type
);

-- :name update_thumbnail_id :affected
UPDATE objects
SET thumbnail_id = :image_id
WHERE id = :id;

-- :name get_image :one
SELECT
	i.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.type,
	o.size,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type,
	o.versions,
	o.thumbnail_id
FROM
	images AS i,
	objects AS o
WHERE
	i.object_id = o.id
	AND i.id = :id
	AND o.is_deleted = FALSE;

-- :name get_image_by_object_id :one
SELECT
	i.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.type,
	o.size,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type,
	o.versions,
	o.thumbnail_id
FROM
	images AS i,
	objects AS o
WHERE
	i.object_id = o.id
	AND i.object_id = :object_id
	AND o.is_deleted = FALSE;

-- :name get_pointcloud :one
SELECT
	p.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.size,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type,
	o.versions,
	o.type
FROM
	pointclouds AS p,
	objects AS o
WHERE
	p.object_id = o.id
	AND p.id = :id
	AND o.is_deleted = FALSE;

-- :name get_pointcloud_by_object_id :one
SELECT
	p.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.size,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type,
	o.versions,
	o.type
FROM
	pointclouds AS p,
	objects AS o
WHERE
	p.object_id = o.id
	AND p.object_id = :object_id
	AND o.is_deleted = FALSE;

-- :name get_object :one
SELECT
	id,
	name,
	etag,
	modified_time,
	size,
	versions,
	content_type,
	folders,
	tags
FROM
	objects
WHERE
	id = :id
	AND is_deleted = FALSE;

-- :name delete_image :affected
UPDATE images
SET is_deleted = TRUE
WHERE id = :id;

-- :name delete_pointcloud :affected
UPDATE pointclouds
SET is_deleted = TRUE
WHERE id = :id;

-- :name delete_object :affected
UPDATE objects
SET is_deleted = TRUE
WHERE id = :id;

-- :name update_object_folder :affected
UPDATE objects
SET
	folders = :folders,
	updated_time = NOW()
WHERE
	id = :id
	AND is_deleted = FALSE;

-- :name get_objects_by_ids :many
SELECT *
FROM objects
WHERE
	id IN :ids
	AND is_deleted = FALSE;

-- :name get_object_name :scalar
SELECT name
FROM objects
WHERE
	id = :id
	AND is_deleted = FALSE;

-- :name get_pointclouds :many
SELECT
	p.*,
	o.type,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.size,
	o.versions,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type
FROM pointclouds AS p, objects AS o
WHERE
	p.object_id = o.id
	AND o.is_deleted = FALSE
	AND o.origin_type IN :origin_types
LIMIT :offset, :row_count;

-- :name get_images :many
SELECT
	i.*,
	o.name,
	o.type,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.size,
	o.versions,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type,
	o.thumbnail_id
FROM images AS i, objects AS o
WHERE
	i.object_id = o.id
	AND o.is_deleted = FALSE
	AND o.origin_type IN :origin_types
LIMIT :offset, :row_count;

-- :name get_images_by_ids :many
SELECT
	i.*,
	o.name,
	o.type,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.size,
	o.versions,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type
FROM images AS i, objects AS o
WHERE
	i.object_id = o.id
	AND o.is_deleted = FALSE
	AND i.id IN :ids;

-- :name get_objects :many
SELECT
	*,
	id AS object_id
FROM objects
WHERE
	is_deleted = FALSE
	AND origin_type IN :origin_types
LIMIT :offset, :row_count;
