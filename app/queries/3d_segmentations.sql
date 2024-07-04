-- :name get_3d_segmentation_by_project_id :one
SELECT *
FROM 3d_segmentations
WHERE project_id = :project_id;

-- :name get_3d_segmentation_by_id :one
SELECT *
FROM 3d_segmentations
WHERE id = :id;
