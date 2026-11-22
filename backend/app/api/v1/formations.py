from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_service
from app.api.responses import RESP_403, RESP_404, RESP_409, RESP_422
from app.core.security import get_current_role, require_admin
from app.schemas.critere import (
    CritereAdmissionCreate,
    CritereAdmissionOut,
    CritereAdmissionUpdate,
)
from app.schemas.formation import (
    FormationCreate,
    FormationOut,
    FormationUpdate,
    StatutFormation,
)
from app.services.formation_service import FormationService

router = APIRouter(prefix="/formations", tags=["formations"])
criteria_router = APIRouter(tags=["criteres"])


@router.post(
    "",
    response_model=FormationOut,
    status_code=201,
    summary="Créer une formation (admin)",
    dependencies=[Depends(require_admin)],
    responses={403: RESP_403, 404: RESP_404, 409: RESP_409, 422: RESP_422},
)
def create_formation(
    data: FormationCreate, service: FormationService = Depends(get_service)
):
    return service.create(data)


@router.get(
    "",
    response_model=list[FormationOut],
    summary="Lister les formations visibles",
    responses={403: RESP_403, 422: RESP_422},
)
def list_formations(
    etablissement: str | None = Query(default=None, description="Code établissement"),
    type_parcours: str | None = None,
    statut: StatutFormation | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role: str = Depends(get_current_role),
    service: FormationService = Depends(get_service),
):
    return service.list(
        role,
        etablissement_code=etablissement,
        type_parcours=type_parcours,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{formation_id}/criteres",
    response_model=list[CritereAdmissionOut],
    summary="Lister les critères d'admission",
    responses={404: RESP_404, 422: RESP_422},
)
def list_criteres(
    formation_id: int,
    role: str = Depends(get_current_role),
    service: FormationService = Depends(get_service),
):
    return service.list_criteres(formation_id, role)


@router.post(
    "/{formation_id}/criteres",
    response_model=CritereAdmissionOut,
    status_code=201,
    summary="Ajouter un critère d'admission (admin)",
    dependencies=[Depends(require_admin)],
    responses={403: RESP_403, 404: RESP_404, 409: RESP_409, 422: RESP_422},
)
def create_critere(
    formation_id: int,
    data: CritereAdmissionCreate,
    service: FormationService = Depends(get_service),
):
    return service.create_critere(formation_id, data)


@router.get(
    "/{formation_id}",
    response_model=FormationOut,
    summary="Consulter une formation visible",
    responses={404: RESP_404, 422: RESP_422},
)
def get_formation(
    formation_id: int,
    role: str = Depends(get_current_role),
    service: FormationService = Depends(get_service),
):
    return service.get(formation_id, role)


@router.patch(
    "/{formation_id}",
    response_model=FormationOut,
    summary="Modifier une formation (admin)",
    dependencies=[Depends(require_admin)],
    responses={403: RESP_403, 404: RESP_404, 409: RESP_409, 422: RESP_422},
)
def update_formation(
    formation_id: int,
    data: FormationUpdate,
    service: FormationService = Depends(get_service),
):
    return service.update(formation_id, data)


@router.delete(
    "/{formation_id}",
    status_code=204,
    summary="Archiver une formation (admin)",
    dependencies=[Depends(require_admin)],
    responses={403: RESP_403, 404: RESP_404, 409: RESP_409, 422: RESP_422},
)
def delete_formation(formation_id: int, service: FormationService = Depends(get_service)):
    service.archive(formation_id)
    return Response(status_code=204)


@criteria_router.get(
    "/criteres/{critere_id}",
    response_model=CritereAdmissionOut,
    summary="Consulter un critère d'admission visible",
    responses={404: RESP_404, 422: RESP_422},
)
def get_critere(
    critere_id: int,
    role: str = Depends(get_current_role),
    service: FormationService = Depends(get_service),
):
    return service.get_critere(critere_id, role)


@criteria_router.patch(
    "/criteres/{critere_id}",
    response_model=CritereAdmissionOut,
    summary="Modifier un critère d'admission (admin)",
    dependencies=[Depends(require_admin)],
    responses={403: RESP_403, 404: RESP_404, 409: RESP_409, 422: RESP_422},
)
def update_critere(
    critere_id: int,
    data: CritereAdmissionUpdate,
    service: FormationService = Depends(get_service),
):
    return service.update_critere(critere_id, data)


@criteria_router.delete(
    "/criteres/{critere_id}",
    status_code=204,
    summary="Supprimer un critère d'admission (admin)",
    dependencies=[Depends(require_admin)],
    responses={403: RESP_403, 404: RESP_404, 409: RESP_409, 422: RESP_422},
)
def delete_critere(critere_id: int, service: FormationService = Depends(get_service)):
    service.delete_critere(critere_id)
    return Response(status_code=204)
