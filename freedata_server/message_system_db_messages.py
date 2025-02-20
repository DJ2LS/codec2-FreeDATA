from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_model import Status, P2PMessage
from message_system_db_station import DatabaseManagerStations
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json
import os


class DatabaseManagerMessages(DatabaseManager):
    def __init__(self, event_manager):
        super().__init__(event_manager)
        self.attachments_manager = DatabaseManagerAttachments(event_manager)
        self.stations_manager = DatabaseManagerStations(event_manager)

    def add_message(self, message_data, statistics, direction='receive', status=None, is_read=True, frequency=None):
        session = self.get_thread_scoped_session()
        try:
            # Create and add the origin and destination Stations
            origin = self.get_or_create_station(message_data['origin'], session)
            destination = self.get_or_create_station(message_data['destination'], session)

            # Create and add Status if provided
            if status:
                status = self.get_or_create_status(session, status)

            # Parse the timestamp from the message ID
            timestamp = datetime.fromisoformat(message_data['id'].split('_')[2])

            if frequency and frequency not in ['---']:
                statistics["frequency"] = frequency

            # Create the P2PMessage instance
            new_message = P2PMessage(
                id=message_data['id'],
                origin_callsign=origin.callsign,
                destination_callsign=destination.callsign,
                body=message_data['body'],
                timestamp=timestamp,
                direction=direction,
                status_id=status.id if status else None,
                is_read=is_read,
                attempt=0,
                statistics=statistics            )

            session.add(new_message)

            # Process and add attachments
            if 'attachments' in message_data:
                for attachment_data in message_data['attachments']:
                    self.attachments_manager.add_attachment(session, new_message, attachment_data)

            session.commit()
            self.log(f"Added data to database: {new_message.id}")
            self.event_manager.freedata_message_db_change(message_id=new_message.id)
            return new_message.id
        except IntegrityError as e:
            session.rollback()  # Roll back the session to a clean state
            self.log(f"Message with ID {message_data['id']} already exists in the database.", isWarning=True)
            return None

        except Exception as e:
            session.rollback()
            self.log(f"error adding new message to database with error: {e}", isWarning=True)
        finally:
            session.remove()

    def get_all_messages(self, filters=None):
        session = self.get_thread_scoped_session()
        try:
            query = session.query(P2PMessage)

            if filters:
                if 'id' in filters:
                    query = query.filter(P2PMessage.id == filters['id'])
                if 'callsign' in filters:
                    callsign_filter = filters['callsign']
                    query = query.filter(
                        (P2PMessage.origin_callsign.contains(callsign_filter)) |
                        (P2PMessage.via_callsign.contains(callsign_filter)) |
                        (P2PMessage.destination_callsign.contains(callsign_filter))
                    )
                if 'origin_callsign' in filters:
                    query = query.filter(P2PMessage.origin_callsign.contains(filters['origin_callsign']))
                if 'via_callsign' in filters:
                    query = query.filter(P2PMessage.via_callsign.contains(filters['via_callsign']))
                if 'destination_callsign' in filters:
                    query = query.filter(P2PMessage.destination_callsign.contains(filters['destination_callsign']))
                if 'direction' in filters:
                    query = query.filter(P2PMessage.direction.contains(filters['direction']))

            messages = query.all()
            return [message.to_dict() for message in messages]

        except Exception as e:
            self.log(f"error fetching database messages with error: {e}", isWarning=True)
            self.log(f"---> please delete or update existing database", isWarning=True)

            return []

        finally:
            session.remove()

    def get_all_messages_json(self, filters=None):
        messages_dict = self.get_all_messages(filters)
        messages_with_header = {'total_messages': len(messages_dict), 'messages': messages_dict}
        return messages_with_header

    def get_message_by_id(self, message_id):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                return message.to_dict()
            else:
                return None
        except Exception as e:
            self.log(f"Error fetching message with ID {message_id}: {e}", isWarning=True)
            return None
        finally:
            session.remove()

    def get_message_by_id_json(self, message_id):
        message_dict = self.get_message_by_id(message_id)
        return json.dumps(message_dict)  # Convert to JSON string

    def get_message_by_id_adif(self, message_id):
        """
        Fetches a message by ID and returns it in ADIF format.

        Parameters:
        message_id (str): The ID of the message to retrieve.

        Returns:
        str: The ADIF formatted message, or None if the message is not found.
        """
        message_dict = self.get_message_by_id(message_id)
        if message_dict:
            try:
                # Extract fields from the message dictionary
                origin = message_dict.get("origin", "")
                destination = message_dict.get("destination", "")
                timestamp = message_dict.get("timestamp", "")
                direction = message_dict.get("direction", "").lower()  # Ensure case insensitivity
                status = message_dict.get("status", "")
                statistics = message_dict.get("statistics", {})

                print(message_dict)
                print(statistics)

                # Determine the CALL based on the direction
                if direction == "receive":
                    call = origin.split("-")[0]  # Take the part before the "-" if it exists
                else:
                    call = destination.split("-")[0]  # Take the part before the "-" if it exists

                # Fetch station info
                origin_info = self.stations_manager.get_station(origin)

                # Parse the timestamp for QSO date and time, strip fractional seconds
                timestamp_clean = timestamp.split(".")[0]  # Remove fractional seconds
                qso_date = timestamp_clean.split("T")[0].replace("-", "")  # Extract the date part and remove hyphens

                # Extract the time and format it as HHMMSS
                time_on = datetime.strptime(timestamp_clean.split("T")[1], "%H:%M:%S").strftime("%H%M%S")

                # Calculate TIME_OFF by adding duration to TIME_ON
                duration = statistics.get("duration", 0.0)  # Duration in seconds
                time_on_obj = datetime.strptime(timestamp_clean.split("T")[1],
                                                "%H:%M:%S")  # Parse time_on as a datetime object
                time_off_obj = time_on_obj + timedelta(seconds=duration)
                time_off = time_off_obj.strftime("%H%M%S")  # Format time_off back to HHMMSS format

                # Set ADIF Fields
                mode = "DYNAMIC"
                submode = "FREEDATA"
                comment = f"QSO via FreeDATA RF-Chat"

                # Gridsquare handling
                print(origin_info)
                if origin_info and "location" in origin_info and origin_info["location"] is not None:
                    print(origin_info["location"])
                    grid = origin_info["location"].get("gridsquare", "")
                else:
                    grid = ""


                # Extract and adjust the frequency (Hz to MHz)
                frequency_hz = statistics.get("frequency")  # Get the frequency, may be None
                if frequency_hz is not None:
                    frequency_mhz = round(frequency_hz / 1_000_000,
                                          3)  # Convert Hz to MHz and round to 3 decimal places
                    frequency_str = str(frequency_mhz)  # Convert to string for ADIF format
                else:
                    frequency_str = "14.000000"  # Default to "0.000" MHz if frequency is missing

                # Construct the ADIF message
                adif_fields = [
                    f"<CALL:{len(call)}>{call}",
                    f"<QSO_DATE:{len(qso_date)}>{qso_date}",
                    f"<TIME_ON:{len(time_on)}>{time_on}",
                    f"<TIME_OFF:{len(time_off)}>{time_off}",  # Include TIME_OFF
                    f"<FREQ:{len(frequency_str)}>{frequency_str}",  # Frequency in MHz
                    f"<MODE:{len(mode)}>{mode}",
                    f"<SUBMODE:{len(submode)}>{submode}",
                    f"<COMMENT:{len(comment)}>{comment}",
                    f"<GRIDSQUARE:{len(grid)}>{grid}",
                    #f"<DIRECTION:{len(direction)}>{direction}",
                    #f"<STATUS:{len(status)}>{status}",
                    #f"<DURATION:{len(str(duration))}>{duration}",
                    "<EOR>"
                ]

                return "".join(adif_fields)

            except Exception as e:
                self.log(f"Error converting message {message_id} to ADIF: {e}", isWarning=True)
                return None
        else:
            self.log(f"Message with ID {message_id} not found.", isWarning=True)
            return None

    def delete_message(self, message_id):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                session.delete(message)
                session.commit()
                self.log(f"Deleted: {message_id}")
                self.event_manager.freedata_message_db_change(message_id=message_id)
                return {'status': 'success', 'message': f'Message {message_id} deleted'}
            else:
                return {'status': 'failure', 'message': 'Message not found'}

        except Exception as e:
            session.rollback()
            self.log(f"Error deleting message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': 'error deleting message'}

        finally:
            session.remove()

    def update_message(self, message_id, update_data, frequency=None):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                # Update fields of the message as per update_data
                if 'body' in update_data:
                    message.body = update_data['body']
                if 'status' in update_data:
                    message.status = self.get_or_create_status(session, update_data['status'])
                if 'statistics' in update_data:
                    statistics = update_data['statistics']
                    if frequency and frequency not in ['---']:
                        statistics["frequency"] = frequency
                    message.statistics = statistics
                if 'is_read' in update_data:
                    message.is_read = update_data['is_read']
                if 'attempt' in update_data:
                    message.attempt = update_data['attempt']
                if 'priority' in update_data:
                    message.priority = update_data['priority']

                session.commit()
                self.log(f"Updated: {message_id}")
                self.event_manager.freedata_message_db_change(message_id=message_id)
                return {'status': 'success', 'message': f'Message {message_id} updated'}
            else:
                return {'status': 'failure', 'message': 'Message not found'}

        except Exception as e:
            session.rollback()
            self.log(f"Error updating message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': 'error updating message'}

        finally:
            session.remove()

    def get_first_queued_message(self):
        session = self.get_thread_scoped_session()
        try:
            # Find the status object for "queued"
            queued_status = session.query(Status).filter_by(name='queued').first()
            if queued_status:
                # Query for the first (oldest) message with status "queued"
                message = session.query(P2PMessage)\
                    .filter_by(status=queued_status)\
                    .order_by(P2PMessage.timestamp)\
                    .first()
                if message:
                    self.log(f"Found queued message with ID {message.id}")
                    return message.to_dict()
                else:
                    return None
            else:
                self.log("Queued status not found", isWarning=True)
                return None
        except Exception as e:
            self.log(f"Error fetching the first queued message: {e}", isWarning=True)
            return None
        finally:
            session.remove()

    def increment_message_attempts(self, message_id, session=None):
        own_session = False
        if not session:
            session = self.get_thread_scoped_session()
            own_session = True
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                message.attempt += 1
                if own_session:
                    session.commit()
                self.log(f"Incremented attempt count for message {message_id}")
            else:
                self.log(f"Message with ID {message_id} not found")
        except Exception as e:
            if own_session:
                session.rollback()
            self.log(f"An error occurred while incrementing attempts for message {message_id}: {e}")
        finally:
            if own_session:
                session.remove()


    def set_message_to_queued_for_callsign(self, callsign):
        session = self.get_thread_scoped_session()
        try:
            # Find the 'failed' status object
            failed_status = session.query(Status).filter_by(name='failed').first()
            # Find the 'queued' status object
            queued_status = session.query(Status).filter_by(name='queued').first()

            # Ensure both statuses are found
            if not failed_status or not queued_status:
                self.log("Failed or queued status not found", isWarning=True)
                return

            # Query for messages with the specified callsign, 'failed' status, and fewer than 10 attempts
            message = session.query(P2PMessage) \
                .filter(P2PMessage.destination_callsign == callsign) \
                .filter(P2PMessage.status_id == failed_status.id) \
                .filter(P2PMessage.attempt < 10) \
                .first()

            if message:
                # Increment attempt count using the existing function
                self.increment_message_attempts(message.id, session)

                message.status_id = queued_status.id
                self.log(f"Set message {message.id} to queued and incremented attempt")

                session.commit()
                return {'status': 'success', 'message': f'message(s) set to queued'}
            else:
                return {'status': 'failure', 'message': 'No eligible messages found'}
        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while setting messages to queued: {e}", isWarning=True)
            return {'status': 'failure', 'message': 'error setting message to queued'}
        finally:
            session.remove()
