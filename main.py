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
from PIL import Image, ImageDraw

# 导入 petpet 生成器
try:
    from .petpet.petpet_generator import generate_meme, generate_meme_from_bytes
except ImportError: # pyright: ignore[reportUndefinedVariable]
    # 如果无法导入，使用系统路径导入
    import sys
    import os
    petpet_path = os.path.join(os.path.dirname(__file__), 'petpet')
    if petpet_path not in sys.path:
        sys.path.append(petpet_path)
    from petpet_generator import generate_meme, generate_meme_from_bytes


@register(
    "astrbot_plugin_yikt",
    "yiktllw", 
    "yikt 多功能插件，提供 petpet 生成等功能",
    "1.0.0"
)
class YiktPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context) # pyright: ignore[reportUndefinedVariable]
        
        # 获取配置
        self.debug_mode = config.get("debug_mode", False)
        self.save_probability = config.get("save_probability", 0.05)
        self.replay_probability = config.get("replay_probability", 0.02)
        self.max_messages = config.get("max_messages", 200)
        
        # 数据存储目录
        self.data_dir = StarTools.get_data_dir("astrbot_plugin_yikt")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 消息存储文件
        self.messages_file = os.path.join(self.data_dir, "saved_messages.json")
        self.saved_messages = self._load_messages()
        
        # 插件目录
        self.plugin_dir = os.path.dirname(__file__)
        self.petpet_dir = os.path.join(self.plugin_dir, "petpet")
        
        # 支持的模板映射
        self.template_mapping = {
            "挠头": "scratch_head",
            "拍": "pat",
            "摸": "petpet",
            "雪球": "roll",
        }
        
        debug_status = "开启" if self.debug_mode else "关闭"
        logger.info(f"yikt插件初始化完成，调试模式: {debug_status}")

    def _debug_log(self, message: str): # type: ignore
        """输出调试信息"""
        if self.debug_mode:
            logger.info(f"[yikt调试] {message}")

    def _load_messages(self) -> list:
        """加载保存的消息"""
        try:
            if os.path.exists(self.messages_file):
                with open(self.messages_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)
                    self._debug_log(f"加载了 {len(messages)} 条保存的消息")
                    return messages
        except Exception as e:
            self._debug_log(f"加载消息失败: {e}")
        return []

    def _save_messages(self):
        """保存消息到文件"""
        try:
            with open(self.messages_file, "w", encoding="utf-8") as f:
                json.dump(self.saved_messages, f, ensure_ascii=False, indent=2)
            self._debug_log(f"保存了 {len(self.saved_messages)} 条消息")
        except Exception as e:
            self._debug_log(f"保存消息失败: {e}")

    def _add_message(self, message_text: str, group_id: str):
        """添加消息到存储"""
        # 检查消息长度（排除过长消息）
        if len(message_text) > 100:
            return False
            
        # 检查是否是命令（以/开头）
        if message_text.strip().startswith("/"):
            return False
            
        # 检查是否已存在相同消息
        for msg in self.saved_messages:
            if msg.get("text") == message_text:
                return False
                
        # 添加新消息
        new_message = {
            "text": message_text,
            "group_id": group_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.saved_messages.append(new_message)
        
        # 如果超出最大数量，删除最旧的消息
        if len(self.saved_messages) > self.max_messages:
            self.saved_messages.pop(0)
            
        self._save_messages()
        self._debug_log(f"保存消息: {message_text[:50]}...")
        return True

    def _get_random_message(self, group_id: str = None) -> Optional[str]:
        """获取随机消息"""
        if not self.saved_messages:
            return None
            
        # 优先从同群组的消息中选择
        group_messages = [msg for msg in self.saved_messages if msg.get("group_id") == group_id] if group_id else []
        
        if group_messages:
            import random
            selected = random.choice(group_messages)
        else:
            import random
            selected = random.choice(self.saved_messages)
            
        return selected.get("text")
        """输出调试信息"""
        if self.debug_mode:
            logger.info(f"[yikt调试] {message}")

    async def get_avatar(self, user_id: str) -> Optional[bytes]: # type: ignore
        """获取用户头像"""
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        try:
            async with aiohttp.ClientSession() as client:
                response = await client.get(avatar_url)
                response.raise_for_status()
                return await response.read()
        except Exception as e: # type: ignore
            self._debug_log(f"下载头像失败: {e}")
            logger.error(f"下载头像失败: {e}")
            return None

    def make_avatar_circular(self, avatar_bytes: bytes, size: int = 640) -> bytes: # type: ignore
        """将头像处理成圆形"""
        try:
            # 打开图片
            with BytesIO(avatar_bytes) as input_buffer:
                img = Image.open(input_buffer).convert("RGBA")
            
            # 调整图片大小
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # 创建一个圆形遮罩
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            
            # 创建透明背景的输出图片
            output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            
            # 应用圆形遮罩
            output.paste(img, (0, 0))
            output.putalpha(mask)
            
            # 转换为字节
            with BytesIO() as output_buffer:
                output.save(output_buffer, format="PNG")
                return output_buffer.getvalue()
                
        except Exception as e: # type: ignore
            self._debug_log(f"处理圆形头像失败: {e}")
            logger.error(f"处理圆形头像失败: {e}")
            # 如果处理失败，返回原始字节
            return avatar_bytes

    def _extract_user_info(self, message_chain, message_text: str): # type: ignore
        """从消息中提取用户信息（支持@和用户名）"""
        at_users = []
        user_names = []
        
        # 提取@的用户
        for segment in message_chain:
            if hasattr(segment, 'type') and segment.type == 'at': # type: ignore
                if hasattr(segment, 'data') and 'qq' in segment.data: # type: ignore
                    at_users.append(segment.data['qq'])
        
        # 从文本中提取用户名（去除命令部分和@信息）
        import re
        
        # 调试信息
        self._debug_log(f"原始消息文本: '{message_text}'")
        
        # 去除命令部分和@信息，提取剩余的文本作为用户名
        text_without_command = re.sub(r'^/pet\s+\w+\s*', '', message_text).strip()
        self._debug_log(f"去除命令后: '{text_without_command}'")
        
        # 去除@信息
        text_without_at = re.sub(r'\[At:\d+\]', '', text_without_command).strip()
        self._debug_log(f"去除@信息后: '{text_without_at}'")
        
        if text_without_at and not at_users:
            user_names.append(text_without_at)
            self._debug_log(f"添加用户名: '{text_without_at}'")
        
        self._debug_log(f"提取用户信息: @用户={at_users}, 用户名={user_names}")
        return at_users, user_names

    def _parse_target_user(self, message_chain, message_text: str, sender_id: str) -> Optional[str]: # type: ignore
        """从消息中解析目标用户ID"""
        # 调试：打印消息链结构
        self._debug_log(f"消息链长度: {len(message_chain)}") # type: ignore
        for i, segment in enumerate(message_chain): # type: ignore
            self._debug_log(f"消息段 {i}: type={getattr(segment, 'type', 'Unknown')}, data={getattr(segment, 'data', {})}") # type: ignore
        
        # 首先检查是否有@用户（从消息链中提取）
        at_users = []
        for segment in message_chain:
            # 尝试多种可能的属性名
            segment_type = getattr(segment, 'type', None) # type: ignore
            if segment_type == 'at':
                # 尝试多种可能的数据格式
                data = getattr(segment, 'data', {}) # type: ignore
                if isinstance(data, dict): # type: ignore
                    qq_id = data.get('qq') or data.get('user_id') or data.get('target')
                    if qq_id:
                        at_users.append(str(qq_id)) # type: ignore
                        self._debug_log(f"从消息链找到@用户: {qq_id}")
        
        # 如果从消息链解析失败，尝试从消息文本中提取
        if not at_users:
            import re
            # 匹配 [At:数字] 格式
            at_pattern = r'\[At:(\d+)\]'
            at_matches = re.findall(at_pattern, message_text)
            if at_matches:
                at_users = at_matches
                self._debug_log(f"从消息文本找到@用户: {at_users}")
        
        self._debug_log(f"最终找到@用户: {at_users}")
        
        if at_users:
            # 优先使用@用户（这是最常见的情况）
            target_user_id = at_users[0]
            self._debug_log(f"使用@用户: {target_user_id}")
            return target_user_id
        
        # 尝试从消息文本中提取用户ID（去掉命令部分后的数字）
        import re
        # 匹配 /pet 模板名 后面的数字ID
        pattern = r'/pet\s+\w+\s+(\d+)'
        match = re.search(pattern, message_text)
        if match:
            target_user_id = match.group(1)
            self._debug_log(f"从消息文本解析出用户ID: {target_user_id}")
            return target_user_id
        
        # 没有指定用户，使用发送者自己
        self._debug_log(f"未指定目标，使用发送者: {sender_id}")
        return sender_id

    async def _get_user_id_by_name(self, user_name: str, group_id: str) -> Optional[str]: # type: ignore
        """通过用户名获取用户ID（在群组中搜索）"""
        try:
            # 尝试通过API获取群成员列表
            # 注意：这需要机器人有获取群成员列表的权限
            
            # 由于astrbot框架的API限制，我们目前无法直接获取群成员信息
            # 这里先返回None，表示暂时不支持用户名查询
            self._debug_log(f"尝试查找用户名 '{user_name}' 在群 {group_id} 中的ID")
            
            # TODO: 如果有群成员API，可以在这里实现用户名到ID的映射
            # 目前返回None表示未找到
            return None
            
        except Exception as e: # type: ignore
            self._debug_log(f"查找用户名失败: {e}")
            return None

    def get_group_id_from_session(self, session_id: str) -> str: # type: ignore
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
        /pet <模板> [目标] - 生成 petpet 图片
        
        参数:
        - template_name: 模板名称 (挠头、拍、摸、摸摸)
        目标用户通过@或消息解析自动获取
        """
        message_chain = event.get_messages()

        self._debug_log(f"原始消息字符串: {repr(event.message_str)}") # type: ignore
        self._debug_log(f"事件类型: {type(event)}") # type: ignore
        message_text = event.message_str
        sender_id = event.get_sender_id()

        # 从消息文本中解析模板名称
        parts = message_text.strip().split()
        self._debug_log(f"调试: 消息分割结果 = {parts}")
        
        # 获取模板名称 (第二个词，跳过命令名)
        template = None
        if len(parts) >= 2: # type: ignore
            template = parts[1]
        
        self._debug_log(f"收到pet命令: {message_text}, template='{template}'")
        if not template:
            templates_info = ', '.join(self.template_mapping.keys())
            yield event.plain_result("请指定模板类型！\n用法: /pet <模板> [@用户|用户ID]\n支持的模板: " + templates_info)
            return
        
        if template not in self.template_mapping:
            yield event.plain_result(f"不支持的模板: {template}\n支持的模板: {', '.join(self.template_mapping.keys())}")
            return
        
        template_id = self.template_mapping[template]
        self._debug_log(f"使用模板: {template} -> {template_id}")
        
        # 从消息中解析目标用户信息
        target_user_id = self._parse_target_user(message_chain, message_text, sender_id)
        self._debug_log(f"解析到的目标用户ID: {target_user_id}, 发送者ID: {sender_id}")
        
        # 确保有目标用户ID
        if not target_user_id:
            yield event.plain_result("无法确定目标用户，请检查输入")
            return
        
        try:
            # 获取用户头像
            # 如果解析结果是发送者自己，尝试从消息链字符串中查找AT用户
            if str(target_user_id) == str(sender_id): # type: ignore
                full_message_str = str(message_chain) # type: ignore
                import re
                # 查找数字ID模式（通常AT用户ID是长数字）
                id_pattern = r"(\d{8,})"
                ids = re.findall(id_pattern, full_message_str)
                # 过滤掉发送者ID，找到其他用户ID
                other_ids = [uid for uid in ids if uid != str(sender_id)] # type: ignore
                if other_ids:
                    target_user_id = other_ids[0]
                    self._debug_log(f"从消息链重新找到目标用户: {target_user_id}")
                self._debug_log(f"从消息链重新找到目标用户: {target_user_id}")
                self._debug_log(f"重新解析找到AT用户: {target_user_id}")
            self._debug_log(f"开始获取用户 {target_user_id} 的头像")
            avatar_bytes = await self.get_avatar(str(target_user_id)) # type: ignore
            
            if not avatar_bytes:
                # 使用默认白图
                with BytesIO() as buffer:
                    Image.new("RGB", (640, 640), (255, 255, 255)).save(buffer, format="PNG")
                    avatar_bytes = buffer.getvalue()
                self._debug_log("使用默认白图作为头像")
            
            self._debug_log(f"头像获取完成，大小: {len(avatar_bytes)} bytes") # type: ignore
            
            # 将头像处理成圆形
            self._debug_log("开始处理圆形头像")
            circular_avatar_bytes = self.make_avatar_circular(avatar_bytes)
            self._debug_log(f"圆形头像处理完成，大小: {len(circular_avatar_bytes)} bytes") # type: ignore
            
            # 生成 petpet 图片
            self._debug_log(f"开始生成petpet，模板: {template_id}")
            templates_dir = os.path.join(os.path.dirname(__file__), 'petpet', 'templates')
            result_bytes = await asyncio.to_thread(
                generate_meme_from_bytes,
                circular_avatar_bytes,
                template_id,
                None,  # text_content
                templates_dir
            )
            
            if result_bytes:
                self._debug_log(f"petpet生成成功，大小: {len(result_bytes)} bytes") # type: ignore
                # 发送生成的图片
                yield event.chain_result([
                    seg.Image.fromBytes(result_bytes)
                ])
            else:
                self._debug_log("petpet生成失败，返回结果为空")
                yield event.plain_result("生成petpet失败")
                
        except Exception as e: # type: ignore
            self._debug_log(f"生成petpet时发生异常: {e}")
            logger.error(f"生成petpet失败: {e}")
            yield event.plain_result(f"生成petpet失败: {e}")

    @filter.command("pet帮助")
    @filter.on_message
    async def on_message(self, event: AstrMessageEvent):
        """监听所有消息，进行记录和复读"""
        try:
            # 只处理群聊消息
            if not hasattr(event, "get_sender_id"):
                return
                
            message_text = event.message_str.strip()
            sender_id = event.get_sender_id()
            session_id = event.session_id
            
            # 提取群组ID
            group_id = self.get_group_id_from_session(session_id)
            
            # 跳过空消息
            if not message_text:
                return
                
            # 跳过命令消息
            if message_text.startswith("/"):
                return
                
            # 跳过过长消息
            if len(message_text) > 100:
                self._debug_log(f"消息过长，跳过: {len(message_text)}字符")
                return
                
            # 跳过纯图片或其他特殊消息
            if not message_text or message_text.isspace():
                return
                
            self._debug_log(f"处理群消息: {message_text[:50]}...")
            
            # 随机保存消息
            import random
            if random.random() < self.save_probability:
                if self._add_message(message_text, group_id):
                    self._debug_log(f"消息已保存 (概率: {self.save_probability})")
            
            # 随机复读消息
            if random.random() < self.replay_probability:
                replay_message = self._get_random_message(group_id)
                if replay_message and replay_message != message_text:
                    self._debug_log(f"触发复读 (概率: {self.replay_probability}): {replay_message[:50]}...")
                    yield event.plain_result(replay_message)
                    
        except Exception as e:
            self._debug_log(f"处理消息时发生错误: {e}")
        yield event.plain_result(help_text)
    @filter.command("yikt统计")
    async def message_stats(self, event: AstrMessageEvent):
        """显示消息记录统计"""
        total_messages = len(self.saved_messages)
        if total_messages == 0:
            yield event.plain_result("📊 消息统计\n\n暂无保存的消息")
            return
            
        # 按群组统计
        group_stats = {}
        for msg in self.saved_messages:
            group_id = msg.get("group_id", "未知")
            group_stats[group_id] = group_stats.get(group_id, 0) + 1
            
        stats_text = (
            f"📊 YiktLLW 消息统计\n\n"
            f"📝 总消息数: {total_messages}/{self.max_messages}\n"
            f"💾 保存概率: {self.save_probability * 100:.1f}%\n"
            f"🔄 复读概率: {self.replay_probability * 100:.1f}%\n\n"
            f"📈 分群统计:\n"
        )
        
        for group_id, count in list(group_stats.items())[:5]:  # 只显示前5个群
            stats_text += f"• 群{group_id[-6:]}: {count}条\n"
            
        if len(group_stats) > 5:
            stats_text += f"• ...还有{len(group_stats) - 5}个群\n"
            
        yield event.plain_result(stats_text)

    @filter.command("yikt清理")
    async def clear_messages(self, event: AstrMessageEvent):
        """清理保存的消息"""
        old_count = len(self.saved_messages)
        self.saved_messages.clear()
        self._save_messages()
        yield event.plain_result(f"🗑️ 已清理 {old_count} 条保存的消息")
        """显示petpet帮助信息"""
        help_text = (
            "=== yikt petpet 帮助 ===\n\n"
            "📋 指令列表：\n"
            "  /pet <模板> @用户 - 生成petpet图片\n"
            "  /pet <模板> 用户ID - 使用用户ID生成图片\n"
            "  /pet <模板> - 使用自己的头像生成图片\n"
            "  /pet帮助 - 显示此帮助\n\n"
            "🎨 支持的模板：\n"
            "  挠头 - 挠头动作\n"
            "  拍 - 拍头动作\n"
            "  摸 - 摸头动作\n"
            "  摸摸 - 摸头动作\n\n"
            "💡 使用示例：\n"
            "  /pet 拍 @某人\n"
            "  /pet 挠头 @某人\n"
            "  /pet 拍 1234567890\n"
            "  /pet 挠头\n\n"
            "📝 注意事项：\n"
            "  • 支持@用户、直接在命令后输入用户ID（纯数字）\n"
            "  • 如果不指定用户，将使用你自己的头像\n"
            "  • 请确保有权限获取目标用户的头像\n"
            "  • 用户ID应该紧跟在模板名称后面，如: /pet 拍 1234567890\n"
        )
        yield event.plain_result(help_text)

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("yikt插件已卸载")
    @filter.command("yikt统计")
    async def message_stats(self, event: AstrMessageEvent):
        """显示消息记录统计"""
        total_messages = len(self.saved_messages)
        if total_messages == 0:
            yield event.plain_result("📊 消息统计\n\n暂无保存的消息")
            return
            
        # 按群组统计
        group_stats = {}
        for msg in self.saved_messages:
            group_id = msg.get("group_id", "未知")
            group_stats[group_id] = group_stats.get(group_id, 0) + 1
            
        stats_text = (
            f"📊 YiktLLW 消息统计\n\n"
            f"📝 总消息数: {total_messages}/{self.max_messages}\n"
            f"💾 保存概率: {self.save_probability * 100:.1f}%\n"
            f"🔄 复读概率: {self.replay_probability * 100:.1f}%\n\n"
            f"📈 分群统计:\n"
        )
        
        for group_id, count in list(group_stats.items())[:5]:  # 只显示前5个群
            stats_text += f"• 群{group_id[-6:]}: {count}条\n"
            
        if len(group_stats) > 5:
            stats_text += f"• ...还有{len(group_stats) - 5}个群\n"
            
        yield event.plain_result(stats_text)

    @filter.command("yikt清理")
    async def clear_messages(self, event: AstrMessageEvent):
        """清理保存的消息"""
        old_count = len(self.saved_messages)
        self.saved_messages.clear()
        self._save_messages()
        yield event.plain_result(f"🗑️ 已清理 {old_count} 条保存的消息")

    @filter.command("pet帮助")
    async def pet_help(self, event: AstrMessageEvent):
        """显示pet命令帮助"""
        templates = ", ".join(self.template_mapping.keys())
        help_text = (
            "🐾 YiktLLW Pet 功能使用说明\n\n"
            "📋 命令列表：\n"
            "/pet <模板> [@用户] - 生成petpet图片\n"
            "/pet帮助 - 显示此帮助信息\n"
            "/yikt统计 - 查看消息记录统计\n"
            "/yikt清理 - 清理保存的消息\n\n"
            "🎨 支持的模板：\n" + templates + "\n\n"
            "💡 使用示例：\n"
            "/pet 挠头 @用户 - 对指定用户生成挠头动图\n"
            "/pet 拍 - 对自己生成拍拍动图"
        )
        yield event.plain_result(help_text)

