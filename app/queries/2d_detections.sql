-- :name get_2d_detection :one
SELECT
	2d_det.*,
	p.name,
	p.created_time,
	p.updated_time,
	p.modified_time,
	p.type,
	p.cover_image_id,
	p.status
FROM 2d_detections AS 2d_det, projects AS p
WHERE
	(2d_det.id = :id OR p.id = :project_id)
	AND 2d_det.project_id = p.id
	AND p.is_deleted = false;

-- :name create_2d_detection :insert
INSERT INTO 2d_detections (image_id, video_id, project_id)
VALUES (:image_id, :video_id, :project_id);

-- :name delete_2d_detection :affected
UPDATE 2d_detections AS d,
	projects AS p
SET p.is_deleted = true
WHERE
	d.id = :id
	AND d.project_id = p.id;

-- :name delete_2d_detections_by_project_id :affected
UPDATE 2d_detections
SET is_deleted = true
WHERE project_id = :project_id;

-- :name complete_2d_detection :affected
UPDATE 2d_detections AS 2d_det, projects AS p
SET
	2d_det.plot_image_id = :plot_image_id,
	2d_det.plot_video_id = :plot_video_id,
	p.modified_time = NOW(),
	p.status = 'completed'
WHERE
	(
		2d_det.id = :id
		OR p.id = :project_id
	)
	AND 2d_det.project_id = p.id
	AND p.is_deleted = false;
