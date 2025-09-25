#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Petpet 模板表情包生成器
使用模板配置文件和原始图像生成表情包
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any
import math


class PetpetGenerator:
    """Petpet表情包生成器"""
    
    def __init__(self, templates_path: str = "./templates"):
        """
        初始化生成器
        
        Args:
            templates_path: 模板文件夹路径
        """
        self.templates_path = templates_path
        self.supported_formats = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"]
    
    def load_avatar_auto(self, base_path: str = "avatar") -> Image.Image:
        """
        自动加载头像文件，支持多种格式
        
        Args:
            base_path: 基础文件名（不含扩展名）
            
        Returns:
            PIL Image对象
        """
        for ext in self.supported_formats:
            file_path = base_path + ext
            if os.path.exists(file_path):
                print(f"✓ 找到头像文件: {file_path}")
                avatar = Image.open(file_path)
                
                # 确保图像为RGBA模式以支持透明度
                if avatar.mode != "RGBA":
                    avatar = avatar.convert("RGBA")
                
                return avatar
        
        raise FileNotFoundError(f"未找到头像文件！支持格式：{', '.join(self.supported_formats)}")
    
    def load_avatar_from_path(self, file_path: str) -> Image.Image:
        """
        从指定路径加载头像文件
        
        Args:
            file_path: 头像文件路径
            
        Returns:
            PIL Image对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"头像文件不存在: {file_path}")
        
        avatar = Image.open(file_path)
        
        # 确保图像为RGBA模式以支持透明度
        if avatar.mode != "RGBA":
            avatar = avatar.convert("RGBA")
        
        print(f"✓ 加载头像: {file_path} ({avatar.size[0]}x{avatar.size[1]})")
        return avatar
        
    def load_template_config(self, template_name: str) -> Dict[str, Any]:
        """
        加载模板配置文件
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板配置字典
        """
        template_dir = os.path.join(self.templates_path, template_name)
        
        # 尝试加载 data.json (API v0) 或 template.json (API v100+)
        for config_file in ["data.json", "template.json"]:
            config_path = os.path.join(template_dir, config_file)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        raise FileNotFoundError(f"未找到模板配置文件: {template_name}")
    
    def load_template_frames(self, template_name: str) -> List[Image.Image]:
        """
        加载模板帧图像
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板帧图像列表
        """
        template_dir = os.path.join(self.templates_path, template_name)
        frames = []
        
        # 按数字顺序加载帧
        frame_index = 0
        while True:
            frame_path = os.path.join(template_dir, f"{frame_index}.png")
            if not os.path.exists(frame_path):
                break
            
            frame = Image.open(frame_path).convert("RGBA")
            frames.append(frame)
            frame_index += 1
        
        if not frames:
            raise FileNotFoundError(f"未找到模板帧文件: {template_name}")
        
        return frames
    
    def resize_avatar(self, avatar: Image.Image, size: Tuple[int, int], 
                     fit_mode: str = "FILL") -> Image.Image:
        """
        调整头像尺寸
        
        Args:
            avatar: 原始头像图像
            size: 目标尺寸 (width, height)
            fit_mode: 适配模式 FILL/COVER/FIT
            
        Returns:
            调整后的头像图像
        """
        if fit_mode.upper() == "COVER":
            # 保持比例，裁剪多余部分
            avatar_ratio = avatar.width / avatar.height
            target_ratio = size[0] / size[1]
            
            if avatar_ratio > target_ratio:
                # 头像更宽，以高度为准
                new_height = size[1]
                new_width = int(new_height * avatar_ratio)
            else:
                # 头像更高，以宽度为准
                new_width = size[0]
                new_height = int(new_width / avatar_ratio)
            
            resized = avatar.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 居中裁剪
            left = (new_width - size[0]) // 2
            top = (new_height - size[1]) // 2
            cropped = resized.crop((left, top, left + size[0], top + size[1]))
            return cropped
        
        elif fit_mode.upper() == "FIT":
            # 保持比例，不裁剪
            avatar.thumbnail(size, Image.Resampling.LANCZOS)
            # 创建透明背景
            result = Image.new("RGBA", size, (0, 0, 0, 0))
            # 居中粘贴
            x = (size[0] - avatar.width) // 2
            y = (size[1] - avatar.height) // 2
            result.paste(avatar, (x, y))
            return result
        
        else:  # FILL - 直接拉伸
            return avatar.resize(size, Image.Resampling.LANCZOS)
    
    def make_round_avatar(self, avatar: Image.Image) -> Image.Image:
        """
        将头像制作成圆形
        
        Args:
            avatar: 头像图像
            
        Returns:
            圆形头像图像
        """
        size = avatar.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        
        result = Image.new("RGBA", size, (0, 0, 0, 0))
        result.paste(avatar, (0, 0))
        result.putalpha(mask)
        return result
    
    def generate_gif(self, avatar_image: Image.Image, template_name: str, 
                    output_path: str = None, **kwargs) -> str:
        """
        生成GIF表情包
        
        Args:
            avatar_image: 用户头像图像
            template_name: 模板名称
            output_path: 输出路径，None则自动生成
            **kwargs: 其他参数（如文字内容）
            
        Returns:
            生成的GIF文件路径
        """
        # 加载模板配置和帧
        config = self.load_template_config(template_name)
        template_frames = self.load_template_frames(template_name)
        
        if output_path is None:
            output_path = f"{template_name}_output.gif"
        
        # 确保头像为RGBA模式
        if avatar_image.mode != "RGBA":
            avatar_image = avatar_image.convert("RGBA")
        
        result_frames = []
        
        # 处理每一帧
        for i, template_frame in enumerate(template_frames):
            frame = template_frame.copy()
            
            # 处理头像配置
            if "avatar" in config and config["avatar"]:
                avatar_config = config["avatar"][0]  # 取第一个头像配置
                positions = avatar_config.get("pos", [])
                
                if positions:
                    # 获取当前帧的位置（循环使用）
                    pos = positions[i % len(positions)]
                    x, y, w, h = pos
                    
                    # 调整头像尺寸
                    resized_avatar = self.resize_avatar(
                        avatar_image, 
                        (w, h), 
                        avatar_config.get("fit", "FILL")
                    )
                    
                    # 如果需要圆形头像
                    if avatar_config.get("round", False):
                        resized_avatar = self.make_round_avatar(resized_avatar)
                    
                    # 粘贴头像（支持PNG透明度）
                    if avatar_config.get("avatarOnTop", False):
                        # 头像在模板上方
                        temp_frame = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                        temp_frame.paste(resized_avatar, (x, y), resized_avatar)
                        frame = Image.alpha_composite(temp_frame, frame)
                    else:
                        # 头像在模板下方，使用alpha通道进行合成
                        frame.paste(resized_avatar, (x, y), resized_avatar)
            
            result_frames.append(frame)
        
        # 保存GIF
        if result_frames:
            # 获取延迟时间，默认60ms
            delay = config.get("delay", 60)
            
            result_frames[0].save(
                output_path,
                save_all=True,
                append_images=result_frames[1:],
                duration=delay,
                loop=0,
                optimize=True
            )
        
        return output_path
    
    def generate_static_image(self, avatar_image: Image.Image, template_name: str,
                            output_path: str = None, text_content: str = None) -> str:
        """
        生成静态图片表情包
        
        Args:
            avatar_image: 用户头像图像
            template_name: 模板名称
            output_path: 输出路径，None则自动生成
            text_content: 文字内容
            
        Returns:
            生成的图片文件路径
        """
        # 加载模板配置和帧
        config = self.load_template_config(template_name)
        template_frames = self.load_template_frames(template_name)
        
        if output_path is None:
            output_path = f"{template_name}_output.png"
        
        # 使用第一帧作为基础
        result_image = template_frames[0].copy()
        
        # 确保头像为RGBA模式
        if avatar_image.mode != "RGBA":
            avatar_image = avatar_image.convert("RGBA")
        
        # 处理头像配置
        if "avatar" in config and config["avatar"]:
            avatar_config = config["avatar"][0]
            pos = avatar_config.get("pos")
            
            if pos:
                if isinstance(pos[0], list):
                    # 多帧位置，取第一帧
                    x, y, w, h = pos[0]
                else:
                    # 单个位置
                    x, y, w, h = pos
                
                # 调整头像尺寸
                resized_avatar = self.resize_avatar(
                    avatar_image, 
                    (w, h), 
                    avatar_config.get("fit", "COVER")
                )
                
                # 如果需要圆形头像
                if avatar_config.get("round", False):
                    resized_avatar = self.make_round_avatar(resized_avatar)
                
                # 粘贴头像（支持PNG透明度）
                if avatar_config.get("avatarOnTop", False):
                    temp_frame = Image.new("RGBA", result_image.size, (0, 0, 0, 0))
                    temp_frame.paste(resized_avatar, (x, y), resized_avatar)
                    result_image = Image.alpha_composite(temp_frame, result_image)
                else:
                    # 使用alpha通道进行透明合成
                    result_image.paste(resized_avatar, (x, y), resized_avatar)
        
        # 处理文字配置
        if "text" in config and config["text"] and text_content:
            text_config = config["text"][0]
            
            try:
                # 尝试加载字体
                font_name = text_config.get("font", "MiSans")
                font_size = text_config.get("size", 40)
                font_path = os.path.join(self.templates_path, "fonts", f"{font_name}-Bold.ttf")
                
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.load_default()
                
                # 处理文字内容中的占位符
                text = text_config.get("text", "$txt1")
                if "$txt1" in text:
                    text = text.replace("$txt1", text_content)
                
                # 绘制文字
                draw = ImageDraw.Draw(result_image)
                
                pos = text_config.get("pos", [100, 100])
                if len(pos) >= 2:
                    x, y = pos[0], pos[1]
                    color = text_config.get("color", "#000000")
                    
                    draw.text((x, y), text, font=font, fill=color)
            
            except Exception as e:
                print(f"绘制文字时出错: {e}")
        
        # 保存图片
        result_image.save(output_path, "PNG")
        return output_path


def generate_meme(input_image_path: str, output_path: str, template_name: str, 
                 text_content: str = None, templates_dir: str = "./templates") -> str:
    """
    外部调用接口：生成表情包
    
    Args:
        input_image_path: 输入图片路径 (支持PNG、JPG、WebP等多种格式)
        output_path: 输出文件路径 (.gif 或 .png/.jpg)
        template_name: 模板名称 (如 "petpet", "pat", "anyasuki" 等)
        text_content: 文字内容 (用于支持文字的模板，可选)
        templates_dir: 模板文件夹路径 (默认 "./templates")
        
    Returns:
        生成的文件路径
        
    Example:
        # 生成摸头GIF
        generate_meme("avatar.png", "output.gif", "petpet")
        
        # 生成阿尼亚喜欢图片
        generate_meme("avatar.jpg", "output.png", "anyasuki", "编程")
        
        # 生成完美图片
        generate_meme("avatar.webp", "perfect.png", "perfect")
    """
    try:
        # 初始化生成器
        generator = PetpetGenerator(templates_dir)
        
        # 加载输入图片
        if not os.path.exists(input_image_path):
            raise FileNotFoundError(f"输入图片不存在: {input_image_path}")
        
        avatar = generator.load_avatar_from_path(input_image_path)
        
        # 根据输出文件扩展名确定生成类型
        output_ext = os.path.splitext(output_path)[1].lower()
        
        if output_ext == ".gif":
            # 生成GIF动画
            result = generator.generate_gif(avatar, template_name, output_path)
        else:
            # 生成静态图片
            result = generator.generate_static_image(avatar, template_name, output_path, text_content)
        
        print(f"✓ 表情包生成成功: {result}")
        return result
        
    except Exception as e:
        error_msg = f"❌ 生成表情包失败: {e}"
        print(error_msg)
        raise Exception(error_msg)


def batch_generate_memes(input_image_path: str, output_dir: str = "./output", 
                        templates: list = None, templates_dir: str = "./templates") -> list:
    """
    批量生成表情包
    
    Args:
        input_image_path: 输入图片路径
        output_dir: 输出文件夹路径
        templates: 要生成的模板列表，None则使用默认列表
        templates_dir: 模板文件夹路径
        
    Returns:
        生成的文件路径列表
        
    Example:
        # 使用默认模板批量生成
        batch_generate_memes("avatar.png")
        
        # 指定模板列表
        batch_generate_memes("avatar.png", "./my_output", ["petpet", "pat", "perfect"])
    """
    if templates is None:
        # 默认模板列表（常用的几个）
        templates = [
            ("petpet", "gif"),      # 摸头
            ("pat", "gif"),         # 拍头
            ("kiss", "gif"),        # 亲吻
            ("perfect", "png"),     # 完美
            ("anyasuki", "png"),    # 阿尼亚喜欢
            ("dinosaur", "png"),    # 小恐龙
        ]
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    results = []
    failed = []
    
    print(f"🚀 开始批量生成表情包...")
    print(f"输入图片: {input_image_path}")
    print(f"输出目录: {output_dir}")
    print(f"模板数量: {len(templates)}")
    print("-" * 50)
    
    for i, template_info in enumerate(templates, 1):
        if isinstance(template_info, tuple):
            template_name, file_ext = template_info
            text_content = None
        elif isinstance(template_info, dict):
            template_name = template_info["name"]
            file_ext = template_info.get("ext", "png")
            text_content = template_info.get("text", None)
        else:
            template_name = template_info
            file_ext = "png"  # 默认PNG
            text_content = None
        
        try:
            # 生成输出文件名
            if text_content:
                output_filename = f"{template_name}_{text_content}.{file_ext}"
            else:
                output_filename = f"{template_name}.{file_ext}"
            
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"[{i}/{len(templates)}] 生成 {template_name}...")
            
            # 生成表情包
            result = generate_meme(input_image_path, output_path, template_name, text_content, templates_dir)
            results.append(result)
            
        except Exception as e:
            error_info = f"{template_name}: {e}"
            failed.append(error_info)
            print(f"❌ {error_info}")
    
    print("-" * 50)
    print(f"✓ 批量生成完成!")
    print(f"成功: {len(results)} 个")
    print(f"失败: {len(failed)} 个")
    
    if failed:
        print("\n失败列表:")
        for error in failed:
            print(f"  - {error}")
    
    return results


def list_available_templates(templates_dir: str = "./templates") -> dict:
    """
    列出可用的模板
    
    Args:
        templates_dir: 模板文件夹路径
        
    Returns:
        模板信息字典
        
    Example:
        templates = list_available_templates()
        for name, info in templates.items():
            print(f"{name}: {info['alias']}")
    """
    generator = PetpetGenerator(templates_dir)
    templates_info = {}
    
    # 遍历模板目录
    if not os.path.exists(templates_dir):
        return templates_info
    
    for item in os.listdir(templates_dir):
        template_path = os.path.join(templates_dir, item)
        
        if os.path.isdir(template_path) and item != "fonts":
            try:
                # 尝试加载模板配置
                config = generator.load_template_config(item)
                
                # 提取模板信息
                templates_info[item] = {
                    "type": config.get("type", "Unknown"),
                    "alias": config.get("alias", []),
                    "has_text": bool(config.get("text", [])),
                    "has_frames": len(generator.load_template_frames(item)) > 1
                }
                
            except Exception:
                # 如果加载失败，跳过这个模板
                continue
    
    return templates_info


def main():
    """示例用法"""
    # 初始化生成器
    generator = PetpetGenerator("./templates")
    
    # 示例1: 生成摸头GIF
    try:
        # 自动加载头像文件（支持PNG、JPG等多种格式）
        avatar = generator.load_avatar_auto("avatar")
        
        # 生成摸头GIF
        output_gif = generator.generate_gif(avatar, "petpet", "摸头.gif")
        print(f"✓ 生成摸头GIF: {output_gif}")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    
    # 示例2: 生成阿尼亚喜欢静态图
    try:
        
        output_img = generator.generate_static_image(
            avatar, 
            "anyasuki", 
            "阿尼亚喜欢.png",
            text_content="编程"
        )
        print(f"✓ 生成阿尼亚喜欢图片: {output_img}")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
    
    # 示例3: 批量生成多个模板
    templates_to_generate = ["pat", "kiss", "hammer", "perfect"]
    
    try:
        
        for template in templates_to_generate:
            try:
                if template in ["pat", "kiss", "hammer"]:
                    # GIF模板
                    output_path = generator.generate_gif(avatar, template, f"{template}.gif")
                    print(f"✓ 生成 {template} GIF: {output_path}")
                else:
                    # 静态图片模板
                    output_path = generator.generate_static_image(avatar, template, f"{template}.png")
                    print(f"✓ 生成 {template} 图片: {output_path}")
                    
            except Exception as e:
                print(f"❌ 生成 {template} 时出错: {e}")
                
    except Exception as e:
        print(f"❌ 批量生成失败: {e}")


if __name__ == "__main__":
    main()