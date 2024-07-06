-- :name get_3d_segmentation_by_project_id :one
SELECT *
FROM 3d_segmentations
WHERE project_id = :project_id;

-- :name get_3d_segmentation_by_id :one
SELECT *
FROM 3d_segmentations
WHERE id = :id;

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

-- :name delete_3d_segmentation :affected
UPDATE 3d_segmentations AS s,
	projects AS p
SET p.is_deleted = true
WHERE
	s.id = :id
	AND s.project_id = p.id;
