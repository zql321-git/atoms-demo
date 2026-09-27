import json
import logging
from typing import List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.page_versions import Page_versionsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/page_versions", tags=["page_versions"])


# ---------- Pydantic Schemas ----------
class Page_versionsData(BaseModel):
    """Entity data schema (for create/update)"""
    version_no: int
    prompt: str
    html: str


class Page_versionsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    version_no: Optional[int] = None
    prompt: Optional[str] = None
    html: Optional[str] = None


class Page_versionsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    version_no: int
    prompt: str
    html: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Page_versionsListResponse(BaseModel):
    """List response schema"""
    items: List[Page_versionsResponse]
    total: int
    skip: int
    limit: int


class Page_versionsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Page_versionsData]


class Page_versionsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Page_versionsUpdateData


class Page_versionsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Page_versionsBatchUpdateItem]


class Page_versionsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Page_versionsListResponse)
async def query_page_versionss(
    query: str = Query(None, description='Query conditions as JSON, e.g. {"id":2} or {"id":{"$gte":2}}'),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query page_versionss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying page_versionss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Page_versionsService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} page_versionss")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid page_versions query: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error querying page_versionss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Page_versionsListResponse)
async def query_page_versionss_all(
    query: str = Query(None, description='Query conditions as JSON, e.g. {"id":2} or {"id":{"$gte":2}}'),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query page_versionss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying page_versionss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Page_versionsService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} page_versionss")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid page_versions query: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error querying page_versionss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Page_versionsResponse)
async def get_page_versions(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single page_versions by ID (user can only see their own records)"""
    logger.debug(f"Fetching page_versions with id: {id}, fields={fields}")
    
    service = Page_versionsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Page_versions with id {id} not found")
            raise HTTPException(status_code=404, detail="Page_versions not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching page_versions {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Page_versionsResponse, status_code=201)
async def create_page_versions(
    data: Page_versionsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new page_versions"""
    logger.debug(f"Creating new page_versions with data: {data}")
    
    service = Page_versionsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create page_versions")
        
        logger.info(f"Page_versions created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating page_versions: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating page_versions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Page_versionsResponse], status_code=201)
async def create_page_versionss_batch(
    request: Page_versionsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple page_versionss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} page_versionss")
    
    service = Page_versionsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} page_versionss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Page_versionsResponse])
async def update_page_versionss_batch(
    request: Page_versionsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple page_versionss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} page_versionss")
    
    service = Page_versionsService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} page_versionss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Page_versionsResponse)
async def update_page_versions(
    id: int,
    data: Page_versionsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing page_versions (requires ownership)"""
    logger.debug(f"Updating page_versions {id} with data: {data}")

    service = Page_versionsService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Page_versions with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Page_versions not found")
        
        logger.info(f"Page_versions {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating page_versions {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating page_versions {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_page_versionss_batch(
    request: Page_versionsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple page_versionss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} page_versionss")
    
    service = Page_versionsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} page_versionss successfully")
        return {"message": f"Successfully deleted {deleted_count} page_versionss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_page_versions(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single page_versions by ID (requires ownership)"""
    logger.debug(f"Deleting page_versions with id: {id}")
    
    service = Page_versionsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Page_versions with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Page_versions not found")
        
        logger.info(f"Page_versions {id} deleted successfully")
        return {"message": "Page_versions deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting page_versions {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")