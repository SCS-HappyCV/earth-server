-- :name get_3d_segmentation :one
SELECT
	3d_seg.*,
	p.name,
	p.created_time,
	p.updated_time,
	p.cover_image_id,
	p.modified_time,
	p.status
FROM 3d_segmentations AS 3d_seg, projects AS p
WHERE
	(3d_seg.id = :id OR p.id = :project_id)
	AND 3d_seg.project_id = p.id
	AND p.is_deleted = false;

-- :name create_3d_segmentation :insert
INSERT INTO 3d_segmentations (
	project_id,
	pointcloud_id
) VALUES (
	:project_id,
	:pointcloud_id
);

-- :name update_3d_segmentation :affected
UPDATE 3d_segmentations
SET
	result_pointcloud_id = :result_pointcloud_id
WHERE id = :id;

-- :name complete_3d_segmentation :affected
UPDATE 3d_segmentations, projects
SET
	3d_segmentations.result_pointcloud_id = :result_pointcloud_id,
	projects.modified_time = NOW(),
	projects.status = 'completed'
WHERE
	(
		3d_segmentations.id = :id
		OR projects.id = :project_id
	)
	AND 3d_segmentations.project_id = projects.id
	AND projects.is_deleted = false;

-- :name delete_3d_segmentation :affected
UPDATE 3d_segmentations AS s,
	projects AS p
SET p.is_deleted = true
WHERE
	s.id = :id
	AND s.project_id = p.id;
