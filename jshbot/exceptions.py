import discord
import logging
import sys

#import traceback

from enum import Enum

# Rudimentary enumerated error types
class ErrorTypes(Enum):
    USER, RECOVERABLE, INTERNAL, STARTUP, FATAL = range(5)

class BotException(Exception):

    def __init__(self, error_type, error_subject, error_details, *args, e=None):
        self.error_type = error_type
        self.error_subject = str(error_subject)
        self.error_details = str(error_details)
        self.error_other = args
        other_details = ''
        for detail in args:
            other_details += '{}\n'.format(detail)
        self.error_message = "`{subject} error: {details}`\n{others}".format(
                subject = self.error_subject,
                details = self.error_details,
                others = other_details)
        if e:
            self.error_message += '\nGiven error:\n{0}: {1}'.format(
                    type(e).__name__, e)

        logging.error(self.error_message)

        # If non-recoverable, quit
        if error_type in (ErrorTypes.STARTUP, 
                ErrorTypes.FATAL, 
                ErrorTypes.INTERNAL):
            sys.exit()
            
    def __str__(self):
        return self.error_message
