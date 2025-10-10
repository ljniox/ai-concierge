"""
User service for managing user data in Supabase
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client, create_client
from src.models.user import User, UserCreate, UserUpdate, UserWithStats
from src.utils.config import get_settings
import structlog

logger = structlog.get_logger()


class UserService:
    """Service for managing user operations"""

    def __init__(self):
        self.settings = get_settings()
        self.supabase: Optional[Client] = None
        self._initialize_supabase()

    def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            # Initialize Supabase with minimal parameters to avoid proxy issues
            self.supabase = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key
            )
            logger.info("supabase_client_initialized")
        except Exception as e:
            logger.error("supabase_initialization_failed", error=str(e))
            # Don't raise - allow application to start without Supabase
            self.supabase = None

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user in the database

        Args:
            user_data: User creation data

        Returns:
            Created user object
        """
        try:
            logger.info("creating_user", phone_number=user_data.phone_number)

            # Check if user already exists
            existing_user = await self.get_user_by_phone(user_data.phone_number)
            if existing_user:
                logger.warning("user_already_exists", phone_number=user_data.phone_number)
                return existing_user

            # Create user in database
            user_dict = {
                "phone_number": user_data.phone_number,
                "name": user_data.name,
                "preferred_language": user_data.preferred_language,
                "timezone": user_data.timezone,
                "metadata": user_data.metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_active": True
            }

            response = self.supabase.table("users").insert(user_dict).execute()

            if response.data:
                created_user = User(
                    id=response.data[0]["id"],
                    **user_data.model_dump() if hasattr(user_data, 'model_dump') else user_data.dict(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                logger.info("user_created_successfully", user_id=created_user.id)
                return created_user
            else:
                raise Exception("Failed to create user")

        except Exception as e:
            logger.error("user_creation_failed", phone_number=user_data.phone_number, error=str(e))
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID to retrieve

        Returns:
            User object if found, None otherwise
        """
        try:
            logger.info("getting_user_by_id", user_id=user_id)

            response = self.supabase.table("users").select("*").eq("id", user_id).execute()

            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data["id"],
                    phone_number=user_data["phone_number"],
                    name=user_data["name"],
                    preferred_language=user_data["preferred_language"],
                    timezone=user_data["timezone"],
                    metadata=user_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(user_data["created_at"]),
                    updated_at=datetime.fromisoformat(user_data["updated_at"]),
                    is_active=user_data.get("is_active", True)
                )
            return None

        except Exception as e:
            logger.error("get_user_by_id_failed", user_id=user_id, error=str(e))
            raise

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """
        Get user by phone number

        Args:
            phone_number: Phone number to search for

        Returns:
            User object if found, None otherwise
        """
        try:
            logger.info("getting_user_by_phone", phone_number=phone_number)

            response = self.supabase.table("users").select("*").eq("phone_number", phone_number).execute()

            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data["id"],
                    phone_number=user_data["phone_number"],
                    name=user_data["name"],
                    preferred_language=user_data["preferred_language"],
                    timezone=user_data["timezone"],
                    metadata=user_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(user_data["created_at"]),
                    updated_at=datetime.fromisoformat(user_data["updated_at"]),
                    is_active=user_data.get("is_active", True)
                )
            return None

        except Exception as e:
            logger.error("get_user_by_phone_failed", phone_number=phone_number, error=str(e))
            raise

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """
        Update user information

        Args:
            user_id: User ID to update
            user_data: Update data

        Returns:
            Updated user object
        """
        try:
            logger.info("updating_user", user_id=user_id)

            # Build update dictionary with only provided fields
            update_dict = {}
            for field, value in user_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_dict[field] = value

            if update_dict:
                update_dict["updated_at"] = datetime.now().isoformat()

                response = self.supabase.table("users").update(update_dict).eq("id", user_id).execute()

                if response.data:
                    updated_user = await self.get_user_by_id(user_id)
                    logger.info("user_updated_successfully", user_id=user_id)
                    return updated_user
                else:
                    raise Exception("Failed to update user")
            else:
                # No fields to update
                return await self.get_user_by_id(user_id)

        except Exception as e:
            logger.error("user_update_failed", user_id=user_id, error=str(e))
            raise

    async def get_or_create_user(self, phone_number: str, name: Optional[str] = None) -> User:
        """
        Get existing user or create new one

        Args:
            phone_number: User's phone number
            name: User's name (if creating new user)

        Returns:
            User object
        """
        user = await self.get_user_by_phone(phone_number)
        if user:
            return user
        else:
            user_data = UserCreate(
                phone_number=phone_number,
                name=name
            )
            return await self.create_user(user_data)

    async def get_user_with_stats(self, user_id: str) -> Optional[UserWithStats]:
        """
        Get user with additional statistics

        Args:
            user_id: User ID to retrieve

        Returns:
            User with statistics if found, None otherwise
        """
        try:
            logger.info("getting_user_with_stats", user_id=user_id)

            # Get basic user info
            user = await self.get_user_by_id(user_id)
            if not user:
                return None

            # Get session count
            sessions_response = self.supabase.table("sessions").select("id").eq("user_id", user_id).execute()
            total_sessions = len(sessions_response.data) if sessions_response.data else 0

            # Get interaction count
            interactions_response = self.supabase.table("interactions").select("id").eq("user_id", user_id).execute()
            total_interactions = len(interactions_response.data) if interactions_response.data else 0

            # Get last interaction
            last_interaction = None
            if interactions_response.data:
                last_response = self.supabase.table("interactions").select("created_at").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
                if last_response.data:
                    last_interaction = datetime.fromisoformat(last_response.data[0]["created_at"])

            # Get most used service
            service_stats = {}
            if interactions_response.data:
                service_response = self.supabase.table("interactions").select("service").eq("user_id", user_id).execute()
                if service_response.data:
                    for interaction in service_response.data:
                        service = interaction["service"]
                        service_stats[service] = service_stats.get(service, 0) + 1

            preferred_service = max(service_stats, key=service_stats.get) if service_stats else None

            return UserWithStats(
                **user.model_dump() if hasattr(user, 'model_dump') else user.dict(),
                total_sessions=total_sessions,
                total_interactions=total_interactions,
                last_interaction=last_interaction,
                preferred_service=preferred_service
            )

        except Exception as e:
            logger.error("get_user_with_stats_failed", user_id=user_id, error=str(e))
            raise

    async def deactivate_user(self, user_id: str) -> User:
        """
        Deactivate a user

        Args:
            user_id: User ID to deactivate

        Returns:
            Updated user object
        """
        logger.info("deactivating_user", user_id=user_id)
        update_data = UserUpdate(is_active=False)
        return await self.update_user(user_id, update_data)

    async def activate_user(self, user_id: str) -> User:
        """
        Activate a user

        Args:
            user_id: User ID to activate

        Returns:
            Updated user object
        """
        logger.info("activating_user", user_id=user_id)
        update_data = UserUpdate(is_active=True)
        return await self.update_user(user_id, update_data)

    async def list_users(self, limit: int = 50, offset: int = 0, active_only: bool = True) -> List[User]:
        """
        List users with pagination

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            active_only: Whether to return only active users

        Returns:
            List of user objects
        """
        try:
            logger.info("listing_users", limit=limit, offset=offset, active_only=active_only)

            query = self.supabase.table("users").select("*")

            if active_only:
                query = query.eq("is_active", True)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()

            users = []
            if response.data:
                for user_data in response.data:
                    user = User(
                        id=user_data["id"],
                        phone_number=user_data["phone_number"],
                        name=user_data["name"],
                        preferred_language=user_data["preferred_language"],
                        timezone=user_data["timezone"],
                        metadata=user_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(user_data["created_at"]),
                        updated_at=datetime.fromisoformat(user_data["updated_at"]),
                        is_active=user_data.get("is_active", True)
                    )
                    users.append(user)

            return users

        except Exception as e:
            logger.error("list_users_failed", error=str(e))
            raise