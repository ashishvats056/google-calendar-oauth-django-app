from django.shortcuts import redirect

from rest_framework.decorators import api_view
from rest_framework.response import Response

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
import json

# Since we are bulding in localhost, to enable use of Oauth2 over http, we are setting this to 1
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CREDENTIALS_FILE = "credentials.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection and REDIRECT URL.
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']
# Add this redirect uri in allowed redirect uri list in the google developer app.
REDIRECT_URL = '/v1/calendar/redirect'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


@api_view(['GET'])
def GoogleCalendarInitView(request):
    # Create google auth flow instance
    google_oauth = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    base_url = '/'.join(request.build_absolute_uri().split('/')[:3])

    google_oauth.redirect_uri = base_url+REDIRECT_URL

    auth_url, state = google_oauth.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    request.session['state'] = state

    return Response({"authorization_url": auth_url})


@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    # Added to request while calling the google oauth flow.
    # verified in the authorization server response below.
    state = request.session['state']

    google_oauth = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CREDENTIALS_FILE, scopes=SCOPES, state=state)
    base_url = '/'.join(request.build_absolute_uri().split('/')[:3])
    google_oauth.redirect_uri = base_url + REDIRECT_URL

    # Fetch access tokens
    auth_response = request.get_full_path()
    google_oauth.fetch_token(authorization_response=auth_response)

    # Store the latest access tokens.
    # Ideally, to be stored in a database.
    credentials = google_oauth.credentials
    request.session['credentials'] = get_credentials_dict(credentials)

    # If credentials are not in session, initialise oauth again.
    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')

    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials'])

    # Create Google api client to connect to Google calendar
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # list calendar names in user's calendar
    calendar_list = service.calendarList().list().execute()

    # Following filter is to identify the email address of the user(main calendar_id) to be used to get the events.
    # It fails if the gmail address follows different pattern.
    # Ideally, a userinfo call should be used to get the calendar_id.
    calendar_id = list(filter(lambda x:x['accessRole']=='owner' and len(x['id'].split("@"))==2 and x['id'].split('@')[1] == 'gmail.com',calendar_list['items']))[0]['id']

    # get the events in the main calendar of the owner.
    events  = service.events().list(calendarId=calendar_id).execute()

    # special handling when no event returned or there are no events in the calendar.
    if not events or 'items' not in events:
        print('No data found.')
        return Response({"message": "No data found or user credentials invalid."})
    else:
        return Response({"events": events['items']})


def get_credentials_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

# get secret key to be used in settings.
def read_secret_key():
    with open(CREDENTIALS_FILE, "r") as f:
        creds = json.load(f)
    return creds["web"]["client_secret"]