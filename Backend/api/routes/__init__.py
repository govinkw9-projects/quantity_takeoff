# app/api/routes/__init__.py

from fastapi import APIRouter
from .process_complete_plan import router as get_all_templates_from_pdf
from .segment_legend import router as get_all_symbols_from_legend

router = APIRouter()
router.include_router(get_all_templates_from_pdf, tags=["Get All TemplateMatching From Pdf"]) # , prefix="/"
router.include_router(get_all_symbols_from_legend, tags=["Get All symbols From Legend"]) # , prefix="/"
