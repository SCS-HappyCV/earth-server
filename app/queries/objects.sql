-- :name insert_image :insert
INSERT INTO images (object_id, channel_count, height, width)
VALUES (:object_id, :channel_count, :height, :width);

-- :name insert_pointcloud :insert
INSERT INTO pointclouds (object_id, point_count)
VALUES (:object_id, :point_count);

-- :name insert_video :insert
INSERT INTO videos (object_id, duration, codec, container, width, height)
VALUES (:object_id, :duration, :codec, :container, :width, :height);

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
SET thumbnail_id = :thumbnail_image_id
WHERE id = :object_id;

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
	(i.id = :id OR o.id = :object_id)
	AND i.object_id = o.id
	AND o.is_deleted = FALSE;

-- :name get_video :one
SELECT
	v.*,
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
	videos AS v,
	objects AS o
WHERE
	(v.id = :id OR o.id = :object_id)
	AND v.object_id = o.id
	AND o.is_deleted = FALSE;

-- :name get_image_by_origin_name :one
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
	o.origin_name = :origin_name
	AND i.object_id = o.id
	AND o.is_deleted = FALSE;

-- :name get_pointcloud :one
SELECT
	p.*,
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
	pointclouds AS p,
	objects AS o
WHERE
	(p.id = :id OR o.id = :object_id)
	AND p.object_id = o.id
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

-- :name get_images :many
SELECT
	i.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.content_type,
	o.folders,
	o.tags,
	o.origin_name,
	o.origin_type,
	o.size,
	o.thumbnail_id,
	o.versions
FROM images AS i, objects AS o
WHERE
	(i.id IN :ids OR o.id IN :object_ids)
	AND i.object_id = o.id
	AND o.is_deleted = FALSE;

-- :name get_all_images :many
SELECT
	i.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.content_type,
	o.folders,
	o.tags,
	o.type,
	o.origin_name,
	o.origin_type,
	o.size,
	o.thumbnail_id,
	o.versions,
	o.is_deleted
FROM images AS i, objects AS o
WHERE
	i.object_id = o.id
	AND o.is_deleted = FALSE
	AND o.origin_type IN :origin_types
	AND o.content_type LIKE :content_type
LIMIT :offset, :row_count;

-- :name get_all_pointclouds :many
SELECT
	p.*,
	name,
	etag,
	created_time,
	updated_time,
	modified_time,
	content_type,
	folders,
	tags,
	type,
	origin_name,
	origin_type,
	size,
	thumbnail_id,
	versions,
	is_deleted
FROM pointclouds AS p, objects AS o
WHERE
	p.object_id = o.id
	AND o.is_deleted = FALSE
	AND o.origin_type IN :origin_types
LIMIT :offset, :row_count;

-- :name get_all_videos :many
SELECT
	v.*,
	o.name,
	o.etag,
	o.created_time,
	o.updated_time,
	o.modified_time,
	o.content_type,
	o.folders,
	o.tags,
	o.type,
	o.origin_name,
	o.origin_type,
	o.size,
	o.thumbnail_id,
	o.versions,
	o.is_deleted
FROM videos AS v, objects AS o
WHERE
	v.object_id = o.id
	AND o.is_deleted = FALSE
	AND o.origin_type IN :origin_types
	AND o.content_type LIKE :content_type
LIMIT :offset, :row_count;

-- :name get_all_objects :many
SELECT
	*,
	id AS object_id
FROM objects
WHERE
	is_deleted = FALSE
	AND origin_type IN :origin_types
	AND content_type LIKE :content_type
LIMIT :offset, :row_count;

-- :name count_objects :scalar
SELECT COUNT(*)
FROM objects
WHERE
	is_deleted = FALSE
	AND type IN :types
	AND origin_type IN :origin_types;
