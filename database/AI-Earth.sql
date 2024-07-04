/* 对话信息 */
CREATE TABLE `conversations` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`image_id` INT,
	`messages` JSON,
	`project_id` INT,
	`is_deleted` BOOLEAN DEFAULT false,
	PRIMARY KEY(`id`)
) COMMENT='对话信息';

CREATE TABLE `objects` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	-- minio对象名
	`name` VARCHAR(255) COMMENT 'minio对象名',
	`etag` VARCHAR(255),
	`modified_time` DATETIME,
	`size` INT,
	`versions` INT DEFAULT 1,
	-- 文件的mime类型
	`content_type` VARBINARY(255) COMMENT '文件的mime类型',
	-- minio桶中保存的对象的目录路径
	`folders` VARCHAR(255) COMMENT 'minio桶中保存的对象的目录路径',
	-- 对象tags, https://min.io/docs/minio/linux/reference/minio-mc/mc-tag.html
	`tags` JSON COMMENT '对象tags, https://min.io/docs/minio/linux/reference/minio-mc/mc-tag.html',
	`is_deleted` BOOLEAN DEFAULT false,
	-- 原始上传的名称
	`origin_name` VARCHAR(255) COMMENT '原始上传的名称',
	PRIMARY KEY(`id`)
);

/* 项目 */
CREATE TABLE `projects` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`name` VARCHAR(255),
	`created_time` DATETIME DEFAULT NOW(),
	`updated_time` DATETIME DEFAULT NOW() ON UPDATE NOW(),
	`is_deleted` BOOLEAN DEFAULT false,
	-- 遥感影像解译,地物分类提取,水环境污染监测,流域变化检测
	`type` ENUM("2d_change_detection", "2d_detection", "2d_segmentation", "3d_segmentation") COMMENT '遥感影像解译,地物分类提取,水环境污染监测,流域变化检测',
	-- 封面缩略图的id
	`cover_image_id` INT COMMENT '封面缩略图的id',
	PRIMARY KEY(`id`)
) COMMENT='项目';

CREATE TABLE `images` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`object_id` INT,
	-- 图片的通道数量
	`channel_count` INT DEFAULT 3 COMMENT '图片的通道数量',
	-- 图片的高
	`height` INT COMMENT '图片的高',
	-- 图片的宽
	`width` INT COMMENT '图片的宽',
	PRIMARY KEY(`id`)
);

CREATE TABLE `pointclouds` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`object_id` INT,
	-- 点云文件的点数量
	`point_count` INT COMMENT '点云文件的点数量',
	PRIMARY KEY(`id`)
);

CREATE TABLE `2d_change_detections` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`project_id` INT,
	`image1_id` INT,
	`image2_id` INT,
	`mask_image_id` INT,
	`result` JSON,
	`plot_image_id` INT,
	PRIMARY KEY(`id`)
);

CREATE TABLE `3d_segmentations` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`pointcloud_id` INT,
	`result_pointcloud_id` INT,
	`project_id` INT,
	PRIMARY KEY(`id`)
);

CREATE TABLE `2d_segmentations` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`image_id` INT,
	`mask_image_id` INT,
	`project_id` INT,
	`plot_image_id` INT,
	`result` JSON,
	PRIMARY KEY(`id`)
);

CREATE TABLE `2d_detections` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`image_id` INT,
	`result` JSON,
	`project_id` INT,
	`plot_image_id` INT,
	PRIMARY KEY(`id`)
);

-- ALTER TABLE `images`
-- ADD FOREIGN KEY(`object_id`) REFERENCES `objects`(`id`)
-- ON UPDATE CASCADE ON DELETE CASCADE;
-- ALTER TABLE `pointclouds`
-- ADD FOREIGN KEY(`object_id`) REFERENCES `objects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `conversations`
-- ADD FOREIGN KEY(`image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `conversations`
-- ADD FOREIGN KEY(`project_id`) REFERENCES `projects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_change_detections`
-- ADD FOREIGN KEY(`project_id`) REFERENCES `projects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_change_detections`
-- ADD FOREIGN KEY(`image1_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_change_detections`
-- ADD FOREIGN KEY(`mask_image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_change_detections`
-- ADD FOREIGN KEY(`image2_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `3d_segmentations`
-- ADD FOREIGN KEY(`pointcloud_id`) REFERENCES `pointclouds`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `3d_segmentations`
-- ADD FOREIGN KEY(`result_pointcloud_id`) REFERENCES `pointclouds`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_segmentations`
-- ADD FOREIGN KEY(`image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_segmentations`
-- ADD FOREIGN KEY(`mask_image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_detections`
-- ADD FOREIGN KEY(`image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_detections`
-- ADD FOREIGN KEY(`project_id`) REFERENCES `projects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_segmentations`
-- ADD FOREIGN KEY(`project_id`) REFERENCES `projects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `3d_segmentations`
-- ADD FOREIGN KEY(`project_id`) REFERENCES `projects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_segmentations`
-- ADD FOREIGN KEY(`plot_image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_detections`
-- ADD FOREIGN KEY(`plot_image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_change_detections`
-- ADD FOREIGN KEY(`plot_image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `projects`
-- ADD FOREIGN KEY(`cover_image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;