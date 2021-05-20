from tortoise import models, fields
from utils.constants import Day
from .functions import *
from .fields import *
import discord

__all__ = ("Tourney", "TMSlot", "Scrim", "AssignedSlot", "ReservedSlot", "BannedTeam", "TagCheck")


class Tourney(models.Model):
    class Meta:
        table = "tm.tourney"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    name = fields.TextField()
    registration_channel_id = fields.BigIntField()
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    banned_users = BigIntArrayField(default=list)
    host_id = fields.BigIntField()
    started_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    open_role_id = fields.BigIntField()

    assigned_slots: fields.ManyToManyRelation["TMSlot"] = fields.ManyToManyField("models.TMSlot")


class TMSlot(models.Model):
    class Meta:
        table = "tm.register"

    id = fields.BigIntField(pk=True)
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    members = BigIntArrayField(default=list)
    jump_url = fields.TextField(null=True)


class Scrim(models.Model):
    class Meta:
        table = "sm.scrims"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    name = fields.TextField(default="Quotient-Scrims")
    registration_channel_id = fields.BigIntField()
    slotlist_channel_id = fields.BigIntField()
    slotlist_message_id = fields.BigIntField(null=True)
    role_id = fields.BigIntField(null=True)
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    host_id = fields.BigIntField()
    open_time = fields.DatetimeField()
    opened_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    autoclean = fields.BooleanField(default=False)
    autoslotlist = fields.BooleanField(default=True)
    ping_role_id = fields.BigIntField(null=True)
    stoggle = fields.BooleanField(default=True)
    open_role_id = fields.BigIntField(null=True)
    open_days = EnumArrayField(Day, default=Day.__iter__)
    assigned_slots: fields.ManyToManyRelation["AssignedSlot"] = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField("models.ReservedSlot")
    banned_teams: fields.ManyToManyRelation["BannedTeam"] = fields.ManyToManyField("models.BannedTeam")

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def logschan(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, name="quotient-scrims-logs")

    @property
    def modrole(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.roles, name="scrims-mod")

    @property
    def registration_channel(self):
        return self.bot.get_channel(self.registration_channel_id)

    @property
    def slotlist_channel(self):
        return self.bot.get_channel(self.slotlist_channel_id)

    @property
    def host(self):
        if self.guild is not None:
            return self.guild.get_member(self.host_id)

        return self.bot.get_user(self.host_id)

    @property
    def banned_users(self):
        return list(map(self.bot.get_user, self.banned_users_ids()))

    @property
    def opened(self):
        if self.opened_at is None:
            return False

        if self.closed_at is not None:
            return self.closed_at < self.opened_at

        return True

    @property
    def closed(self):
        return not self.opened

    @property
    def ping_role(self):
        if self.guild is not None:
            return self.guild.get_role(self.ping_role_id)

    @property
    def open_role(self):
        if self.guild is not None:
            if self.open_role_id is not None:
                return self.guild.get_role(self.open_role_id)
            else:
                return self.guild.default_role

    @property  # what? you think its useless , i know :)
    def toggle(self):
        return self.stoggle

    @property
    def teams_registered(self):  # This should be awaited
        return self.assigned_slots.order_by("num").all()

    async def user_registered(self):
        async for members in self.teams_registered.only("members"):
            for member_id in members:
                yield member_id

    async def reserved_user_ids(self):
        return (i.user_id for i in await self.reserved_slots.all())

    async def banned_user_ids(self):
        return (i.user_id for i in await self.banned_teams.all())

    async def create_slotlist(self):
        slots = await self.teams_registered
        description = "\n".join(f"Slot {slot.num:02}  ->  {slot.team_name}" for slot in slots)
        embed = discord.Embed(title=self.name + " Slotlist", description=f"```{description}```")
        channel = self.slotlist_channel
        return embed, channel


class BaseSlot(models.Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    team_name = fields.TextField(null=True)
    members = BigIntArrayField(default=list)


class AssignedSlot(BaseSlot):
    class Meta:
        table = "sm.assigned_slots"

    num = fields.IntField()
    jump_url = fields.TextField(null=True)


class ReservedSlot(BaseSlot):
    class Meta:
        table = "sm.reserved_slots"

    expires = fields.DatetimeField(null=True)


class BannedTeam(BaseSlot):
    class Meta:
        table = "sm.banned_teams"

    expires = fields.DatetimeField(null=True)


# ************************************************************************************************


class TagCheck(models.Model):
    class Meta:
        table = "tagcheck"

    guild_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField()
    required_mentions = fields.IntField(default=0)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    @property
    def modrole(self):
        guild = self.bot.get_guild(self.guild_id)
        if guild != None:
            return discord.utils.get(guild.roles, name="scrims-mod")


# class Fornite(models.Model):
#     class Meta:
#         table = "fn.settings"

#     guild_id = fields.BigIntField(pk=True)
#     suspended_role_id = fields.BigIntField()
#     is_authorized = fields.BooleanField(default=False)
#     logging_channel_id = fields.BigIntField()
#     logging_toggle = fields.BooleanField(default=True)
#     data: fields.ManyToManyRelation["ForData"] = fields.ManyToManyField("models.ForData")

#     @property
#     def guild(self):
#         return self.bot.get_guild(self.guild_id)

#     @property
#     def suspended_role(self):
#         if self.guild is not None:
#             return self.guild.get_role(self.suspended_role_id)

#     @property
#     def logging_channel(self):
#         if self.guild is not None:
#             return self.guild.get_channel(self.logging_channel_id)


# class ForData(models.Model):
#     class Meta:
#         table = "fn.data"

#     id = fields.BigIntField(pk=True)
#     moderator_id = fields.BigIntField()
#     action_user_id = fields.BigIntField()
#     start_time = fields.DatetimeField(auto_now=True)
#     expire_time = fields.DatetimeField()
#     reason = fields.TextField(null=True)
#     jump_url = fields.TextField(null=True)


# ************************************************************************************************
