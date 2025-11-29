"""
Simple Music Control View for buttons
"""
import discord
import time
import logging

logger = logging.getLogger('discord_bot')

class RequestFirstSongView(discord.ui.View):
    """Simple view to prompt users to request their first song"""
    def __init__(self):
        super().__init__(timeout=None)

class MusicControlView(discord.ui.View):
    """Simplified view for music controls"""
    _cooldowns = {}  # user_id: last_used_time

    def __init__(self, bot, logger_instance, guild: discord.Guild, channel_id: int, server_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.logger = logger_instance
        self.guild = guild
        self.channel_id = channel_id
        self.server_id = server_id

    def get_manager(self):
        """Retrieves the current MusicManager instance."""
        return self.bot.get_manager(self.server_id)

    async def _check_permission(self, interaction: discord.Interaction):
        manager = self.get_manager()
        is_owner = interaction.user.id == manager.owner_id
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_owner or is_admin):
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            embed = discord.Embed(title="❌ ไม่มีสิทธิ์", description="คุณไม่ใช่เจ้าของห้องหรือแอดมิน", color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return False
        return True

    async def _check_cooldown(self, interaction: discord.Interaction, cooldown: int = 2):
        user_id = interaction.user.id
        now = time.time()
        last = self._cooldowns.get(user_id, 0)
        if now - last < cooldown:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            embed = discord.Embed(title="⏳ โปรดลองใหม่อีกครั้ง", description=f"คุณต้องรอ {cooldown} วินาทีระหว่างการกดปุ่ม", color=0xffcc00)
            await interaction.followup.send(embed=embed, ephemeral=True)
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
            embed = discord.Embed(title="แจ้งเตือน", description="หยุดชั่วคราว", color=0xffcc00)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Error", description="ไม่มีเพลงที่กำลังเล่น!", color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="▶️ Resume", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        manager = self.get_manager()
        vc = manager.voice_client
        if vc and vc.is_paused():
            vc.resume()
            embed = discord.Embed(title="แจ้งเตือน", description="เล่นต่อ", color=0x00ff99)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Error", description="ไม่มีเพลงที่หยุดชั่วคราว!", color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        
        manager = self.get_manager()
        
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
            
        channel = self.guild.get_channel(self.channel_id)
        await manager.skip_to_next(channel)
        embed = discord.Embed(title="แจ้งเตือน", description="ข้ามเพลงแล้ว!", color=0x0099ff)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔉 Vol-", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction, cooldown=1):
            return
        
        manager = self.get_manager()
        vc = manager.voice_client
        
        if vc and vc.source:
            current_volume = vc.source.volume
            new_volume = max(0.0, current_volume - 0.1)  # ลดลง 10%, ต่ำสุด 0%
            vc.source.volume = new_volume
            embed = discord.Embed(title="🔉 ปรับระดับเสียง", description=f"ระดับเสียง: **{int(new_volume * 100)}%**", color=0x0099ff)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Error", description="ไม่มีเพลงที่กำลังเล่น!", color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔊 Vol+", style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction, cooldown=1):
            return
        
        manager = self.get_manager()
        vc = manager.voice_client
        
        if vc and vc.source:
            current_volume = vc.source.volume
            new_volume = min(2.0, current_volume + 0.1)  # เพิ่มขึ้น 10%, สูงสุด 200%
            vc.source.volume = new_volume
            embed = discord.Embed(title="🔊 ปรับระดับเสียง", description=f"ระดับเสียง: **{int(new_volume * 100)}%**", color=0x0099ff)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Error", description="ไม่มีเพลงที่กำลังเล่น!", color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🚪 Leave", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permission(interaction) or not await self._check_cooldown(interaction):
            return
        
        manager = self.get_manager()
        
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
            
        await manager.disconnect_and_cleanup(self.guild)
        
        embed = discord.Embed(title="🚪 Bot Exited", description="บอทหยุดเล่นและลบห้องแชทเรียบร้อยแล้ว!", color=0xff0000)
        await interaction.followup.send(embed=embed, ephemeral=True)
