import os
import asyncio
from config import *
from pyrogram import Client, filters
from pyrogram.types import Message, User, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, ChatAdminRequired, RPCError, UserNotParticipant
from database.database import set_approval_off, is_approval_off
from helper_func import *

# Default settings
APPROVAL_WAIT_TIME = 1  # seconds 
AUTO_APPROVE_ENABLED = True  # Toggle for enabling/disabling auto approval 

async def get_user_client():
    global user_client
    if user_client is None:
        user_client = UserClient("userbot", session_string=USER_SESSION, api_id=APP_ID, api_hash=API_HASH)
        await user_client.start()
    return user_client

@Client.on_chat_join_request((filters.group | filters.channel) & filters.chat(CHAT_ID) if CHAT_ID else (filters.group | filters.channel))  
async def autoapprove(client, message: ChatJoinRequest):  
    global AUTO_APPROVE_ENABLED  
  
    if not AUTO_APPROVE_ENABLED:  
        return  
  
    chat = message.chat  
    user = message.from_user  
  
    # check if approval is off for this channel  
    if await is_approval_off(chat.id):  
        print(f"Auto-approval is OFF for channel {chat.id}")  
        return  
  
    print(f"{user.first_name} requested to join {chat.title}")  
      
    await asyncio.sleep(APPROVAL_WAIT_TIME)  
  
    # Check if user is already a participant before approving  
    try:  
        member = await client.get_chat_member(chat.id, user.id)  
        if member.status in ["member", "administrator", "creator"]:  
            print(f"User {user.id} is already a participant of {chat.id}, skipping approval.")  
            return  
    except UserNotParticipant:  
        # User is not a member, handle accordingly  
        pass  
  
    # Move this inside the async function
    await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
    
    if APPROVED == "on":
        invite_link = await client.export_chat_invite_link(chat.id)
        buttons = [
            [InlineKeyboardButton(f'• ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ •', url=invite_link)]
        ]
        markup = InlineKeyboardMarkup(buttons)
        caption = f"<b>Hᴇʏ {user.mention()},\n<blockquote> ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat.title} ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ.</blockquote> </b>"
        
        sent_msg = await client.send_photo(
            chat_id=user.id,
            photo='https://graph.org/file/2a3bdf158d2d876c474a1-8566a8ace3bc440d18.jpg',
            caption=caption,
            reply_markup=markup
        )

        await asyncio.sleep(60)
        try:
            await client.delete_messages(chat_id=user.id, message_ids=sent_msg.id)
        except Exception as e:
            print(f"Failed to delete message: {e}")

@Client.on_message(filters.command("reqtime") & is_owner_or_admin)
async def set_reqtime(client, message: Message):
    global APPROVAL_WAIT_TIME
    
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("Usage: <code>/reqtime {seconds}</code>")
    
    APPROVAL_WAIT_TIME = int(message.command[1])
    await message.reply_text(f"✅ Request approval time set to <b>{APPROVAL_WAIT_TIME}</b> seconds.")

@Client.on_message(filters.command("reqmode") & is_owner_or_admin)
async def toggle_reqmode(client, message: Message):
    global AUTO_APPROVE_ENABLED
    
    if len(message.command) != 2 or message.command[1].lower() not in ["on", "off"]:
        return await message.reply_text("Usage: <code>/reqmode on</code> or <code>/reqmode off</code>")
    
    mode = message.command[1].lower()
    AUTO_APPROVE_ENABLED = (mode == "on")
    status = "enabled ✅" if AUTO_APPROVE_ENABLED else "disabled ❌"
    await message.reply_text(f"Auto-approval has been {status}.")

@Client.on_message(filters.command("approveoff") & is_owner_or_admin)
async def approve_off_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/approveoff {channel_id}</code>")
    channel_id = int(message.command[1])
    success = await set_approval_off(channel_id, True)
    if success:
        await message.reply_text(f"✅ Auto-approval is now <b>OFF</b> for channel <code>{channel_id}</code>.")
    else:
        await message.reply_text(f"❌ Failed to set auto-approval OFF for channel <code>{channel_id}</code>.")

@Client.on_message(filters.command("approveon") & is_owner_or_admin)
async def approve_on_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/approveon {channel_id}</code>")
    channel_id = int(message.command[1])
    success = await set_approval_off(channel_id, False)
    if success:
        await message.reply_text(f"✅ Auto-approval is now <b>ON</b> for channel <code>{channel_id}</code>.")
    else:
        await message.reply_text(f"❌ Failed to set auto-approval ON for channel <code>{channel_id}</code>.")
