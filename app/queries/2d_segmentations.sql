-- :name get_2d_segmentations_by_project_id :many
SELECT *
FROM 2d_segmentations
WHERE project_id = :project_id;
