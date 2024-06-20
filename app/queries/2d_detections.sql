-- :name get_2d_detections_by_project_id :many
SELECT *
FROM 2d_detections
WHERE project_id = :project_id;

-- :name get_2d_detection :one
SELECT
    '2d_detections.' AS 2d_detections_prefix,
    2d_detections.*,
    'projects.' AS projects_prefix,
    projects.*
FROM 2d_detections, projects
WHERE
    2d_detections.id = :id
    AND 2d_detections.project_id = projects.id
    AND projects.is_deleted = false;

-- :name delete_2d_detection :affected
UPDATE 2d_detections
SET is_deleted = true
WHERE id = :id;
