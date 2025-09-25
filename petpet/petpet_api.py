#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Petpet 表情包生成器 - 简化API接口
提供最简单的调用方式
"""

from petpet_generator import generate_meme, batch_generate_memes, list_available_templates
import os


def make_petpet(input_path: str, output_path: str = None) -> str:
    """
    生成摸头GIF（最常用的功能）
    
    Args:
        input_path: 输入图片路径
        output_path: 输出GIF路径，None则自动生成
        
    Returns:
        生成的GIF文件路径
        
    Example:
        make_petpet("avatar.png")  # 生成 petpet.gif
        make_petpet("avatar.png", "my_petpet.gif")
    """
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"{base_name}_petpet.gif"
    
    return generate_meme(input_path, output_path, "petpet")


def make_meme(input_path: str, template: str, output_path: str = None, text: str = None) -> str:
    """
    生成指定模板的表情包
    
    Args:
        input_path: 输入图片路径
        template: 模板名称
        output_path: 输出文件路径，None则自动生成
        text: 文字内容（可选）
        
    Returns:
        生成的文件路径
        
    Example:
        make_meme("avatar.png", "pat")  # 拍头GIF
        make_meme("avatar.png", "anyasuki", text="编程")  # 阿尼亚喜欢
        make_meme("avatar.png", "perfect", "perfect.png")  # 完美图片
    """
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        # 根据模板类型决定扩展名
        gif_templates = ["petpet", "pat", "kiss", "hammer", "bite", "knock", "play"]
        
        if template in gif_templates:
            ext = "gif"
        else:
            ext = "png"
        
        if text:
            output_path = f"{base_name}_{template}_{text}.{ext}"
        else:
            output_path = f"{base_name}_{template}.{ext}"
    
    return generate_meme(input_path, output_path, template, text)


def make_collection(input_path: str, output_dir: str = None) -> list:
    """
    生成常用表情包合集
    
    Args:
        input_path: 输入图片路径
        output_dir: 输出目录，None则使用默认
        
    Returns:
        生成的文件路径列表
        
    Example:
        make_collection("avatar.png")
        make_collection("avatar.png", "./my_memes")
    """
    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = f"{base_name}_memes"
    
    # 精选常用模板
    popular_templates = [
        ("petpet", "gif"),          # 摸头
        ("pat", "gif"),             # 拍头  
        ("kiss", "gif"),            # 亲吻
        ("perfect", "png"),         # 完美
        ("dinosaur", "png"),        # 小恐龙
        ("anyasuki", "png"),        # 阿尼亚喜欢（需要文字）
    ]
    
    return batch_generate_memes(input_path, output_dir, popular_templates)


def get_templates() -> dict:
    """
    获取所有可用模板
    
    Returns:
        模板信息字典
        
    Example:
        templates = get_templates()
        for name, info in templates.items():
            print(f"{name}: {info}")
    """
    return list_available_templates()


# 便捷别名
petpet = make_petpet
meme = make_meme
collection = make_collection
templates = get_templates


if __name__ == "__main__":
    # 简单的交互式演示
    print("🎨 Petpet 表情包生成器 - 简化API")
    print("=" * 50)
    
    # 检查是否有测试图片
    test_images = ["avatar.png", "avatar.jpg", "test.png", "test.jpg"]
    test_image = None
    
    for img in test_images:
        if os.path.exists(img):
            test_image = img
            break
    
    if not test_image:
        print("📝 使用示例代码:")
        print("""
# 导入API
from petpet_api import make_petpet, make_meme, make_collection

# 生成摸头GIF  
make_petpet("avatar.png")

# 生成拍头GIF
make_meme("avatar.png", "pat")

# 生成阿尼亚喜欢图片
make_meme("avatar.png", "anyasuki", text="编程")

# 生成表情包合集
make_collection("avatar.png")
        """)
        
        print("\n💡 提示: 准备一张名为 avatar.png 或 avatar.jpg 的图片来测试")
    
    else:
        print(f"✓ 找到测试图片: {test_image}")
        print("\n开始生成演示...")
        
        try:
            # 演示摸头
            result1 = make_petpet(test_image, "demo_petpet.gif")
            print(f"✓ 摸头GIF: {result1}")
            
            # 演示完美
            result2 = make_meme(test_image, "perfect", "demo_perfect.png")
            print(f"✓ 完美图片: {result2}")
            
            # 演示阿尼亚（如果有这个模板）
            try:
                result3 = make_meme(test_image, "anyasuki", "demo_anya.png", "API测试")
                print(f"✓ 阿尼亚图片: {result3}")
            except Exception:
                print("- 跳过阿尼亚模板（模板不可用）")
            
            print("\n🎉 演示完成！")
            
        except Exception as e:
            print(f"❌ 演示失败: {e}")
    
    print(f"\n📚 可用函数:")
    print("- make_petpet(input_path, output_path=None)")
    print("- make_meme(input_path, template, output_path=None, text=None)")
    print("- make_collection(input_path, output_dir=None)")
    print("- get_templates()")