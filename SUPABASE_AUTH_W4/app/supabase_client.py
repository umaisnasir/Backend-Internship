from supabase import Client, create_client
from supabase.client import ClientOptions

from .config import get_settings


def create_supabase_client() -> Client:
    """
    Create a fresh, stateless Supabase client.

    A new client is created for each authentication operation
    so that one user's session cannot leak into another request.
    """

    settings = get_settings()

    return create_client(
        settings.supabase_url,
        settings.supabase_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )