from fastapi import APIRouter, Depends

from app.api.dependencies import get_service
from app.api.responses import RESP_422
from app.schemas.etablissement import EtablissementOut
from app.services.formation_service import FormationService

router = APIRouter(prefix="/etablissements", tags=["etablissements"])


@router.get("", response_model=list[EtablissementOut], responses={422: RESP_422})
def list_etablissements(service: FormationService = Depends(get_service)):
    return service.list_etablissements()
