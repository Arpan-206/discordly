import os

import discord
from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.query import Query
from appwrite.services.databases import Databases
from discord.ext import commands
from dotenv import load_dotenv
from table2ascii import PresetStyle, table2ascii

load_dotenv()

intents = discord.Intents.all()
my_secret = os.environ["DISCORD_BOT_TOKEN"]  # Bot Token
bot = commands.Bot(command_prefix="!", intents=intents)

client = Client()

(client
 .set_endpoint(os.environ['AW_ENDPOINT'])  # Your API Endpoint
 .set_project(os.environ['AW_PROJECT'])  # Your project ID
 .set_key(os.environ['AW_KEY'])  # Your secret API key
 .set_self_signed()
 )
dbs = Databases(client)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot is running as {0.user}".format(bot))


@bot.hybrid_command()
async def shorten(ctx, long_url, alias=None, public: bool = False):
    """Shorten a URL"""

    if alias:
        # Check if alias exists
        response = dbs.list_documents(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], queries=[
                                      Query.equal("alias", alias)])
        if response['total'] > 0:
            return await ctx.send("Alias already taken, please choose a different one.", ephemeral=True)
    else:
        # Generate random alias
        import random
        import string
        alias = ''.join(random.choice(string.ascii_lowercase)
                        for i in range(6))

    try:
        result = dbs.create_document(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], 'unique()', {
            'long_url': long_url,
            'alias': alias,
            'user_id': ctx.author.id
        })
    except AppwriteException:
        return await ctx.send("Error creating document. Maybe the URL the invalid?", ephemeral=True)
    await ctx.send("Shortening URL...", ephemeral=True)

    await ctx.send(f'Your shortened URL is: {os.environ["DEPLOY_URL"]}/{alias}', ephemeral=not public)


@bot.hybrid_command()
async def delete(ctx, alias, public: bool = False):
    """Delete a shortened URL"""
    await ctx.send("Deleting URL...", ephemeral=True)
    try:
        doc = dbs.list_documents(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], queries=[
                                 Query.equal("alias", alias)])['documents'][0]
    except IndexError:
        return await ctx.send("Alias not found.", ephemeral=True)
    if doc['user_id'] != ctx.author.id:
        return await ctx.send("You don't own this alias.", ephemeral=True)
    dbs.delete_document(
        os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], doc["$id"])
    await ctx.send(f"URL with alias `{alias}` deleted.", ephemeral=not public)


@bot.hybrid_command()
async def list(ctx, public: bool = False):
    """List all your shortened URLs"""
    await ctx.send("Fetching URLs...", ephemeral=True)
    docs = dbs.list_documents(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], queries=[
                              Query.equal("user_id", ctx.author.id)])['documents']
    if len(docs) == 0:
        return await ctx.send("You don't have any shortened URLs.", ephemeral=not public)

    list_of_urls = []
    for doc in docs:
        list_of_urls.append([doc['alias'], '...' + doc['long_url'][-10:],
                            doc['active'], doc['clicks'], doc['$createdAt'][:10].replace('-', '/')])

    outp = table2ascii(
        header=['Alias', 'Long URL', 'Active', 'Clicks', 'Created At'],
        body=list_of_urls,
        style=PresetStyle.thin_compact
    )
    await ctx.send(f"Your shortened URLs are: ```\n{outp}\n```", ephemeral=not public)


@bot.hybrid_command()
async def change_alias(ctx, old_alias, new_alias, public: bool = False):
    """Change the alias of a shortened URL"""
    await ctx.send("Changing alias...", ephemeral=True)
    try:
        doc = dbs.list_documents(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], queries=[
                                 Query.equal("alias", old_alias)])['documents'][0]
    except IndexError:
        return await ctx.send("Alias not found.", ephemeral=True)
    if doc['user_id'] != ctx.author.id:
        return await ctx.send("You don't own this alias.", ephemeral=True)
    dbs.update_document(
        os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], doc["$id"], {'alias': new_alias})
    await ctx.send(f"URL with alias `{old_alias}` changed to `{new_alias}`.", ephemeral=not public)


@bot.command()
async def sync(ctx):
    if str(ctx.author.id) == str(os.environ["OWNER"]):
        await ctx.send("Syncing the bot...")
        await bot.tree.sync()
        await ctx.send("Synced the bot!")
    else:
        await ctx.send("You are not the owner of this bot!")

bot.run(my_secret)