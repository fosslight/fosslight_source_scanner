import logging
from fosslight_util.get_pom_license import get_license_from_pom
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)


def get_manifest_licenses(file_path: str) -> list[str]:
    if file_path.endswith('.pom'):
        try:
            pom_licenses = get_license_from_pom(group_id='', artifact_id='', version='', pom_path=file_path, check_parent=True)
            if not pom_licenses:
                return []
            return [x.strip() for x in pom_licenses.split(', ') if x.strip()]
        except Exception as ex:
            logger.info(f"Failed to extract license from POM {file_path}: {ex}")
            return []
