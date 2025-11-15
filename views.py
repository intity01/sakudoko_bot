import discord
import time
import asyncio
from typing import TYPE_CHECKING, Optional

# Type checking to avoid circular import with main.py
if TYPE_CHECKING:
    from main import MyBot
    from music_manager import MusicManager

# --- Helper Functions (Simplified) ---

async def send_notify_embed(interaction: discord.Interaction, title: str, desc: str, color: int):
    embed = discord.Embed(title=title, description=desc, color=color)
    # Use followup if response is already deferred/sent
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Views ---

class RequestFirstSongView(discord.ui.View):
    """View for the initial music room message."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ขอเพลงแรก / เริ่มเล่น", style=discord.ButtonStyle.success, custom_id="request_first_song")
    async def request_first_song(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
        await interaction_btn.response.send_message("กรุณาพิมพ์ชื่อเพลงหรือวางลิงก์ในห้องนี้เพื่อเริ่มเล่นเพลงแรก!", ephemeral=True)

class MusicControlView(discord.ui.View):
    _cooldowns = {}  # user_id: last_used_time

    def __init__(self, bot: 'MyBot', logger, guild: discord.Guild, channel_id: int, server_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.logger = logger
        self.guild = guild
        self.channel_id = channel_id
        self.server_id = server_id
        # Manager is retrieved dynamically on button click to ensure it's up-to-date
        # self.manager: 'MusicManager' = self.bot.get_manager(server_id)

    def get_manager(self) -> 'MusicManager':
        """Retrieves the current MusicManager instance."""
        return self.bot.get_manager(self.server_id)

    async def _check_permission(self, interaction: discord.Interaction):
        manager = self.get_manager()
        # Check if the user is the owner or an admin
        is_owner = interaction.user.id == manager.owner_id
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_owner or is_admin):
            # Defer the response if not already done
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            await send_notify_embed(interaction, "❌ ไม่มีสิทธิ์", "คุณไม่ใช่เจ้าของห้องหรือแอดมิน", 0xff0000)
            return False
        return True

    async def _check_cooldown(self, interaction: discord.Interaction, cooldown: int = 2):
        user_id = interaction.user.id
        now = time.time()
        last = self._cooldowns.get(user_id, 0)
        if now - last < cooldown:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            await send_notify_embed(interaction, "⏳ โปรดลองใหม่อีกครั้ง", f"คุณต้องรอ {cooldown} วินาทีระหว่างการกดปุ่ม", 0xffcc00)
            return False
        self._cooldowns[user_id] = now
        return True

    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        vc = manager.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await send_notify_embed(interaction, "แจ้งเตือน", "หยุดชั่วคราว", 0xffcc00)
        else:
            await send_notify_embed(interaction, "Error", "ไม่มีเพลงที่กำลังเล่น!", 0xff0000)

    @discord.ui.button(label="▶️ Resume", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        vc = manager.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await send_notify_embed(interaction, "แจ้งเตือน", "เล่นต่อ", 0x00ff99)
        else:
            await send_notify_embed(interaction, "Error", "ไม่มีเพลงที่หยุดชั่วคราว!", 0xff0000)

    @discord.ui.button(label="🚪 Exit", style=discord.ButtonStyle.danger)
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        
        manager = self.get_manager()
        
        # Defer the response if not already done
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
            
        await manager.disconnect_and_cleanup(self.guild)
        
        # The manager instance is deleted in disconnect_and_cleanup, so we don't need to do it here
        
        await send_notify_embed(interaction, "🚪 Bot Exited & Room Deleted", "บอทหยุดเล่นและลบห้องแชทเรียบร้อยแล้ว!", 0xff0000)

    @discord.ui.button(label="⏭️ Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        
        manager = self.get_manager()
        
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
            
        channel = self.guild.get_channel(self.channel_id)
        await manager.skip_to_next(channel)
        await send_notify_embed(interaction, "แจ้งเตือน", "ข้ามเพลงแล้ว!", 0x0099ff)

    @discord.ui.button(label="🔀 Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        if manager.shuffle_queue():
            await send_notify_embed(interaction, "🔀 Shuffle Queue", "คิวเพลงถูกสุ่มใหม่แล้ว!", 0x1abc9c)
        else:
            await send_notify_embed(interaction, "Shuffle", "คิวเพลงมีน้อยเกินไปสำหรับการสุ่ม!", 0xffcc00)

    @discord.ui.button(label="🔁 Loop", style=discord.ButtonStyle.success)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        status = "เปิด" if manager.toggle_loop() else "ปิด"
        await send_notify_embed(interaction, "🔁 Loop Queue", f"Loop คิวเพลง: {status}", 0x1abc9c)

    @discord.ui.button(label="⏩ Vote Skip", style=discord.ButtonStyle.danger)
    async def vote_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_cooldown(interaction):
            return
        
        manager = self.get_manager()
        
        if manager.add_vote_skip(interaction.user.id):
            channel = self.guild.get_channel(self.channel_id)
            await manager.skip_to_next(channel)
            await send_notify_embed(interaction, "⏭️ Vote Skip", "ข้ามเพลงสำเร็จด้วยการโหวต!", 0x1abc9c)
        else:
            current, required = manager.get_vote_status()
            await send_notify_embed(interaction, "Vote Skip", f"โหวตข้ามเพลงแล้ว ({current}/{required})", 0xffcc00)

    @discord.ui.button(label="🔊 Volume +", style=discord.ButtonStyle.success)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        vc = manager.voice_client
        if vc and vc.source:
            new_vol = min(1.0, vc.source.volume + 0.1)
            vc.source.volume = new_vol
            await send_notify_embed(interaction, "🔊 Volume Up", f"ปรับเสียงเป็น {int(new_vol*100)}%", 0x1abc9c)
        else:
            await send_notify_embed(interaction, "Volume", "ไม่มีเพลงที่กำลังเล่น!", 0xff0000)

    @discord.ui.button(label="🔉 Volume -", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        vc = manager.voice_client
        if vc and vc.source:
            new_vol = max(0.0, vc.source.volume - 0.1)
            vc.source.volume = new_vol
            await send_notify_embed(interaction, "🔉 Volume Down", f"ปรับเสียงเป็น {int(new_vol*100)}%", 0x1abc9c)
        else:
            await send_notify_embed(interaction, "Volume", "ไม่มีเพลงที่กำลังเล่น!", 0xff0000)

    @discord.ui.button(label="⚙️ Filter", style=discord.ButtonStyle.primary)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction):
            return
        
        manager = self.get_manager()
        
        class FilterModal(discord.ui.Modal):
            def __init__(self, manager: 'MusicManager'):
                super().__init__(title="ตั้งค่า Filter/Effect")
                self.manager = manager
                self.filter = discord.ui.TextInput(
                    label="Filter (เช่น bass, nightcore, pitch)", 
                    placeholder=f"ปัจจุบัน: {manager.selected_filter or 'none'}", 
                    required=False
                )
                self.add_item(self.filter)
                
            async def on_submit(self, modal_interaction: discord.Interaction):
                selected_filter = self.filter.value.strip() or None
                self.manager.selected_filter = selected_filter
                
                embed = discord.Embed(title="⚙️ Filter Set", description=f"ตั้งค่า filter เป็น: {selected_filter or 'none'}", color=0x3498db)
                await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                
        await interaction.response.send_modal(FilterModal(manager))
