# Ce fichier permet l'importation depuis le dossier serializers

from .base import (
    SchoolTypeBaseSerializer,
    CityBaseSerializer,
    SchoolContactBaseSerializer,
    FacilityBaseSerializer,
    DepartmentBaseSerializer,
    ProgramBaseSerializer,
    SchoolReviewBaseSerializer,
    SchoolMediaBaseSerializer,
    SchoolEventBaseSerializer,
    SchoolBaseSerializer
)

from .web import (
    SchoolTypeWebSerializer,
    CityWebSerializer,
    SchoolContactWebSerializer,
    FacilityWebSerializer,
    DepartmentWebSerializer,
    ProgramWebSerializer,
    SchoolReviewWebSerializer,
    SchoolMediaWebSerializer,
    SchoolEventWebSerializer,
    SchoolListWebSerializer,
    SchoolDetailWebSerializer,
    SchoolCreateUpdateWebSerializer
)

from .mobile import (
    SchoolTypeSerializer,
    CitySerializer,
    SchoolContactSerializer,
    FacilitySerializer,
    DepartmentSerializer,
    ProgramSerializer,
    SchoolReviewSerializer,
    SchoolMediaSerializer,
    SchoolEventSerializer,
    SchoolListSerializer,
    SchoolDetailSerializer,
    SchoolCreateUpdateSerializer
)