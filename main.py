import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from io import BytesIO

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.star import StarTools
from astrbot.core.config import AstrBotConfig
import astrbot.api.message_components as seg
from PIL import Image

# 导入 petpet 生成器
try:
    from .petpet.petpet_generator import generate_meme
except ImportError:
    # 如果无法导入，使用系统路径导入
    import sys
    import os
    petpet_path = os.path.join(os.path.dirname(__file__), 'petpet')
    if petpet_path not in sys.path:
        sys.path.append(petpet_path)
    from petpet_generator import generate_meme


@register(
    "astrbot_plugin_yikt",
    "yiktllw", 
    "yikt 多功能插件，提供 petpet 生成等功能",
    "1.0.0"
)
class YiktPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        
        # 获取配置
        self.debug_mode = config.get("debug_mode", False)
        
        # 数据存储目录
        self.data_dir = StarTools.get_data_dir("astrbot_plugin_yikt")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 插件目录
        self.plugin_dir = os.path.dirname(__file__)
        self.petpet_dir = os.path.join(self.plugin_dir, "petpet")
        
        # 支持的模板映射
        self.template_mapping = {
            "挠头": "scratch_head",
            "拍": "pat",
            "摸": "pat",
            "摸摸": "pat"
        }
        
        debug_status = "开启" if self.debug_mode else "关闭"
        logger.info(f"yikt插件初始化完成，调试模式: {debug_status}")

    def _debug_log(self, message: str):
        """输出调试信息"""
        if self.debug_mode:
            logger.info(f"[yikt调试] {message}")

    async def get_avatar(self, user_id: str) -> Optional[bytes]:
        """获取用户头像"""
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        try:
            async with aiohttp.ClientSession() as client:
                response = await client.get(avatar_url)
                response.raise_for_status()
                return await response.read()
        except Exception as e:
            self._debug_log(f"下载头像失败: {e}")
            logger.error(f"下载头像失败: {e}")
            return None

    def _extract_user_info(self, message_chain, message_text: str):
        """从消息中提取用户信息（支持@和用户名）"""
        at_users = []
        user_names = []
        
        # 提取@的用户
        for segment in message_chain:
            if hasattr(segment, 'type') and segment.type == 'at':
                if hasattr(segment, 'data') and 'qq' in segment.data:
                    at_users.append(segment.data['qq'])
        
        # 从文本中提取用户名（去除命令部分）
        import re
        # 去除命令部分，提取剩余的文本作为用户名
        text_without_command = re.sub(r'^/pet\s+\w+\s*', '', message_text).strip()
        if text_without_command and not at_users:
            user_names.append(text_without_command)
        
        self._debug_log(f"提取用户信息: @用户={at_users}, 用户名={user_names}")
        return at_users, user_names

    def get_group_id_from_session(self, session_id: str) -> str:
        """从会话ID中提取群组ID"""
        # 参考 xyxy_violence 插件的实现
        if "_" in session_id:
            group_id = session_id.split("_")[-1]  # 取最后一部分作为群组ID
            self._debug_log(f"从会话ID {session_id} 提取群组ID: {group_id}")
        else:
            group_id = session_id
            self._debug_log(f"使用完整会话ID作为群组ID: {group_id}")
        return group_id

    @filter.command("pet")
    async def pet_command(self, event: AstrMessageEvent):
        """
        /pet 模板名 @用户 - 生成 petpet 图片
        支持的模板：挠头、拍
        """
        message_chain = event.get_messages()
        message_text = event.message_str
        sender_id = event.get_sender_id()
        
        self._debug_log(f"收到pet命令: {message_text}")
        
        # 解析命令参数
        parts = message_text.split()
        if len(parts) < 2:
            yield event.plain_result("请指定模板类型！\n用法: /pet 挠头|拍 @用户\n支持的模板: 挠头、拍")
            return
        
        template_name = parts[1]
        if template_name not in self.template_mapping:
            yield event.plain_result(f"不支持的模板: {template_name}\n支持的模板: {', '.join(self.template_mapping.keys())}")
            return
        
        template_id = self.template_mapping[template_name]
        self._debug_log(f"使用模板: {template_name} -> {template_id}")
        
        # 提取目标用户信息
        at_users, user_names = self._extract_user_info(message_chain, message_text)
        
        if not at_users and not user_names:
            # 如果没有指定用户，使用发送者自己
            target_user_id = sender_id
            self._debug_log(f"未指定目标用户，使用发送者: {target_user_id}")
        else:
            # 优先使用@的用户
            if at_users:
                target_user_id = at_users[0]
                self._debug_log(f"使用@用户: {target_user_id}")
            else:
                # TODO: 这里简化处理，实际可能需要用户名到用户ID的映射
                yield event.plain_result("暂时只支持@用户，不支持用户名")
                return
        
        try:
            # 获取用户头像
            self._debug_log(f"开始获取用户 {target_user_id} 的头像")
            avatar_bytes = await self.get_avatar(str(target_user_id))
            
            if not avatar_bytes:
                # 使用默认白图
                with BytesIO() as buffer:
                    Image.new("RGB", (640, 640), (255, 255, 255)).save(buffer, format="PNG")
                    avatar_bytes = buffer.getvalue()
                self._debug_log("使用默认白图作为头像")
            
            self._debug_log(f"头像获取完成，大小: {len(avatar_bytes)} bytes")
            
            # 生成 petpet 图片
            self._debug_log(f"开始生成petpet，模板: {template_id}")
            result_bytes = await asyncio.to_thread(
                generate_meme,
                template_id,
                [avatar_bytes]  # petpet API 需要图片列表
            )
            
            if result_bytes:
                self._debug_log(f"petpet生成成功，大小: {len(result_bytes)} bytes")
                # 发送生成的图片
                yield event.chain_result([
                    seg.Image.fromBytes(result_bytes)
                ])
            else:
                self._debug_log("petpet生成失败，返回结果为空")
                yield event.plain_result("生成petpet失败")
                
        except Exception as e:
            self._debug_log(f"生成petpet时发生异常: {e}")
            logger.error(f"生成petpet失败: {e}")
            yield event.plain_result(f"生成petpet失败: {e}")

    @filter.command("pet帮助")
    async def pet_help(self, event: AstrMessageEvent):
        """显示petpet帮助信息"""
        help_text = (
            "=== yikt petpet 帮助 ===\n\n"
            "📋 指令列表：\n"
            "  /pet <模板> @用户 - 生成petpet图片\n"
            "  /pet帮助 - 显示此帮助\n\n"
            "🎨 支持的模板：\n"
            "  挠头 - 挠头动作\n"
            "  拍 - 拍头动作\n"
            "  摸 - 摸头动作\n"
            "  摸摸 - 摸头动作\n\n"
            "💡 使用示例：\n"
            "  /pet 拍 @某人\n"
            "  /pet 挠头 @某人\n\n"
            "📝 注意事项：\n"
            "  • 如果不指定用户，将使用你自己的头像\n"
            "  • 请确保有权限获取目标用户的头像\n"
        )
        yield event.plain_result(help_text)

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("yikt插件已卸载")