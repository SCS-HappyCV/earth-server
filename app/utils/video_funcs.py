import ffmpeg


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
