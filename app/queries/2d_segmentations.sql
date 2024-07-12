-- :name get_2d_segmentation_by_project_id :one
SELECT
	2d_segmentations.*,
	p.name,
	p.created_time,
	p.updated_time,
	p.cover_image_id,
	p.modified_time,
	p.status
FROM 2d_segmentations AS 2d_seg, projects AS p
WHERE
	2d_seg.project_id = :project_id
	AND 2d_seg.project_id = p.id
	AND p.deleted = false;

-- :name get_2d_segmentation :one
SELECT
	2d_segmentations.*,
	p.name,
	p.created_time,
	p.updated_time,
	p.cover_image_id,
	p.modified_time,
	p.status
FROM 2d_segmentations AS 2d_seg, projects AS p
WHERE
	2d_seg.id = :id
	AND 2d_seg.project_id = p.id
	AND p.deleted = false;

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
