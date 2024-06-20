-- :name get_3d_segmentations_by_project_id :many
SELECT *
FROM 3d_segmentations
WHERE project_id = :project_id;
