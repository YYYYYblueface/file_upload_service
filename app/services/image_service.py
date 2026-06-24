from pathlib import Path

from PIL import Image

from app.config import IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, IMAGE_QUALITY


def compress_image(input_path: str, output_path: str | None = None) -> str:
    """
    压缩图片：缩小尺寸 + 降低质量
    返回压缩后的文件路径
    """
    if output_path is None:
        output_path = input_path

    img = Image.open(input_path)

    # 仅对超尺寸图片进行缩放
    if img.width > IMAGE_MAX_WIDTH or img.height > IMAGE_MAX_HEIGHT:
        img.thumbnail((IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT), Image.LANCZOS)

    # 确保输出路径目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 转换为RGB（避免PNG RGBA模式保存为JPEG时出错）
    if img.mode in ("RGBA", "P", "LA"):
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = rgb_img

    img.save(output_path, quality=IMAGE_QUALITY, optimize=True)
    return output_path