-- :name insert_image :insert
INSERT INTO images (object_id, channel_count, height, width)
VALUES (:object_id, :channel_count, :height, :width);

-- :name insert_pointcloud :insert
INSERT INTO pointclouds (object_id, point_count)
VALUES (:object_id, :point_count);

-- :name get_image :one
SELECT
    i.*,
    o.name,
    o.etag,
    o.modified_time,
    o.size,
    o.content_type,
    o.folders,
    o.tags,
    o.origin_name,
    o.versions,
    o.type
FROM
    images AS i,
    objects AS o
WHERE
    i.object_id = o.id
    AND i.id = :id
    AND o.is_deleted = FALSE;

-- :name get_pointcloud :one
SELECT
    p.*,
    o.name,
    o.etag,
    o.modified_time,
    o.size,
    o.content_type,
    o.folders,
    o.tags,
    o.origin_name,
    o.versions,
    o.type
FROM
    pointclouds AS p,
    objects AS o
WHERE
    p.object_id = o.id
    AND p.id = :id
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

-- :name insert_object :insert
INSERT INTO objects (
    name,
    etag,
    modified_time,
    size,
    content_type,
    folders,
    origin_name,
    type
) VALUES (
    :name,
    :etag,
    :modified_time,
    :size,
    :content_type,
    :folders,
    :origin_name,
    :type
);

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
    o.modified_time,
    o.size,
    o.versions,
    o.content_type,
    o.folders,
    o.tags,
    o.origin_name
FROM pointclouds AS p, objects AS o
WHERE
    p.object_id = o.id
    AND o.is_deleted = FALSE;

-- :name get_images :many
SELECT
    i.*,
    o.name,
    o.type,
    o.etag,
    o.modified_time,
    o.size,
    o.versions,
    o.content_type,
    o.folders,
    o.tags,
    o.origin_name
FROM images AS i, objects AS o
WHERE
    i.object_id = o.id
    AND o.is_deleted = FALSE;

-- :name get_objects :many
SELECT
    id,
    name,
    etag,
    modified_time,
    size,
    versions,
    content_type,
    folders,
    tags,
    origin_name
FROM objects
WHERE is_deleted = FALSE;
