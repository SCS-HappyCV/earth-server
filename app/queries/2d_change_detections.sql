-- :name get_2d_change_detection_by_project_id :one
SELECT *
FROM 2d_change_detections
WHERE project_id = :project_id;

-- :name get_2d_change_detection :one
SELECT
	cd.*,
	p.name,
	p.created_time,
	p.updated_time,
	p.modified_time,
	p.type,
	p.cover_image_id,
	p.status
FROM 2d_change_detections AS cd, projects AS p
WHERE
	(cd.id = :id OR p.id = :project_id)
	AND cd.project_id = p.id
	AND p.is_deleted = false;

-- :name create_2d_change_detection :insert
INSERT INTO 2d_change_detections (
	project_id,
	image1_id,
	image2_id
) VALUES (
	:project_id,
	:image1_id,
	:image2_id
);

-- :name update_2d_change_detection :affected
UPDATE 2d_change_detections
SET
	result = :result,
	plot_image_id = :plot_image_id,
	mask_image_id = :mask_image_id
WHERE id = :id;

-- :name delete_2d_change_detection :affected
UPDATE 2d_change_detections AS cd,
	projects AS p
SET p.is_deleted = true
WHERE
	cd.id = :id
	AND cd.project_id = p.id;

-- :name complete_2d_change_detection :affected
UPDATE 2d_change_detections AS cd, projects AS p
SET
	cd.plot_image_id = :plot_image_id,
	cd.mask_image_id = :mask_image_id,
	p.modified_time = NOW(),
	p.status = 'completed'
WHERE
	(
		cd.id = :id
		OR p.id = :project_id
	)
	AND cd.project_id = p.id
	AND p.is_deleted = false;
