-- :name get_all_objects :many
SELECT *
FROM objects
WHERE is_deleted = false
LIMIT :offset, :row_count;

-- :name get_object_by_id :one
SELECT *
FROM objects
WHERE
    id = :id
    AND is_deleted = false;

-- :name get_images_by_object_id :many
SELECT *
FROM images
WHERE object_id = :object_id;

-- :name get_pointclouds_by_object_id :many
SELECT *
FROM pointclouds
WHERE object_id = :object_id;

-- :name get_image_by_id :one
SELECT
    'images.' AS images_prefix,
    images.*,
    'objects.' AS objects_prefix,
    objects.*
FROM images, objects
WHERE
    images.id = :id
    AND images.object_id = objects.id
    AND objects.is_deleted = false;

-- :name get_pointcloud_by_id :one
SELECT
    'pointclouds.' AS pointclouds_prefix,
    pointclouds.*,
    'objects.' AS objects_prefix,
    objects.*
FROM pointclouds, objects
WHERE
    pointclouds.id = :id
    AND pointclouds.object_id = objects.id
    AND objects.is_deleted = false;
