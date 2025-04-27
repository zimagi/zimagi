from mcp.server.lowlevel import Server

from .errors import SessionNotFoundError


class MCPSessions(object):

    def __init__(self):
        self.sessions = {}

    def create(self, user, name):
        self.sessions[user.name] = Server(name)
        return self.sessions[user.name]

    def get(self, user):
        if user.name not in self.sessions:
            raise SessionNotFoundError(f"Session not found for user: {user.name}")
        return self.sessions[user.name]
