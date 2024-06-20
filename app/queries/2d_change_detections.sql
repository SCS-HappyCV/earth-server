-- :name get_2d_change_detections_by_project_id :many
SELECT *
FROM 2d_change_detections
WHERE project_id = :project_id;
