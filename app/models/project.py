from enum import Enum

ProjectType = Enum(
    "ProjectType",
    ("2d_change_detection", "2d_detection", "2d_segmentation", "3d_segmentation"),
)
