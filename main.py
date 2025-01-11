from telethon import TelegramClient, events
from datetime import datetime, timedelta
import asyncio

# Bot initialization
api_id = 11573285
api_hash = "f2cc3fdc32197c8fbaae9d0bf69d2033"
bot_token = "7439518206:AAG7n5rN4foWudgkvZ8PpJnEVzoGh-mcEhs"

client = TelegramClient("queue_bot", api_id, api_hash).start(bot_token=bot_token)

# Queue system
message_queue = []  # List to store messages with metadata
channels = [-1002457351800]  # Add all your channel IDs
last_message_time = None  # Tracks the last message's post time

# Function to process the queue
async def process_queue():
    global last_message_time
    while True:
        if message_queue:
            current_time = datetime.now()
            first_message = message_queue[0]
            if current_time >= first_message["post_time"]:
                # Post the message/media to all channels
                for channel in channels:
                    if first_message["media"]:
                        await client.send_file(entity=channel, file=first_message["media"], caption=first_message["message_text"])
                    else:
                        await client.send_message(entity=channel, message=first_message["message_text"])
                message_queue.pop(0)  # Remove the processed message
                last_message_time = current_time
        await asyncio.sleep(1)  # Check the queue every second

# Handle incoming messages
@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    global last_message_time
    user_id = event.sender_id
    message_text = event.raw_text
    media = event.message.media  # Check for media content
    current_time = datetime.now()

    # If there was no previous message or enough time has passed, post immediately
    if not last_message_time or (current_time - last_message_time).total_seconds() > 60:
        for channel in channels:
            if media:
                await client.send_file(entity=channel, file=media, caption=message_text)
            else:
                await client.send_message(entity=channel, message=message_text)
        last_message_time = current_time
        await event.reply("Your message has been posted instantly.")
    else:
        # If the message is within 1 minute, add it to the queue
        if message_queue:
            # Set post_time to 1 minute after the last message in the queue
            post_time = message_queue[-1]["post_time"] + timedelta(minutes=1)
        else:
            # If the queue is empty, set post_time to 1 minute after the last message time
            post_time = last_message_time + timedelta(minutes=1)

        # Add message to queue
        message_queue.append({
            "user_id": user_id,
            "message_text": message_text,
            "media": media,
            "post_time": post_time
        })

        # Calculate remaining time and queue position
        remaining_time = post_time - current_time
        remaining_minutes = remaining_time.seconds // 60
        remaining_seconds = remaining_time.seconds % 60
        queue_position = len(message_queue)  # Get the position in the queue

        await event.reply(
            f"Your message has been queued and will be posted in {remaining_minutes} min {remaining_seconds} sec. (Position: {queue_position})"
        )

# Delete the last message from the queue
@client.on(events.NewMessage(incoming=True, pattern="/deletelast"))
async def delete_last_message(event):
    user_id = event.sender_id
    for idx, queued_message in enumerate(message_queue):
        if queued_message["user_id"] == user_id:
            removed_message = message_queue.pop(idx)

            # Adjust timing for the next message in the queue
            if idx < len(message_queue):
                message_queue[idx]["post_time"] = removed_message["post_time"]

            await event.reply("Your last message has been removed from the queue.")
            return

    await event.reply("You don't have any messages in the queue.")

# Start the queue processor
loop = asyncio.get_event_loop()
loop.create_task(process_queue())

print("Bot is running...")
client.run_until_disconnected()
