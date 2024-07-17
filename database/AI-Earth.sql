/* 对话信息 */
CREATE TABLE `conversations` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`messages` JSON,
	`project_id` INT NOT NULL UNIQUE,
	PRIMARY KEY(`id`)
) COMMENT='对话信息';


CREATE TABLE `objects` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	-- minio对象名
	`name` VARCHAR(255) COMMENT 'minio对象名',
	`etag` VARCHAR(255),
	`created_time` DATETIME,
	`updated_time` DATETIME DEFAULT NOW() ON UPDATE NOW(),
	`modified_time` DATETIME,
	-- 文件的mime类型
	`content_type` VARCHAR(255) COMMENT '文件的mime类型',
	-- minio桶中保存的对象的目录路径
	`folders` VARCHAR(255) COMMENT 'minio桶中保存的对象的目录路径',
	-- 对象tags, https://min.io/docs/minio/linux/reference/minio-mc/mc-tag.html
	`tags` JSON COMMENT '对象tags, https://min.io/docs/minio/linux/reference/minio-mc/mc-tag.html',
	`type` ENUM('image', 'pointcloud'),
	-- 原始上传的名称
	`origin_name` VARCHAR(255) COMMENT '原始上传的名称',
	`origin_type` ENUM('user', 'system', 'thumbnail', 'mask_svg') DEFAULT 'user',
	`size` INT,
	`thumbnail_id` INT UNIQUE,
	`versions` INT DEFAULT 1,
	`is_deleted` BOOLEAN DEFAULT false,
	PRIMARY KEY(`id`)
);


/* 项目 */
CREATE TABLE `projects` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`name` VARCHAR(255),
	`created_time` DATETIME DEFAULT NOW(),
	`updated_time` DATETIME DEFAULT NOW() ON UPDATE NOW(),
	`modified_time` DATETIME DEFAULT NOW(),
	-- 遥感影像解译,地物分类提取,水环境污染监测,流域变化检测
	`type` ENUM('2d_change_detection', '2d_detection', '2d_segmentation', '3d_segmentation', 'conversation') COMMENT '遥感影像解译,地物分类提取,水环境污染监测,流域变化检测',
	-- 封面缩略图的id
	`cover_image_id` INT COMMENT '封面缩略图的id',
	`is_deleted` BOOLEAN DEFAULT false,
	-- 项目状态
	`status` ENUM('waiting', 'running', 'completed') DEFAULT 'waiting' COMMENT '项目状态',
	PRIMARY KEY(`id`)
) COMMENT='项目';


CREATE TABLE `images` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`object_id` INT NOT NULL UNIQUE,
	-- 图片的通道数量
	`channel_count` INT DEFAULT 3 COMMENT '图片的通道数量',
	-- 图片的高
	`height` INT COMMENT '图片的高',
	-- 图片的宽
	`width` INT COMMENT '图片的宽',
	-- 位深，默认RGB为24位
	`bit_depth` INT DEFAULT 24 COMMENT '位深，默认RGB为24位',
	PRIMARY KEY(`id`)
);


CREATE TABLE `pointclouds` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`object_id` INT NOT NULL UNIQUE,
	-- 点云文件的点数量
	`point_count` INT COMMENT '点云文件的点数量',
	PRIMARY KEY(`id`)
);


CREATE TABLE `2d_change_detections` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`project_id` INT NOT NULL UNIQUE,
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
	`project_id` INT NOT NULL UNIQUE,
	PRIMARY KEY(`id`)
);


CREATE TABLE `2d_segmentations` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`image_id` INT,
	`mask_image_id` INT,
	`project_id` INT NOT NULL UNIQUE,
	`plot_image_id` INT UNIQUE,
	`result` JSON,
	-- mask svg图片id
	`mask_svg_id` INT UNIQUE COMMENT 'mask svg图片id',
	PRIMARY KEY(`id`)
);


CREATE TABLE `2d_detections` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`image_id` INT,
	`result` JSON,
	`project_id` INT NOT NULL UNIQUE,
	`plot_image_id` INT,
	`video_id` INT,
	`plot_video_id` INT,
	PRIMARY KEY(`id`)
);


CREATE TABLE `conversation_images` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`conversation_id` INT,
	`image_id` INT,
	PRIMARY KEY(`id`)
);


CREATE TABLE `videos` (
	`id` INT NOT NULL AUTO_INCREMENT UNIQUE,
	`object_id` INT UNIQUE,
	-- 视频时长
	`duration` TIME COMMENT '视频时长',
	-- 视频编码格式
	`codec` VARCHAR(255) COMMENT '视频编码格式',
	-- 视频容器格式
	`container` VARCHAR(255) COMMENT '视频容器格式',
	PRIMARY KEY(`id`)
);


-- ALTER TABLE `images`
-- ADD FOREIGN KEY(`object_id`) REFERENCES `objects`(`id`)
-- ON UPDATE CASCADE ON DELETE CASCADE;
-- ALTER TABLE `pointclouds`
-- ADD FOREIGN KEY(`object_id`) REFERENCES `objects`(`id`)
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
-- ALTER TABLE `conversation_images`
-- ADD FOREIGN KEY(`image_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `conversation_images`
-- ADD FOREIGN KEY(`conversation_id`) REFERENCES `conversations`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `conversations`
-- ADD FOREIGN KEY(`project_id`) REFERENCES `projects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `objects`
-- ADD FOREIGN KEY(`thumbnail_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_segmentations`
-- ADD FOREIGN KEY(`mask_svg_id`) REFERENCES `images`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `videos`
-- ADD FOREIGN KEY(`object_id`) REFERENCES `objects`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_detections`
-- ADD FOREIGN KEY(`video_id`) REFERENCES `videos`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
-- ALTER TABLE `2d_detections`
-- ADD FOREIGN KEY(`plot_video_id`) REFERENCES `videos`(`id`)
-- ON UPDATE NO ACTION ON DELETE NO ACTION;
