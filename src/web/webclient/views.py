
"""
This contains a simple view for rendering the webclient
page and serve it eventual static content.

"""

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from src.server.sessionhandler import SESSIONS

def webclient(request):
    """
    Webclient page template loading.
    """

    # analyze request to find which port we are on
    if int(request.META["SERVER_PORT"]) == 8000:
        # we relay webclient to the portal port
        print "Called from port 8000!"
        #return redirect("http://localhost:8001/webclient/", permanent=True)

    # as an example we send the number of connected players to the template
    pagevars = {'num_players_connected': SESSIONS.player_count()}

    context_instance = RequestContext(request)
    return render_to_response('webclient.html', pagevars, context_instance)
