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

-- :name create_2d_segmentation :insert
INSERT INTO 2d_segmentations (
	project_id,
	image_id
) VALUES (
	:project_id,
	:image_id
);

-- :name update_2d_segmentation :affected
UPDATE 2d_segmentations
SET
	result = :result,
	mask_image_id = :mask_image_id,
	plot_image_id = :plot_image_id
WHERE id = :id;

-- :name delete_2d_segmentation :affected
UPDATE 2d_segmentations AS s,
	projects AS p
SET p.is_deleted = true
WHERE
	s.id = :id
	AND s.project_id = p.id;

-- :name complete_2d_segmentation :affected
UPDATE 2d_segmentations, projects
SET
	2d_segmentations.plot_image_id = :plot_image_id,
	projects.modified_time = NOW()
WHERE
	2d_segmentations.id = :id
	AND 2d_segmentations.project_id = projects.id
	AND projects.deleted = false;
