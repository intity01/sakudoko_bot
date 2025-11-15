import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send(f"Pong! 🏓 {round(self.bot.latency * 1000)}ms")

    @commands.command(name="hello")
    async def hello(self, ctx):
        # The original command was: await ctx.send("สวัสดี! 👋 วะฮ่า ฮ๋า ฮ่า ฮ่า ~~~")
        await ctx.send("สวัสดี! 👋 วะฮ่า ฮ๋า ฮ่า ฮ่า ~~~")

async def setup(bot):
    await bot.add_cog(Basic(bot))
