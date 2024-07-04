-- :name get_2d_segmentation_by_project_id :one
SELECT *
FROM 2d_segmentations
WHERE project_id = :project_id;

-- :name get_2d_segmentation :one
SELECT
    2d_segmentations.id,
    image_id,
    mask_image_id,
    plot_image_id,
    result,
    projects.name AS project_name,
    projects.created_time AS project_created_time,
    projects.updated_time AS project_updated_time,
    projects.cover_image_id
FROM 2d_segmentations, projects
WHERE
    2d_segmentations.id = :id
    AND 2d_segmentations.project_id = projects.id
    AND projects.deleted = false;
