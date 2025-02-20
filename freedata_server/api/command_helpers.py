# api/command_helpers.py
import asyncio


async def enqueue_tx_command(app, cmd_class, params={}):
    """
    Enqueue a transmit command using the app's managers.

    Args:
        app: The FastAPI app instance (e.g., request.app) containing config_manager, state_manager, etc.
        cmd_class: The command class to instantiate and run.
        params: A dict of parameters for the command.

    Returns:
        True if the command was successfully enqueued and ran, False otherwise.
    """
    try:
        # Create an instance of the command using app components.
        command = cmd_class(app.config_manager.read(), app.state_manager, app.event_manager, params)
        print(f"Command {command.get_name()} running...")
        # Run the command in a separate thread to avoid blocking the event loop.
        result = await asyncio.to_thread(command.run, app.modem_events, app.service_manager.modem)
        if result:
            return True
    except Exception as e:
        print(f"Command failed: {e}")
    return False
