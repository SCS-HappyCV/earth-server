from pathlib import Path

import ffmpeg
from loguru import logger


def get_video_info(video_path):
    probe = ffmpeg.probe(video_path)
    video_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
    )

    if video_stream is None:
        print("No video stream found")
        return None

    return {
        "duration": float(probe["format"]["duration"]),
        "codec": video_stream["codec_name"],
        "container": probe["format"]["format_name"],
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
    }


def convert_video(input_path: str | Path, output_path: str | Path, codec="av1"):
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        format = output_path.suffix[1:]

        stream = ffmpeg.input(str(input_path))

        if (format in ["mp4", "webm"]) and codec == "av1":
            stream = ffmpeg.output(stream, str(output_path), vcodec="libaom-av1")
        elif format == "mp4" and codec == "avc":
            stream = ffmpeg.output(stream, str(output_path), vcodec="libx264")
        else:
            msg = "不支持的格式或编解码器组合"
            raise ValueError(msg)

        ffmpeg.run(stream)
        logger.debug(f"转换成功: {output_path}")
    except ffmpeg.Error as e:
        logger.debug(f"转换失败: {e.stderr.decode()}")


# 使用示例
if __name__ == "__main__":
    input_file = "/root/autodl-tmp/Zhaoyibei/2D_seg/yolo_det/test.mp4"
    output_file = "/root/autodl-tmp/Zhaoyibei/2D_seg/yolo_det/test1.mp4"
    convert_video(input_file, output_file, codec="avc")
