import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.runtime_db.compat import connect_postgres
from app.session.store import DEFAULT_SESSION_DB_PATH
from app.settings.schemas import ProviderProfile, UserSettingsEnvelope


class SettingsStorage:
    def __init__(self, *, database_url: str | None = None, sqlite_db_path: Path | str | None = None) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(database_url=self.database_url, sqlite_db_path=self.sqlite_db_path)

    def _connect(self):
        if self.backend_kind == "postgresql":
            return connect_postgres(self.database_url)

        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_user_settings(self, *, owner_user_id: str) -> UserSettingsEnvelope | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT appearance_json, chat_json, data_privacy_json, advanced_json, active_provider_ref
                        FROM user_settings
                        WHERE owner_user_id = %s
                        """,
                        (owner_user_id,),
                    )
                    row = cursor.fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT appearance_json, chat_json, data_privacy_json, advanced_json, active_provider_ref
                    FROM user_settings
                    WHERE owner_user_id = ?
                    """,
                    (owner_user_id,),
                ).fetchone()
        return self._row_to_user_settings(row) if row else None

    def upsert_user_settings(self, *, owner_user_id: str, payload: UserSettingsEnvelope, created_at: str, updated_at: str) -> UserSettingsEnvelope:
        appearance_json = json.dumps(payload.appearance.model_dump(), ensure_ascii=False)
        chat_json = json.dumps(payload.chat.model_dump(), ensure_ascii=False)
        data_privacy_json = json.dumps(payload.data_privacy.model_dump(), ensure_ascii=False)
        advanced_json = json.dumps(payload.advanced.model_dump(), ensure_ascii=False)

        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO user_settings (
                            owner_user_id,
                            appearance_json,
                            chat_json,
                            data_privacy_json,
                            advanced_json,
                            active_provider_ref,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (owner_user_id) DO UPDATE SET
                            appearance_json = EXCLUDED.appearance_json,
                            chat_json = EXCLUDED.chat_json,
                            data_privacy_json = EXCLUDED.data_privacy_json,
                            advanced_json = EXCLUDED.advanced_json,
                            active_provider_ref = EXCLUDED.active_provider_ref,
                            updated_at = EXCLUDED.updated_at
                        """,
                        (
                            owner_user_id,
                            appearance_json,
                            chat_json,
                            data_privacy_json,
                            advanced_json,
                            payload.active_provider_ref,
                            created_at,
                            updated_at,
                        ),
                    )
        else:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO user_settings (
                        owner_user_id,
                        appearance_json,
                        chat_json,
                        data_privacy_json,
                        advanced_json,
                        active_provider_ref,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(owner_user_id) DO UPDATE SET
                        appearance_json = excluded.appearance_json,
                        chat_json = excluded.chat_json,
                        data_privacy_json = excluded.data_privacy_json,
                        advanced_json = excluded.advanced_json,
                        active_provider_ref = excluded.active_provider_ref,
                        updated_at = excluded.updated_at
                    """,
                    (
                        owner_user_id,
                        appearance_json,
                        chat_json,
                        data_privacy_json,
                        advanced_json,
                        payload.active_provider_ref,
                        created_at,
                        updated_at,
                    ),
                )

        return payload

    def list_provider_profiles(self, *, owner_user_id: str) -> list[ProviderProfile]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT profile_id, provider_type, display_name, base_url, model_name, config_json, created_at, updated_at
                        FROM user_provider_profiles
                        WHERE owner_user_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        """,
                        (owner_user_id,),
                    )
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT profile_id, provider_type, display_name, base_url, model_name, config_json, created_at, updated_at
                    FROM user_provider_profiles
                    WHERE owner_user_id = ?
                    ORDER BY updated_at DESC, created_at DESC
                    """,
                    (owner_user_id,),
                ).fetchall()
        return [self._row_to_provider_profile(row) for row in rows]

    def get_provider_profile(self, *, owner_user_id: str, profile_id: str) -> dict | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT profile_id, owner_user_id, provider_type, display_name, base_url, model_name, config_json, api_key_encrypted, created_at, updated_at
                        FROM user_provider_profiles
                        WHERE owner_user_id = %s AND profile_id = %s
                        """,
                        (owner_user_id, profile_id),
                    )
                    row = cursor.fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT profile_id, owner_user_id, provider_type, display_name, base_url, model_name, config_json, api_key_encrypted, created_at, updated_at
                    FROM user_provider_profiles
                    WHERE owner_user_id = ? AND profile_id = ?
                    """,
                    (owner_user_id, profile_id),
                ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["config_json"] = json.loads(payload.get("config_json") or "{}")
        return payload

    def upsert_provider_profile(
        self,
        *,
        owner_user_id: str,
        profile_id: str,
        provider_type: str,
        display_name: str,
        base_url: str | None,
        model_name: str | None,
        config_json: dict,
        api_key_encrypted: str | None,
        created_at: str,
        updated_at: str,
    ) -> ProviderProfile:
        config_payload = json.dumps(config_json, ensure_ascii=False)
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO user_provider_profiles (
                            profile_id,
                            owner_user_id,
                            provider_type,
                            display_name,
                            base_url,
                            model_name,
                            config_json,
                            api_key_encrypted,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (profile_id) DO UPDATE SET
                            display_name = EXCLUDED.display_name,
                            base_url = EXCLUDED.base_url,
                            model_name = EXCLUDED.model_name,
                            config_json = EXCLUDED.config_json,
                            api_key_encrypted = COALESCE(EXCLUDED.api_key_encrypted, user_provider_profiles.api_key_encrypted),
                            updated_at = EXCLUDED.updated_at
                        """,
                        (
                            profile_id,
                            owner_user_id,
                            provider_type,
                            display_name,
                            base_url,
                            model_name,
                            config_payload,
                            api_key_encrypted,
                            created_at,
                            updated_at,
                        ),
                    )
        else:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO user_provider_profiles (
                        profile_id,
                        owner_user_id,
                        provider_type,
                        display_name,
                        base_url,
                        model_name,
                        config_json,
                        api_key_encrypted,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(profile_id) DO UPDATE SET
                        display_name = excluded.display_name,
                        base_url = excluded.base_url,
                        model_name = excluded.model_name,
                        config_json = excluded.config_json,
                        api_key_encrypted = COALESCE(excluded.api_key_encrypted, user_provider_profiles.api_key_encrypted),
                        updated_at = excluded.updated_at
                    """,
                    (
                        profile_id,
                        owner_user_id,
                        provider_type,
                        display_name,
                        base_url,
                        model_name,
                        config_payload,
                        api_key_encrypted,
                        created_at,
                        updated_at,
                    ),
                )

        stored = self.get_provider_profile(owner_user_id=owner_user_id, profile_id=profile_id)
        return self._row_to_provider_profile(stored)

    def delete_provider_profile(self, *, owner_user_id: str, profile_id: str) -> bool:
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM user_provider_profiles WHERE owner_user_id = %s AND profile_id = %s",
                        (owner_user_id, profile_id),
                    )
                    return cursor.rowcount > 0

        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM user_provider_profiles WHERE owner_user_id = ? AND profile_id = ?",
                (owner_user_id, profile_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_user_settings(row) -> UserSettingsEnvelope:
        return UserSettingsEnvelope.model_validate(
            {
                "appearance": json.loads(row["appearance_json"] or "{}"),
                "chat": json.loads(row["chat_json"] or "{}"),
                "data_privacy": json.loads(row["data_privacy_json"] or "{}"),
                "advanced": json.loads(row["advanced_json"] or "{}"),
                "active_provider_ref": row["active_provider_ref"] or "builtin:carbonrag-cloud",
            }
        )

    @staticmethod
    def _row_to_provider_profile(row) -> ProviderProfile:
        payload = dict(row)
        payload["config_json"] = payload.get("config_json") if isinstance(payload.get("config_json"), dict) else json.loads(payload.get("config_json") or "{}")
        return ProviderProfile.model_validate(payload)


@lru_cache(maxsize=1)
def get_settings_storage() -> SettingsStorage:
    return SettingsStorage()
