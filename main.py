import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import asyncio
from keep_alive import keep_alive # For Replit/Render to keep the bot alive

# --- 1. Set up your bot with intents ---
# Intents are crucial for telling Discord what events your bot wants to receive.
intents = discord.Intents.default()
intents.members = True # Enable the server members intent
intents.message_content = True # Enable the message content intent (needed for reading commands)

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Report Modal (Handles Promotion, Demotion, Warning) ---
class ReportModal(ui.Modal, title="Member Report"):
    def __init__(self, report_type: str):
        super().__init__()
        self.report_type = report_type.lower() # Store the type (promotion, demotion, warning)

        self.promoted_user_id = ui.TextInput(
            label="Target User ID",
            placeholder="Enter the ID of the user (e.g., 123456789012345678)",
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.promoted_user_id) # Add it to the modal

        self.reason = ui.TextInput(
            label="Reason",
            placeholder="Detailed reason for this action.",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)

        #Add fields specific to Promotion/Demotion
        if self.report_type in ["promotion", "demotion"]:
            self.previous_rank = ui.TextInput(
                label="Previous Rank",
                placeholder="e.g., @ACRP | Probationary",
                required=True,
                style=discord.TextStyle.short
            )
            self.add_item(self.previous_rank)

            self.new_rank = ui.TextInput(
                label="New Rank",
                placeholder="e.g., @ACRP | Member",
                required=True,
                style=discord.TextStyle.short
            )
            self.add_item(self.new_rank)
        elif self.report_type == "warning":
            self.infraction = ui.TextInput(
                label="Infraction",
                placeholder="e.g., Rule 3.2 Violation, Inactivity, Improper Conduct",
                required=True,
                style=discord.TextStyle.short
            )
            self.add_item(self.infraction)

    # This method is called when the user submits the modal
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Report submitted!", ephemeral=True)

        target_id = self.promoted_user_id.value # Renamed for clarity
        report_reason = self.reason.value
        reported_by = interaction.user

        # Fetch the target user
        try:
            target_user = await bot.fetch_user(int(target_id))
        except ValueError:
            await interaction.followup.send("Invalid User ID provided. Please enter a numerical ID.", ephemeral=True)
            return
        except discord.NotFound:
            await interaction.followup.send("User not found with the provided ID. Please double check.", ephemeral=True)
            return

        # --- Define the channels where the embeds will be sent ---
        # REPLACE THESE WITH YOUR ACTUAL CHANNEL IDs
        promotion_channel_id = 1374387686617645107  # Replace with your promotion logs channel ID
        demotion_channel_id = 1374387816011927675   # Replace with your demotion logs channel ID
        warning_channel_id = 1374387889877811324   # Replace with your warning logs channel ID

        # Select the appropriate channel based on report type
        if self.report_type == "promotion":
            target_channel = bot.get_channel(promotion_channel_id)
            channel_type = "promotion"
        elif self.report_type == "demotion":
            target_channel = bot.get_channel(demotion_channel_id)
            channel_type = "demotion"
        elif self.report_type == "warning":
            target_channel = bot.get_channel(warning_channel_id)
            channel_type = "warning"
        else:
            await interaction.followup.send("Error: Unrecognized report type.", ephemeral=True)
            return

        if not target_channel:
            await interaction.followup.send(
                f"Error: {channel_type.capitalize()} logs channel not found or bot doesn't have access. "
                "Please notify an admin.", ephemeral=True
            )
            print(f"ERROR: {channel_type.capitalize()} channel not found.")
            return

        # --- Construct the Embed based on report type ---
        embed_color = discord.Color.greyple()  # Default color

        if self.report_type == "promotion":
            prev_rank = self.previous_rank.value
            new_rank = self.new_rank.value
            embed_title = "Promotion"
            embed_color = discord.Color.green()
            embed_description = f"**{target_user.mention} has been promoted!**"
            embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
            embed.add_field(name="Promoted by:", value=reported_by.mention, inline=False)
            embed.add_field(name="Previous Rank:", value=prev_rank, inline=False)
            embed.add_field(name="New Rank:", value=new_rank, inline=False)
            embed.add_field(name="Reason:", value=report_reason, inline=False)

        elif self.report_type == "demotion":
            prev_rank = self.previous_rank.value
            new_rank = self.new_rank.value
            embed_title = "Demotion"
            embed_color = discord.Color.red()
            embed_description = f"**{target_user.mention} has been demoted!**"
            embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
            embed.add_field(name="Demoted by:", value=reported_by.mention, inline=False)
            embed.add_field(name="Previous Rank:", value=prev_rank, inline=False)
            embed.add_field(name="New Rank:", value=new_rank, inline=False)
            embed.add_field(name="Reason:", value=report_reason, inline=False)

        elif self.report_type == "warning":
            infraction_details = self.infraction.value
            embed_title = "Warning"
            embed_color = discord.Color.yellow()
            embed_description = f"**{target_user.mention} has received a warning!**"
            embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
            embed.add_field(name="Issued by:", value=reported_by.mention, inline=False)
            embed.add_field(name="Infraction:", value=infraction_details, inline=False)
            embed.add_field(name="Reason:", value=report_reason, inline=False)

        else:
            # Fallback for an unrecognized report type
            await interaction.followup.send("Error: Unrecognized report type.", ephemeral=True)
            return

        #Add common embed elemnts
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
        embed.set_footer(text=f"ACRP Fuel stations | Report Type: {self.report_type.capitalize()}")
        embed.set_author(name=target_user.display_name, icon_url=target_user.avatar.url)

        # Handle automatic role assignment for promotions/demotions
        if self.report_type in ["promotion", "demotion"]:
            try:
                # Get the guild (server) to manage roles
                guild = interaction.guild
                if guild:
                    # Get the target member from the guild
                    target_member = guild.get_member(int(target_id))
                    if target_member:
                        await handle_role_assignment(target_member, self.previous_rank.value, self.new_rank.value, self.report_type)
                    else:
                        print(f"Warning: Could not find member {target_id} in guild for role assignment")
            except Exception as e:
                print(f"Error in role assignment: {e}")

        #send the embed to the designated channel
        await target_channel.send(embed=embed)

# Define authorized role IDs - Replace with your actual role IDs
AUTHORIZED_ROLES = [
    1373999258084179989,  # First manager/HR role ID
    1373999187816874075   # Second staff role ID - Replace with actual ID
]

# Define role mappings for automatic role assignment
# Replace these with your actual role IDs and names
ROLE_MAPPINGS = {
    "probationary": 1234567890123456789,   # Replace with Probationary role ID
    "member": 1373999066765201579,         # Replace with Member role ID
    "Employee |": 1376865664005967892,         # Replace with Senior role ID
    "Employee ||": 1376865848043638875,        # Replace with Manager role ID
    "Employee |||": 1376866092781408308        # Replace with Director role ID
}

async def check_authorized_roles(interaction: discord.Interaction) -> bool:
    """Check if user has any of the authorized roles"""
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in AUTHORIZED_ROLES)

async def handle_role_assignment(member: discord.Member, previous_rank: str, new_rank: str, action_type: str):
    """Handle automatic role assignment for promotions/demotions"""
    try:
        # Extract role names from the rank strings (remove prefixes like "@ACRP | ")
        old_role_name = extract_role_name(previous_rank)
        new_role_name = extract_role_name(new_rank)

        # Get role IDs from mappings
        old_role_id = ROLE_MAPPINGS.get(old_role_name.lower())
        new_role_id = ROLE_MAPPINGS.get(new_role_name.lower())

        guild = member.guild

        # Remove old role if it exists
        if old_role_id:
            old_role = guild.get_role(old_role_id)
            if old_role and old_role in member.roles:
                await member.remove_roles(old_role, reason=f"Automatic role removal - {action_type}")
                print(f"Removed role {old_role.name} from {member.display_name}")

        # Add new role if it exists
        if new_role_id:
            new_role = guild.get_role(new_role_id)
            if new_role and new_role not in member.roles:
                await member.add_roles(new_role, reason=f"Automatic role assignment - {action_type}")
                print(f"Added role {new_role.name} to {member.display_name}")

    except Exception as e:
        print(f"Error in handle_role_assignment: {e}")

def extract_role_name(rank_string: str) -> str:
    """Extract the role name from a rank string like '@ACRP | Member' -> 'Member'"""
    # Remove common prefixes and clean up the string
    cleaned = rank_string.replace("@ACRP |", "").replace("@", "").strip()
    return cleaned

# --- Dashboard View for HR Forms ---
class HRDashboardView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @ui.button(label="Promotion Report", style=discord.ButtonStyle.green, emoji="⬆️")
    async def promotion_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ReportModal("promotion"))

    @ui.button(label="Demotion Report", style=discord.ButtonStyle.red, emoji="⬇️")
    async def demotion_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ReportModal("demotion"))

    @ui.button(label="Warning Report", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warning_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ReportModal("warning"))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # You can set the bot's status here
    await bot.change_presence(activity=discord.Game(name="Managing Fuel Stations"))

    # Auto-post HR dashboard
    hr_dashboard_channel_id = 1376059049560375387 # Replace with your desired channel ID
    hr_dashboard_channel = bot.get_channel(hr_dashboard_channel_id)

    if hr_dashboard_channel:
        embed = discord.Embed(
            title="🏢 ACRP Fuel Stations - Management Dashboard",
            description=(
                "**Promotion, Demotion, Warning Portal**\n\n"
                "Use the buttons below to submit official reports for:\n"
                "• **Promotions** - Advance employee ranks\n"
                "• **Demotions** - Reduce employee ranks\n"
                "• **Warnings** - Issue disciplinary actions\n\n"
                "All reports will be automatically logged to the appropriate channels with detailed information.\n\n"
                "*This dashboard is permanent and will remain functional for all authorized Staff personnel.*"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="ACRP Fuel Stations | Management System")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/123456789/folder-icon.png")  # You can replace with your server icon

        view = HRDashboardView()
        await hr_dashboard_channel.send(embed=embed, view=view)
        print(f"HR Dashboard posted in channel {hr_dashboard_channel.name}")
    else:
        print(f"Error: HR dashboard channel not found or bot doesn't have access.")

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# --- Command: About/Info ---
@bot.command(name='about', help='Provides information about the bot.')
async def about(ctx):
    embed = discord.Embed(
        title="ACRP Fuel Station Bot",
        description=(
            "Your dedicated assistant for the ACRP Fuel Stations, maintained by ungradua.\n\n"
            "**Purpose:** This bot helps manage information related to station status, and provides "
            "utility functions for the ACRP Fuel Station operations.\n\n"
            "**Developed by:** [ungradua]\n"
            "**Version:** 1.0.5\n"
            "**Last Updated:** 28 May 2025" # Update this date regularly
        ),
        color=discord.Color.gold() # You can choose any color
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url) # Uses bot's own avatar
    embed.set_footer(text=f"Serving {len(bot.guilds)} servers | Use !help for commands")

    await ctx.send(embed=embed)

# main.py continues here:
if __name__ == "__main__":
    # This will run a simple web server in the background
    keep_alive() 
    # Get the bot token from environment variables
    bot_token = os.environ.get('DISCORD_BOT_TOKEN')
    if bot_token:
        bot.run(bot_token)
    else:
        print("Error: DISCORD_BOT_TOKEN environment variable not set. Please add it to Replit secrets.")