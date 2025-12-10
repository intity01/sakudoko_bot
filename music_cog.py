from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional, List
import logging

logger = logging.getLogger('discord_bot')

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sync_cooldowns = {}  # guild_id: last_sync_time

    def is_in_voice_with_bot(self, interaction):
        """Checks if the user is in the same voice channel as the bot."""
        server_id = interaction.guild_id
        manager = self.bot.get_manager(server_id)
        
        # ตรวจสอบว่าผู้ใช้อยู่ในห้องเสียงหรือไม่
        if not interaction.user.voice or not interaction.user.voice.channel:
            return False
        
        # ตรวจสอบว่าอยู่ห้องเดียวกับบอทหรือไม่
        vc = manager.voice_client
        if vc and vc.channel and interaction.user.voice.channel.id != vc.channel.id:
            return False
        
        return True

    def require_in_voice(self, func):
        """Decorator to enforce voice channel permission for slash commands."""
        import functools
        @functools.wraps(func)
        async def wrapper(interaction, *args, **kwargs):
            if not self.is_in_voice_with_bot(interaction):
                await interaction.response.send_message("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
                return
            return await func(interaction, *args, **kwargs)
        return wrapper

    @app_commands.command(name="join", description="ให้บอทเข้าห้องเสียงและสร้างห้องแชทส่วนตัวสำหรับผู้ใช้")
    async def join(self, interaction):
        # Defer IMMEDIATELY before any checks to prevent timeout
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.warning("Interaction expired before deferring")
            return
        except Exception as e:
            logger.error(f"Error deferring interaction: {e}")
            return
        
        manager = self.bot.get_manager(interaction.guild_id)
        
        # Check voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ คุณต้องอยู่ในห้องเสียงก่อน!", ephemeral=True)
            return
        
        try:
            # Connect to voice channel
            channel = interaction.user.voice.channel
            if interaction.guild.voice_client is None:
                vc = await channel.connect()
                # เปิดไมค์ แต่ปิดหูฟังแบบ server เพื่อประหยัด bandwidth
                await interaction.guild.me.edit(mute=False, deafen=True)
            elif interaction.guild.voice_client.channel != channel:
                await interaction.guild.voice_client.move_to(channel)
                # เปิดไมค์ แต่ปิดหูฟังแบบ server
                await interaction.guild.me.edit(mute=False, deafen=True)

            # Create/Get Music Room
            chat_name = f"{interaction.user.name.lower().replace(' ', '-')}-music-room"
            existing = discord.utils.get(interaction.guild.text_channels, name=chat_name)
            category = channel.category if channel and channel.category else None
            
            # Check if the user is already the owner of a room
            if manager.owner_id and manager.owner_id != interaction.user.id:
                # If the room exists and is owned by someone else, only admin can take over
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send(f"❌ ห้องเพลงถูกสร้างโดย <@{manager.owner_id}> แล้ว", ephemeral=True)
                    return
                # Admin takeover logic:
                manager.owner_id = interaction.user.id
                
            # If no owner, set the current user as owner
            if not manager.owner_id:
                manager.owner_id = interaction.user.id

            embed = discord.Embed(title="🎶 Music Room Created", color=0x1DB954)
            embed.add_field(name="เจ้าของห้อง", value=interaction.user.mention, inline=True)
            embed.add_field(name="Welcome!", value=f"คุณถูกย้ายเข้าห้องเสียงและสร้างห้องแชทส่วนตัวแล้ว\nสามารถขอเพลงหรือควบคุมเพลงได้ทันที!", inline=False)
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/727/727245.png")
            embed.set_footer(text="Sakudoko Music Bot", icon_url="https://cdn-icons-png.flaticon.com/512/727/727245.png")
            
            from views import RequestFirstSongView # Import here to avoid circular dependency
            view = RequestFirstSongView()
            
            if not existing:
                # Create a new channel - ให้ทุกคนในห้องเสียงเห็นและใช้งานได้
                voice_channel = interaction.user.voice.channel
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False,  # คนนอกห้องเสียงไม่เห็น
                        send_messages=False,
                        mention_everyone=False
                    ),
                    interaction.guild.me: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        mention_everyone=False
                    )
                }
                
                # เพิ่ม permission สำหรับทุกคนที่อยู่ในห้องเสียง
                for member in voice_channel.members:
                    if not member.bot:  # ไม่รวม bot อื่น
                        overwrites[member] = discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True,
                            mention_everyone=False
                        )
                
                music_channel = await interaction.guild.create_text_channel(
                    chat_name, 
                    overwrites=overwrites, 
                    category=category
                )
                manager.music_channel_id = music_channel.id
                
                # ปิดเสียงแจ้งเตือนของห้อง (suppress @everyone and @here)
                try:
                    await music_channel.edit(
                        default_auto_archive_duration=60,
                        # Set to only mentions (no all messages notifications)
                    )
                except Exception as e:
                    logger.warning(f"Could not edit channel notification settings: {e}")
                
                # ส่งข้อความแรกแบบ silent (suppress notifications)
                await music_channel.send(embed=embed, view=view, silent=True)
                await interaction.followup.send(f"✅ สร้างห้องแชท {music_channel.mention} แล้ว!", ephemeral=True)
                
                # Start cleanup task (moved to manager in main.py)
                manager.start_cleanup_task(interaction.guild)
                
            else:
                # Use existing channel - อัพเดท permissions ให้ทุกคนในห้องเสียง
                music_channel = existing
                manager.music_channel_id = music_channel.id
                
                # อัพเดท permissions สำหรับทุกคนที่อยู่ในห้องเสียง
                voice_channel = interaction.user.voice.channel
                updated_count = 0
                for member in voice_channel.members:
                    if not member.bot:
                        try:
                            await music_channel.set_permissions(
                                member,
                                read_messages=True,
                                send_messages=True,
                                mention_everyone=False
                            )
                            updated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to update permissions for {member.name}: {e}")
                
                await interaction.followup.send(
                    f"✅ เข้าห้องแชท {music_channel.mention} แล้ว! อัพเดท permissions สำหรับ {updated_count} คน",
                    ephemeral=True
                )
                
                # Send the control view to the music channel if it doesn't exist
                if not manager.now_playing_msg:
                    await music_channel.send(embed=embed, view=view)
                    
        except Exception as e:
            logger.error(f"Error in join command: {e}")
            await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)


    @app_commands.command(name="leave", description="ให้บอทออกจากห้องเสียงและลบห้องแชทเพลง")
    async def leave(self, interaction):
        # Defer immediately
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception as e:
            logger.error(f"Error deferring interaction: {e}")
            return
        
        if not self.is_in_voice_with_bot(interaction):
            await interaction.followup.send("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        manager = self.bot.get_manager(interaction.guild_id)
        
        await manager.disconnect_and_cleanup(interaction.guild)
        
        # Remove manager instance from bot's state
        if interaction.guild_id in self.bot.managers:
            del self.bot.managers[interaction.guild_id]
            
        await interaction.followup.send("🚪 บอทออกจากห้องและลบห้องแชทเพลงเรียบร้อยแล้ว!", ephemeral=True)

    @app_commands.command(name="queue", description="แสดงคิวเพลงปัจจุบัน")
    async def queue(self, interaction):
        manager = self.bot.get_manager(interaction.guild_id)
        embed = manager.get_queue_list_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remove", description="ลบเพลงออกจากคิว")
    @app_commands.describe(index="ลำดับของเพลงในคิวที่จะลบ (1-based)")
    async def remove(self, interaction: "discord.Interaction", index: int):
        if not self.is_in_voice_with_bot(interaction):
            await interaction.response.send_message("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        manager = self.bot.get_manager(interaction.guild_id)
        removed_url = manager.remove_from_queue(index)
        
        if removed_url:
            await interaction.response.send_message(f"✅ ลบเพลงลำดับที่ **{index}** ออกจากคิวแล้ว", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ ไม่พบเพลงลำดับที่ **{index}** ในคิว", ephemeral=True)

    @app_commands.command(name="shuffle", description="สุ่มลำดับเพลงในคิว")
    async def shuffle(self, interaction):
        if not self.is_in_voice_with_bot(interaction):
            await interaction.response.send_message("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        manager = self.bot.get_manager(interaction.guild_id)
        if manager.shuffle_queue():
            await interaction.response.send_message("🔀 สุ่มลำดับเพลงในคิวเรียบร้อยแล้ว!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ คิวเพลงมีน้อยเกินไปสำหรับการสุ่ม!", ephemeral=True)

    @app_commands.command(name="loop", description="เปิด/ปิดการเล่นซ้ำคิวเพลง")
    async def loop(self, interaction):
        if not self.is_in_voice_with_bot(interaction):
            await interaction.response.send_message("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        manager = self.bot.get_manager(interaction.guild_id)
        status = "เปิด" if manager.toggle_loop() else "ปิด"
        await interaction.response.send_message(f"🔁 Loop คิวเพลง: **{status}**", ephemeral=True)

    @app_commands.command(name="autoplay", description="เปิด/ปิดโหมดเล่นเพลงอัตโนมัติเมื่อคิวหมด")
    async def autoplay(self, interaction):
        if not self.is_in_voice_with_bot(interaction):
            await interaction.response.send_message("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        manager = self.bot.get_manager(interaction.guild_id)
        manager.auto_play = not manager.auto_play
        status = "เปิด" if manager.auto_play else "ปิด"
        await interaction.response.send_message(f"🤖 Auto Play: **{status}**", ephemeral=True)

    @app_commands.command(name="filter", description="ตั้งค่า filter/effect ให้กับเพลง")
    @app_commands.describe(filter_name="ชื่อ filter (เช่น bass, nightcore, pitch) หรือ 'none' เพื่อปิด")
    async def filter(self, interaction: "discord.Interaction", filter_name: Literal['none', 'bass', 'nightcore', 'pitch']):
        if not self.is_in_voice_with_bot(interaction):
            await interaction.response.send_message("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        manager = self.bot.get_manager(interaction.guild_id)
        
        if filter_name == 'none':
            manager.selected_filter = None
            await interaction.response.send_message("✅ ปิด filter/effect แล้ว", ephemeral=True)
        else:
            manager.selected_filter = filter_name
            await interaction.response.send_message(f"✅ ตั้งค่า filter เป็น **{filter_name}** แล้ว เพลงถัดไปจะใช้ filter นี้", ephemeral=True)
        
        # Note: To apply the filter to the current song, the song needs to be reloaded.
        # This is complex and usually done by skipping to the next song or replaying the current one.
        # For simplicity, we only apply it to the next song.

    @app_commands.command(name="play", description="เล่นเพลงจาก YouTube")
    @app_commands.describe(query="ชื่อเพลงหรือ YouTube URL")
    async def play(self, interaction: "discord.Interaction", query: str):
        """Play a song from YouTube"""
        # Defer immediately to prevent timeout
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception as e:
            logger.error(f"Error deferring interaction: {e}")
            return
        
        manager = self.bot.get_manager(interaction.guild_id)
        
        # Check if user is in voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ คุณต้องอยู่ในห้องเสียงก่อน! ใช้ `/join` เพื่อเข้าห้องเสียง", ephemeral=True)
            return
        
        # Check if bot is connected
        if not interaction.guild.voice_client:
            await interaction.followup.send("❌ บอทยังไม่ได้เข้าห้องเสียง! ใช้ `/join` ก่อน", ephemeral=True)
            return
        
        # Check if user is in the same voice channel as bot
        if not self.is_in_voice_with_bot(interaction):
            await interaction.followup.send("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        
        # Check if music room exists
        if not manager.music_channel_id:
            await interaction.followup.send("❌ ยังไม่มีห้องแชทเพลง! ใช้ `/join` ก่อน", ephemeral=True)
            return
        
        # Check if user is in the music room
        music_channel = interaction.guild.get_channel(manager.music_channel_id)
        if music_channel and interaction.channel_id != manager.music_channel_id:
            await interaction.followup.send(
                f"❌ คุณต้องใช้คำสั่งนี้ในห้องแชทเพลง {music_channel.mention} เท่านั้น!",
                ephemeral=True
            )
            return
        
        # Add song to queue
        try:
            # Extract info using Cobalt
            from player import YTDL_INSTANCE as cobalt
            info = await cobalt.extract_info(query, download=False)
            
            if not info:
                await interaction.followup.send("❌ ไม่พบเพลงหรือวิดีโอจากคำค้นนี้", ephemeral=True)
                return

            urls_to_add = []
            if 'entries' in info:
                # Handle playlist
                for entry in info['entries']:
                    if entry and 'webpage_url' in entry:
                        urls_to_add.append(entry['webpage_url'])
                
                if urls_to_add:
                    manager.add_to_queue(urls_to_add)
                    await interaction.followup.send(f"✅ เพิ่ม **{len(urls_to_add)}** เพลงจากเพลย์ลิสต์ลงในคิว", ephemeral=True)
                else:
                    await interaction.followup.send("❌ ไม่พบเพลงในเพลย์ลิสต์นี้", ephemeral=True)
                    return
            else:
                # Handle single track
                url = info.get('webpage_url')
                title = info.get('title', 'Unknown Song')
                if url:
                    manager.add_to_queue([url])
                    await interaction.followup.send(f"✅ เพิ่มเพลง **{title}** ในคิวแล้ว!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ ไม่สามารถดึง URL ของเพลงได้", ephemeral=True)
                    return

            # Start playing if not already playing
            vc = interaction.guild.voice_client
            if vc and not vc.is_playing():
                channel = interaction.guild.get_channel(manager.music_channel_id)
                if channel:
                    await manager.play_next(channel)
                
        except Exception as e:
            logger.error(f"Error adding song to queue: {e}")
            await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

    @app_commands.command(name="sync_permissions", description="อัพเดท permissions ของห้องแชทให้ตรงกับคนในห้องเสียง")
    async def sync_permissions(self, interaction):
        """Sync music channel permissions with voice channel members"""
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception as e:
            logger.error(f"Error deferring interaction: {e}")
            return
        
        # Rate limit: 30 seconds cooldown per guild
        import time
        now = time.time()
        
        # Cleanup old cooldowns (older than 5 minutes)
        if len(self.sync_cooldowns) > 100:  # Prevent memory leak
            cutoff = now - 300
            self.sync_cooldowns = {gid: t for gid, t in self.sync_cooldowns.items() if t > cutoff}
        
        last_sync = self.sync_cooldowns.get(interaction.guild_id, 0)
        if now - last_sync < 30:
            remaining = int(30 - (now - last_sync))
            await interaction.followup.send(
                f"⏳ กรุณารอ {remaining} วินาที ก่อนใช้คำสั่งนี้อีกครั้ง",
                ephemeral=True
            )
            return
        
        manager = self.bot.get_manager(interaction.guild_id)
        
        # Check if user is in voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ คุณต้องอยู่ในห้องเสียงก่อน!", ephemeral=True)
            return
        
        # Check if music channel exists
        if not manager.music_channel_id:
            await interaction.followup.send("❌ ยังไม่มีห้องแชทเพลง! ใช้ `/join` ก่อน", ephemeral=True)
            return
        
        music_channel = interaction.guild.get_channel(manager.music_channel_id)
        if not music_channel:
            await interaction.followup.send("❌ ไม่พบห้องแชทเพลง!", ephemeral=True)
            return
        
        # Check if bot is in voice channel
        vc = manager.voice_client
        if not vc or not vc.channel:
            await interaction.followup.send("❌ บอทยังไม่ได้เข้าห้องเสียง!", ephemeral=True)
            return
        
        # Check if user is in the same voice channel as bot
        if interaction.user.voice.channel.id != vc.channel.id:
            await interaction.followup.send("❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", ephemeral=True)
            return
        
        # Sync permissions for all members in voice channel
        voice_channel = vc.channel
        updated_count = 0
        failed_count = 0
        
        for member in voice_channel.members:
            if not member.bot:
                try:
                    await music_channel.set_permissions(
                        member,
                        read_messages=True,
                        send_messages=True,
                        mention_everyone=False
                    )
                    updated_count += 1
                except discord.Forbidden:
                    logger.error(f"No permission to update {member.name}")
                    failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync permissions for {member.name}: {e}")
                    failed_count += 1
        
        # Update cooldown
        self.sync_cooldowns[interaction.guild_id] = now
        
        if failed_count > 0:
            await interaction.followup.send(
                f"⚠️ อัพเดท permissions สำเร็จ {updated_count} คน, ล้มเหลว {failed_count} คน\n"
                f"ทุกคนในห้องเสียงสามารถเห็นและใช้งาน {music_channel.mention} ได้แล้ว",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"✅ อัพเดท permissions สำเร็จ! ทุกคนในห้องเสียง ({updated_count} คน) สามารถเห็นและใช้งาน {music_channel.mention} ได้แล้ว",
                ephemeral=True
            )

    @app_commands.command(name="help", description="แสดงคำสั่งทั้งหมดของบอท")
    async def help_command(self, interaction):
        embed = discord.Embed(
            title="🎶 Sakudoko Music Bot Commands",
            description="คำสั่งหลักสำหรับควบคุมบอทเพลง:",
            color=0x1DB954
        )
        embed.add_field(name="/join", value="ให้บอทเข้าห้องเสียงและสร้างห้องแชทเพลง", inline=False)
        embed.add_field(name="/play [ชื่อเพลง/URL]", value="เล่นเพลงจาก YouTube", inline=False)
        embed.add_field(name="/sync_permissions", value="อัพเดท permissions ของห้องแชทให้ตรงกับคนในห้องเสียง", inline=False)
        embed.add_field(name="/leave", value="ให้บอทออกจากห้องเสียงและลบห้องแชทเพลง", inline=False)
        embed.add_field(name="/queue", value="แสดงคิวเพลงปัจจุบัน", inline=False)
        embed.add_field(name="/remove [ลำดับ]", value="ลบเพลงออกจากคิว", inline=False)
        embed.add_field(name="/shuffle", value="สุ่มลำดับเพลงในคิว", inline=False)
        embed.add_field(name="/loop", value="เปิด/ปิดการเล่นซ้ำคิวเพลง", inline=False)
        embed.add_field(name="/autoplay", value="เปิด/ปิดโหมดเล่นเพลงอัตโนมัติเมื่อคิวหมด", inline=False)
        embed.add_field(name="/filter [ชื่อ]", value="ตั้งค่า filter/effect (bass, nightcore, pitch)", inline=False)
        embed.add_field(name="ในห้องแชทเพลง", value="พิมพ์ชื่อเพลงหรือวางลิงก์เพื่อเพิ่มเพลงในคิว", inline=False)
        embed.set_footer(text="ควบคุมเพลงเพิ่มเติมได้จากปุ่มในข้อความ Now Playing")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
