from __future__ import annotations

__all__: typing.Sequence[str] = "UserCredentialsStrategy"

import asyncio
import base64
import contextlib
import copy
import datetime
import http
import logging
import math
import os
import platform
import sys
import typing
import urllib.parse

import aiohttp
import hikari

from hikari import _about as about
from hikari import applications
from hikari import channels as channels_
from hikari import colors
from hikari import commands
from hikari import embeds as embeds_
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import guilds
from hikari import iterators
from hikari import locales
from hikari import messages as messages_
from hikari import permissions as permissions_
from hikari import scheduled_events
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.api import rest as rest_api
from hikari.impl import buckets as buckets_impl
from hikari.impl import config as config_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl import special_endpoints as special_endpoints_impl
from hikari.interactions import base_interactions
from hikari.internal import aio
from hikari.internal import data_binding
from hikari.internal import mentions
from hikari.internal import net
from hikari.internal import routes
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import audit_logs
    from hikari import invites
    from hikari import sessions
    from hikari import stickers
    from hikari import templates
    from hikari import voices
    from hikari import webhooks
    from hikari.api import cache as cache_api
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import special_endpoints

# new imports
from hikari import RESTApp


class UserCredentialsStrategy(rest_api.TokenStrategy):
    """Strategy class for handling client credential OAuth2 authorization.

    Parameters
    ----------
    client_id : typing.Optional[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]]
        Object or ID of the application this client credentials strategy should
        authorize as.
    client_secret : str
        Client secret to use when authorizing.
    auth_code : str
        Auth code given from Discord when user authorizes
    redirect_uri: str
        The redirect uri that was included in the authorization request

    Other Parameters
    ----------------
    scopes : typing.Sequence[str]
        The scopes to authorize for.
    """

    __slots__: typing.Sequence[str] = (
        "_client_id",
        "_client_secret",
        "_exception",
        "_expire_at",
        "_lock",
        "_scopes",
        "_token",
        "_code",
        "_redirect_uri",
        "_refresh_token",
    )

    def __init__(
        self,
        client_id: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        auth_code: str,
        redirect_uri: str,
        *,
        scopes: typing.Sequence[typing.Union[applications.OAuth2Scope, str]] = (
            applications.OAuth2Scope.APPLICATIONS_COMMANDS_UPDATE,
            applications.OAuth2Scope.IDENTIFY,
        ),
    ) -> None:
        self._client_id = snowflakes.Snowflake(client_id)
        self._client_secret = client_secret
        self._exception: typing.Optional[errors.ClientHTTPResponseError] = None
        self._expire_at = 0.0
        self._lock = asyncio.Lock()
        self._scopes = tuple(scopes)
        self._token: typing.Optional[str] = None
        self._refresh_token = None
        self._code = auth_code
        self._redirect_uri = redirect_uri

    @property
    def client_id(self) -> snowflakes.Snowflake:
        """ID of the application this token strategy authenticates with."""
        return self._client_id

    @property
    def _is_expired(self) -> bool:
        return time.monotonic() >= self._expire_at

    @property
    def scopes(self) -> typing.Sequence[typing.Union[applications.OAuth2Scope, str]]:
        """Sequence of scopes this token strategy authenticates for."""
        return self._scopes

    @property
    def token_type(self) -> applications.TokenType:
        return applications.TokenType.BEARER

    async def acquire(self, client: rest_api.RESTClient | RESTApp) -> str:
        if self._token and not self._is_expired:
            return self._token

        async with self._lock:
            if self._token and not self._is_expired:
                return self._token

            if self._exception:
                # If we don't copy the exception then python keeps adding onto the stack each time it's raised.
                raise copy.copy(self._exception) from None

            try:
                if isinstance(client, RESTApp):
                    client = client.acquire()
                    client.start()

                if not self._token:
                    response = await client.authorize_access_token(
                        client=self._client_id,
                        client_secret=self._client_secret,
                        code=self._code,
                        redirect_uri=self._redirect_uri,
                    )
                else:
                    response = await client.refresh_access_token(
                        client=self._client_id,
                        client_secret=self._client_secret,
                        refresh_token=self._refresh_token,
                    )

            except errors.ClientHTTPResponseError as exc:
                if not isinstance(exc, errors.RateLimitTooLongError):
                    # If we don't copy the exception then python keeps adding onto the stack each time it's raised.
                    self._exception = copy.copy(exc)
                await client.close()
                raise

            # Expires in is lowered a bit in-order to lower the chance of a dead token being used.
            self._expire_at = time.monotonic() + math.floor(
                response.expires_in.total_seconds() * 0.99
            )
            self._token = f"{response.access_token}"
            self._refresh_token = response.refresh_token
            await client.close()
            return self._token

    def invalidate(self, token: typing.Optional[str] = None) -> None:
        if not token or token == self._token:
            self._expire_at = 0.0
            self._token = None
            self._refresh_token = None
