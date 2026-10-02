from ..schemas.tools import ToolMetadata
import logging

logger = logging.getLogger(__name__)

class ActionGuard:
    @staticmethod
    def validate_action(metadata: ToolMetadata, user_permissions: list[str]) -> bool:
        if metadata.operation == "READ":
            return True
            
        if metadata.operation == "WRITE":
            # Check if user has permission
            if "WRITE_OPERATIONS" not in user_permissions:
                logger.warning(f"User lacks permission for WRITE operation: {metadata.name}")
                return False
                
            return True
        return False
