#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Petpet 表情包生成器命令行接口
"""

import argparse
import os
import sys
from petpet_generator import generate_meme, batch_generate_memes, list_available_templates


def main():
    parser = argparse.ArgumentParser(
        description="Petpet 表情包生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 生成摸头GIF
  python cli.py input.png output.gif petpet
  
  # 生成阿尼亚喜欢图片（带文字）
  python cli.py input.jpg output.png anyasuki -t "编程"
  
  # 批量生成多个表情包
  python cli.py input.png -b
  
  # 列出所有可用模板
  python cli.py --list-templates
        """
    )
    
    # 位置参数
    parser.add_argument("input", nargs="?", help="输入图片路径")
    parser.add_argument("output", nargs="?", help="输出文件路径")
    parser.add_argument("template", nargs="?", help="模板名称")
    
    # 可选参数
    parser.add_argument("-t", "--text", help="文字内容（用于支持文字的模板）")
    parser.add_argument("-b", "--batch", action="store_true", help="批量生成多个表情包")
    parser.add_argument("-o", "--output-dir", default="./output", help="批量生成时的输出目录")
    parser.add_argument("--templates-dir", default="./templates", help="模板文件夹路径")
    parser.add_argument("--list-templates", action="store_true", help="列出所有可用模板")
    
    args = parser.parse_args()
    
    # 列出模板
    if args.list_templates:
        print("📋 可用模板列表:")
        print("=" * 60)
        
        try:
            templates = list_available_templates(args.templates_dir)
            
            if not templates:
                print("❌ 未找到可用模板")
                return
            
            # 按类型分组显示
            gif_templates = []
            img_templates = []
            
            for name, info in templates.items():
                template_type = "GIF" if info["has_frames"] or info["type"].upper() == "GIF" else "IMG"
                alias_str = ", ".join(info["alias"]) if info["alias"] else "无别名"
                text_support = "支持文字" if info["has_text"] else "无文字"
                
                template_info = {
                    "name": name,
                    "alias": alias_str,
                    "text": text_support
                }
                
                if template_type == "GIF":
                    gif_templates.append(template_info)
                else:
                    img_templates.append(template_info)
            
            # 显示GIF模板
            if gif_templates:
                print("\n🎬 GIF动画模板:")
                for tmpl in sorted(gif_templates, key=lambda x: x["name"]):
                    print(f"  • {tmpl['name']:<15} - {tmpl['alias']:<20} ({tmpl['text']})")
            
            # 显示静态图片模板  
            if img_templates:
                print("\n🖼️  静态图片模板:")
                for tmpl in sorted(img_templates, key=lambda x: x["name"]):
                    print(f"  • {tmpl['name']:<15} - {tmpl['alias']:<20} ({tmpl['text']})")
            
            print(f"\n总计: {len(templates)} 个模板")
            
        except Exception as e:
            print(f"❌ 获取模板列表失败: {e}")
        
        return
    
    # 批量生成
    if args.batch:
        if not args.input:
            print("❌ 批量生成需要指定输入图片路径")
            print("使用方法: python cli.py input.png -b")
            return
        
        if not os.path.exists(args.input):
            print(f"❌ 输入图片不存在: {args.input}")
            return
        
        try:
            results = batch_generate_memes(
                args.input, 
                args.output_dir, 
                templates_dir=args.templates_dir
            )
            print(f"\n🎉 批量生成完成！生成了 {len(results)} 个表情包")
            
        except Exception as e:
            print(f"❌ 批量生成失败: {e}")
        
        return
    
    # 单个表情包生成
    if not args.input or not args.output or not args.template:
        print("❌ 单个生成需要指定输入图片、输出路径和模板名称")
        print("使用方法: python cli.py input.png output.gif template_name")
        print("或使用 -h 查看完整帮助")
        return
    
    if not os.path.exists(args.input):
        print(f"❌ 输入图片不存在: {args.input}")
        return
    
    try:
        result = generate_meme(
            args.input, 
            args.output, 
            args.template, 
            args.text,
            args.templates_dir
        )
        
        print(f"🎉 表情包生成完成: {result}")
        
        # 显示文件信息
        if os.path.exists(result):
            size = os.path.getsize(result)
            print(f"文件大小: {size:,} bytes")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")


if __name__ == "__main__":
    main()