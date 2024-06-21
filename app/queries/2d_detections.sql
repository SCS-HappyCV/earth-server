-- :name get_2d_detections_by_project_id :many
SELECT *
FROM 2d_detections
WHERE project_id = :project_id;

-- :name get_2d_detection :one
SELECT
    2d_detections.id,
    image_id,
    result,
    project_id,
    plot_image_id,
    projects.name AS project_name,
    projects.created_time AS project_created_time,
    projects.updated_time AS project_updated_time
FROM 2d_detections, projects
WHERE
    2d_detections.id = :id
    AND 2d_detections.project_id = projects.id
    AND projects.is_deleted = false;

-- :name create_2d_detection :insert
INSERT INTO 2d_detections (image_id, project_id)
VALUES (:image_id, :project_id);

-- :name delete_2d_detection :affected
UPDATE 2d_detections
SET is_deleted = true
WHERE id = :id;

-- :name delete_2d_detections_by_project_id :affected
UPDATE 2d_detections
SET is_deleted = true
WHERE project_id = :project_id;
