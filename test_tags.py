
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.growth_club import GrowthClubPost, GrowthClubTag, GrowthClubPostTagLink
from app.models.user import User
from app.features.growth_club.application.post_service import GrowthClubPostService
from app.models.user import AuthenticatedUser
from sqlmodel import select

DATABASE_URL = "postgresql+asyncpg://stepzero_admin:stepzero_password@localhost:5432/stepzero_db"

async def test_create_post_with_tags():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get a user
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("No user found")
            return
            
        auth_user = AuthenticatedUser(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_superuser=user.is_superuser
        )
        
        service = GrowthClubPostService(session)
        print(f"Creating post for user {user.id} with tags ['test1', 'test2']")
        post_id = await service.create_post(
            current_user=auth_user,
            title="Test Post with Tags",
            content="This is a test post content",
            category="free",
            prepared_images=[],
            prepared_files=[],
            tags=["test1", "test2"]
        )
        print(f"Post created with ID: {post_id}")
        
        # Verify in DB
        result = await session.execute(
            select(GrowthClubPost).where(GrowthClubPost.id == post_id)
        )
        post = result.scalar_one()
        # Trigger reload of tags (in a real app we'd use selectinload)
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(GrowthClubPost).where(GrowthClubPost.id == post_id).options(selectinload(GrowthClubPost.tags))
        )
        post = result.scalar_one()
        print(f"Tags in DB for post {post_id}: {[t.name for t in post.tags]}")

if __name__ == "__main__":
    asyncio.run(test_create_post_with_tags())
